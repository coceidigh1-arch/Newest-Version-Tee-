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
from app.models.courses import COURSES
from app.services.scoring import score_tee_time, determine_action, generate_slot_id
from app.services.notifications import send_alert
from app.services.weather import get_forecast
from app.services.scrape_dispatch import dispatch_scan, ScanStatus
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
            # We USED to bail out when there were no users — but the scanner
            # also populates seen_slots, which the dashboard reads regardless
            # of whether anyone is subscribed for alerts. _process_slots
            # already no-ops its per-user alert loop when `users` is empty;
            # slots still get inserted, which is what we want for the UI.
            if not users:
                logger.info("No active users — running in dashboard-only mode (no alerts will be sent).")

            prefs_by_user, suppressions = await _load_user_context(db, users)
            dates_to_search = _get_search_dates()
            all_new_slots: list[dict] = []
            scan_summary = {
                "courses": 0, "slots_found": 0, "new_slots": 0, "alerts_sent": 0,
                "ok": 0, "empty": 0, "unsupported": 0, "error": 0, "config_missing": 0, "skipped": 0,
            }

            # Per-platform polite delay between consecutive scans. golfnow is
            # aggressive about rate limiting; the others are less touchy.
            PLATFORM_DELAYS = {"golfnow": 3.0, "chronogolf": 2.0, "foreup": 1.5, "direct": 2.0}

            for date in dates_to_search:
                weather = await get_forecast(date)
                skip_reason = None
                if weather and weather.get("is_bad_weather"):
                    skip_reason = f"bad weather: {weather.get('summary')}"
                    logger.info("Skipping %s — %s", date, skip_reason)

                for course_id, course in COURSES.items():
                    platform = course.get("platform", "unknown")

                    if skip_reason:
                        await _log_search(
                            db, course_id, platform, ScanStatus.SKIPPED,
                            0, 0, started_at, skip_reason, search_date=date,
                        )
                        scan_summary["skipped"] += 1
                        continue

                    slots, status, err = await dispatch_scan(course_id, date)
                    scan_summary["courses"] += 1
                    scan_summary[status] = scan_summary.get(status, 0) + 1

                    new: list[dict] = []
                    if slots:
                        try:
                            new = await _process_slots(db, slots, users, prefs_by_user, suppressions)
                        except Exception as exc:
                            logger.exception("_process_slots failed for %s/%s", course_id, date)
                            status = ScanStatus.ERROR
                            err = f"_process_slots: {exc}"
                        all_new_slots.extend(new)
                        scan_summary["slots_found"] += len(slots)
                        scan_summary["new_slots"] += len(new)
                        scan_summary["alerts_sent"] += sum(1 for slot in new if slot.get("alerts_sent", 0))

                    await _log_search(
                        db, course_id, platform, status,
                        len(slots), len(new), started_at, err, search_date=date,
                    )

                    # Rate-limit polite pause, but only for platforms that
                    # actually hit the network. UNSUPPORTED/CONFIG_MISSING are
                    # instant; no need to throttle them.
                    if status in (ScanStatus.OK, ScanStatus.EMPTY, ScanStatus.ERROR):
                        await asyncio.sleep(PLATFORM_DELAYS.get(platform, 1.0))

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
                      error: str | None = None, search_date: str | None = None):
    """Record a single scan attempt. `search_date` is the date the scanner was
    querying for (distinct from the row's `timestamp`, which is when the scan
    ran). This lets the /api/course/{id}/week endpoint join against the most
    recent scan for each specific day."""
    duration_ms = int((datetime.now() - scan_start).total_seconds() * 1000)
    await db.execute(
        """INSERT INTO search_log
        (course_id, platform, status, slots_found, new_slots, duration_ms, error_message, search_date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (course_id, platform, status, slots_found, new_slots, duration_ms, error, search_date),
    )


def _get_search_dates() -> list[str]:
    today = datetime.now().date()
    return [(today + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(0, 14)]


def is_surge_mode() -> bool:
    return _surge_mode_until is not None and datetime.now() < _surge_mode_until
