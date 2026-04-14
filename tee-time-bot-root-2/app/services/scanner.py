"""
Scan Orchestrator
Main loop that coordinates scraping, scoring, deduplication, and action routing.
Runs on a schedule via APScheduler.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta

from app.models.database import get_db
from app.models.courses import COURSES, get_courses_by_platform
from app.scrapers.golfnow_v2 import search_golfnow_facility
from app.scrapers.chronogolf import search_chronogolf
from app.scrapers.foreup import search_foreup
from app.scrapers.direct import search_direct
from app.services.scoring import score_tee_time, determine_action, generate_slot_id
from app.services.notifications import send_alert
from app.services.weather import get_forecast
from app.config import settings

logger = logging.getLogger(__name__)

_surge_mode_until: datetime | None = None
_scan_lock = asyncio.Lock()
ACTION_PRIORITY = {"IGNORE": 0, "ALERT": 1, "CONFIRM": 2, "AUTOBOOK": 3, "BOOKED": 4}
FINAL_ALERT_STATUSES = {"SENT", "SKIPPED", "ROLL_CALL_STARTED", "BOOKED", "AUTOBOOKED"}


def _row_to_dict(row):
    if row is None:
        return None
    try:
        return {key: row[key] for key in row.keys()}
    except Exception:
        try:
            return dict(row)
        except Exception:
            return {}


async def _load_user_context(db, users: list[dict]) -> tuple[dict[str, dict], list[dict]]:
    user_ids = [user["id"] for user in users]
    if not user_ids:
        return {}, []
    placeholders = ",".join("?" for _ in user_ids)
    pref_rows = await db.execute_fetchall(
        f"SELECT * FROM user_preferences WHERE user_id IN ({placeholders})",
        user_ids,
    )
    prefs_by_user = {row["user_id"]: _row_to_dict(row) for row in pref_rows}
    suppression_rows = await db.execute_fetchall(
        f"""
        SELECT * FROM alert_suppressions
        WHERE suppressed_until > datetime('now')
          AND (user_id IS NULL OR user_id IN ({placeholders}))
        """,
        user_ids,
    )
    suppressions = [_row_to_dict(row) for row in suppression_rows]
    return prefs_by_user, suppressions


def _is_suppressed(user_id: str, course_id: str, suppressions: list[dict]) -> bool:
    for suppression in suppressions:
        if suppression.get("user_id") not in (None, user_id):
            continue
        if suppression.get("course_id") not in (None, course_id):
            continue
        return True
    return False


async def run_scan_cycle():
    if _scan_lock.locked():
        logger.info("Scan already in progress, skipping")
        return

    async with _scan_lock:
        started_at = datetime.now()
        logger.info("=== Scan cycle started at %s ===", started_at.isoformat())
        db = await get_db()
        try:
            rows = await db.execute_fetchall("SELECT * FROM users WHERE notification_enabled = 1")
            users = [_row_to_dict(r) for r in rows]
            if not users:
                logger.info("No active users configured. Scanning without alerts.")

            prefs_by_user, suppressions = await _load_user_context(db, users) if users else ({}, [])
            dates_to_search = _get_search_dates()
            all_new_slots: list[dict] = []
            scan_summary = {"courses": 0, "slots_found": 0, "new_slots": 0, "alerts_sent": 0}

            for date in dates_to_search:
                weather = await get_forecast(date)
                if weather and weather.get("is_bad_weather"):
                    logger.info("Skipping %s — bad weather: %s", date, weather.get("summary"))
                    continue

                # Fast scrapers first
                for course in get_courses_by_platform("chronogolf"):
                    try:
                        slots = await search_chronogolf(course["id"], date)
                        new = await _process_slots(db, slots, users, prefs_by_user, suppressions)
                        all_new_slots.extend(new)
                        scan_summary["courses"] += 1
                        scan_summary["slots_found"] += len(slots)
                        scan_summary["new_slots"] += len(new)
                        scan_summary["alerts_sent"] += sum(1 for slot in new if slot.get("alerts_sent", 0))
                        await _log_search(db, course["id"], "chronogolf", "success", len(slots), len(new), started_at)
                    except Exception as exc:
                        logger.error("Error scanning %s via Chronogolf: %s", course["id"], exc)
                        await _log_search(db, course["id"], "chronogolf", "error", 0, 0, started_at, str(exc))
                    await asyncio.sleep(1)
                await db.commit()

                for course in get_courses_by_platform("foreup"):
                    try:
                        slots = await search_foreup(course["id"], date)
                        new = await _process_slots(db, slots, users, prefs_by_user, suppressions)
                        all_new_slots.extend(new)
                        scan_summary["courses"] += 1
                        scan_summary["slots_found"] += len(slots)
                        scan_summary["new_slots"] += len(new)
                        scan_summary["alerts_sent"] += sum(1 for slot in new if slot.get("alerts_sent", 0))
                        await _log_search(db, course["id"], "foreup", "success", len(slots), len(new), started_at)
                    except Exception as exc:
                        logger.error("Error scanning %s via ForeUP: %s", course["id"], exc)
                        await _log_search(db, course["id"], "foreup", "error", 0, 0, started_at, str(exc))
                    await asyncio.sleep(1)
                await db.commit()

                for course in get_courses_by_platform("golfnow"):
                    fid = course.get("golfnow_facility_id")
                    if not fid:
                        continue
                    try:
                        slots = await search_golfnow_facility(fid, course["id"], date)
                        new = await _process_slots(db, slots, users, prefs_by_user, suppressions)
                        all_new_slots.extend(new)
                        scan_summary["courses"] += 1
                        scan_summary["slots_found"] += len(slots)
                        scan_summary["new_slots"] += len(new)
                        scan_summary["alerts_sent"] += sum(1 for slot in new if slot.get("alerts_sent", 0))
                        await _log_search(db, course["id"], "golfnow", "success", len(slots), len(new), started_at)
                    except Exception as exc:
                        logger.error("Error scanning %s: %s", course["id"], exc)
                        await _log_search(db, course["id"], "golfnow", "error", 0, 0, started_at, str(exc))
                    await asyncio.sleep(3)
                await db.commit()

                direct_courses = [
                    cid for cid, c in COURSES.items()
                    if (c.get("platform") == "golfnow" and not c.get("golfnow_facility_id"))
                    or c.get("platform") == "custom"
                ]
                for course_id in direct_courses:
                    try:
                        slots = await search_direct(course_id, date)
                        new = await _process_slots(db, slots, users, prefs_by_user, suppressions)
                        all_new_slots.extend(new)
                        scan_summary["courses"] += 1
                        scan_summary["slots_found"] += len(slots)
                        scan_summary["new_slots"] += len(new)
                        scan_summary["alerts_sent"] += sum(1 for slot in new if slot.get("alerts_sent", 0))
                        await _log_search(db, course_id, "direct", "success", len(slots), len(new), started_at)
                    except Exception as exc:
                        logger.error("Error scanning %s via direct: %s", course_id, exc)
                        await _log_search(db, course_id, "direct", "error", 0, 0, started_at, str(exc))
                    await asyncio.sleep(3)
                await db.commit()

            if all_new_slots:
                global _surge_mode_until
                _surge_mode_until = datetime.now() + timedelta(minutes=30)
                logger.info("Surge mode activated: %d new slots found", len(all_new_slots))

            await db.commit()
            elapsed = (datetime.now() - started_at).total_seconds()
            logger.info(
                "=== Scan complete: %.1fs, new slots=%d, alerts=%d, slots found=%d ===",
                elapsed,
                scan_summary["new_slots"],
                scan_summary["alerts_sent"],
                scan_summary["slots_found"],
            )
        finally:
            await db.close()


async def _process_slots(db, slots: list[dict], users: list[dict], prefs_by_user: dict[str, dict], suppressions: list[dict]) -> list[dict]:
    new_slots: list[dict] = []

    for slot in slots:
        slot_id = generate_slot_id(slot["course_id"], slot["date"], slot["time"])
        slot["id"] = slot_id
        existing_row = await db.execute_fetchone("SELECT * FROM seen_slots WHERE id = ?", (slot_id,))
        existing = _row_to_dict(existing_row) if existing_row else None

        if existing:
            await db.execute(
                "UPDATE seen_slots SET last_seen_at = datetime('now'), disappeared_at = NULL WHERE id = ?",
                (slot_id,),
            )
            if existing.get("disappeared_at"):
                slot["is_new"] = True
            else:
                slot["is_new"] = False
        else:
            slot["is_new"] = True

        course = COURSES.get(slot["course_id"], {})
        highest_score = existing.get("score", 0) if existing else 0
        highest_action = existing.get("action", "PENDING") if existing else "PENDING"
        alerts_sent_for_slot = 0

        await db.execute(
            """INSERT OR IGNORE INTO seen_slots
            (id, course_id, date, time, players_available, price, walk_ride, sub_course,
             score, action, booking_url, source, first_seen_at, last_seen_at, raw_data)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'), ?)
            """,
            (
                slot_id,
                slot["course_id"],
                slot["date"],
                slot["time"],
                slot.get("players_available"),
                slot.get("price"),
                slot.get("walk_ride"),
                slot.get("sub_course"),
                highest_score,
                highest_action if highest_action != "PENDING" else "LOGGED",
                slot.get("booking_url", ""),
                slot.get("source", "scanner"),
                json.dumps(slot),
            ),
        )

        for user in users:
            user_prefs = dict(prefs_by_user.get(user["id"], {}))
            if not user_prefs:
                continue
            if _is_suppressed(user["id"], slot["course_id"], suppressions):
                continue

            overrides_str = user_prefs.get("course_overrides", "{}") or "{}"
            try:
                overrides = json.loads(overrides_str)
            except Exception:
                overrides = {}
            if slot["course_id"] in overrides:
                user_prefs.update(overrides[slot["course_id"]])

            score = score_tee_time(slot, user_prefs, course)
            action = determine_action(score, course, user_prefs)
            if action == "IGNORE":
                continue

            if score > highest_score:
                highest_score = score
            if ACTION_PRIORITY.get(action, 0) > ACTION_PRIORITY.get(highest_action, 0):
                highest_action = action

            existing_alert = await db.execute_fetchone(
                "SELECT * FROM slot_alerts WHERE slot_id = ? AND user_id = ?",
                (slot_id, user["id"]),
            )
            should_send = True
            if existing_alert and not slot["is_new"] and existing_alert["status"] in FINAL_ALERT_STATUSES:
                should_send = False

            if should_send and user.get("telegram_chat_id"):
                response = await send_alert(user["telegram_chat_id"], slot, score, action)
                sent_ok = bool(response and response.get("ok"))
                message_id = None
                if sent_ok:
                    message_id = str(response.get("result", {}).get("message_id", "")) or None
                    alerts_sent_for_slot += 1
                await db.execute(
                    """
                    INSERT INTO slot_alerts
                    (slot_id, user_id, score, recommended_action, status, response, telegram_message_id, sent_at, responded_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, NULL, ?, datetime('now'), NULL, datetime('now'))
                    ON CONFLICT(slot_id, user_id) DO UPDATE SET
                        score = excluded.score,
                        recommended_action = excluded.recommended_action,
                        status = excluded.status,
                        response = NULL,
                        telegram_message_id = COALESCE(excluded.telegram_message_id, telegram_message_id),
                        sent_at = datetime('now'),
                        responded_at = NULL,
                        updated_at = datetime('now')
                    """,
                    (
                        slot_id,
                        user["id"],
                        score,
                        action,
                        "SENT" if sent_ok else "FAILED",
                        message_id,
                    ),
                )
                if sent_ok:
                    await db.execute(
                        "UPDATE seen_slots SET alerted_at = datetime('now') WHERE id = ?",
                        (slot_id,),
                    )

        await db.execute(
            """
            INSERT INTO seen_slots
            (id, course_id, date, time, players_available, price, walk_ride, sub_course,
             score, action, booking_url, source, first_seen_at, last_seen_at, alerted_at, raw_data)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'), NULL, ?)
            ON CONFLICT(id) DO UPDATE SET
                players_available = excluded.players_available,
                price = excluded.price,
                walk_ride = excluded.walk_ride,
                sub_course = excluded.sub_course,
                score = excluded.score,
                action = excluded.action,
                booking_url = excluded.booking_url,
                source = excluded.source,
                last_seen_at = datetime('now'),
                disappeared_at = NULL,
                raw_data = excluded.raw_data
            """,
            (
                slot_id,
                slot["course_id"],
                slot["date"],
                slot["time"],
                slot.get("players_available"),
                slot.get("price"),
                slot.get("walk_ride"),
                slot.get("sub_course"),
                highest_score,
                highest_action if highest_action != "PENDING" else "LOGGED",
                slot.get("booking_url", ""),
                slot.get("source", "scanner"),
                json.dumps(slot),
            ),
        )

        if slot["is_new"] or alerts_sent_for_slot:
            slot["score"] = highest_score
            slot["action"] = highest_action
            slot["alerts_sent"] = alerts_sent_for_slot
            new_slots.append(slot)

    return new_slots


async def _log_search(db, course_id: str, platform: str, status: str,
                      slots_found: int, new_slots: int, scan_start: datetime,
                      error: str | None = None):
    duration_ms = int((datetime.now() - scan_start).total_seconds() * 1000)
    await db.execute(
        """INSERT INTO search_log
        (course_id, platform, status, slots_found, new_slots, duration_ms, error_message)
        VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (course_id, platform, status, slots_found, new_slots, duration_ms, error),
    )


def _get_search_dates() -> list[str]:
    today = datetime.now().date()
    all_dates = [(today + timedelta(days=i)) for i in range(0, 14)]
    weekends = [d.strftime("%Y-%m-%d") for d in all_dates if d.weekday() in (4, 5, 6)]
    weekdays = [d.strftime("%Y-%m-%d") for d in all_dates if d.weekday() not in (4, 5, 6)]
    return weekends + weekdays


def is_surge_mode() -> bool:
    return _surge_mode_until is not None and datetime.now() < _surge_mode_until
