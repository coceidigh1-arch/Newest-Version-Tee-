"""
Snipe Engine
Calculates when tee times release for each course, manages snipe requests,
and runs rapid-fire scans at the exact release moment.

Three entry points:
1. SNIPE command via Telegram ("SNIPE bolingbrook sat 7am")
2. Weekly menu (bot sends options Sunday evening)
3. Set-and-forget preferences (always snipe certain courses)
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from app.models.database import get_db
from app.models.courses import COURSES
from app.scrapers.golfnow_v2 import search_golfnow_facility
from app.services.scoring import generate_slot_id
from app.services.notifications import send_message

logger = logging.getLogger(__name__)

# Snipe scan lock
_snipe_lock = asyncio.Lock()


def get_next_release_events(days_ahead: int = 14) -> list[dict]:
    """
    Calculate upcoming tee time release events.
    Returns a list of {course_id, course_name, play_date, release_date, release_time, advance_days}
    sorted by release_date.
    """
    events = []
    now = datetime.now()

    for i in range(1, days_ahead + 1):
        play_date = now + timedelta(days=i)

        # Only care about Fri/Sat/Sun
        if play_date.weekday() not in (4, 5, 6):
            continue

        day_name = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"][play_date.weekday()]

        for course_id, course in COURSES.items():
            advance = course.get("advance_booking_days", 7)
            release_date = play_date - timedelta(days=advance)

            # Skip if release already happened
            if release_date.date() < now.date():
                continue

            # Release typically happens at midnight
            release_dt = release_date.replace(hour=0, minute=0, second=0)

            events.append({
                "course_id": course_id,
                "course_name": course["name"],
                "play_date": play_date.strftime("%Y-%m-%d"),
                "play_day": day_name,
                "release_date": release_dt.strftime("%Y-%m-%d"),
                "release_time": "12:00 AM",
                "release_dt": release_dt,
                "advance_days": advance,
                "platform": course.get("platform"),
                "risk_tier": course.get("risk_tier"),
                "booking_url": course.get("booking_url", ""),
            })

    events.sort(key=lambda e: e["release_dt"])
    return events


async def create_snipe_request(user_id: str, course_id: str, play_day: str,
                                preferred_time: str, auto_book: bool = False) -> dict:
    """
    Create a snipe request. The bot will rapid-scan at release time.
    play_day: 'sat' or 'sun' or specific date like '2026-04-26'
    preferred_time: '7:00' or '7:00 AM' or 'earliest' or 'any'
    """
    course = COURSES.get(course_id)
    if not course:
        return {"error": f"Unknown course: {course_id}"}

    # Normalize time
    if preferred_time.lower() in ("earliest", "early", "first"):
        preferred_time = "05:00"
    elif preferred_time.lower() in ("any", "all"):
        preferred_time = "any"
    else:
        preferred_time = _normalize_time_input(preferred_time)

    # Calculate the target play date
    if len(play_day) == 10:  # Full date like 2026-04-26
        target_date = play_day
    else:
        target_date = _next_day(play_day)

    # Calculate release date
    advance = course.get("advance_booking_days", 7)
    play_dt = datetime.strptime(target_date, "%Y-%m-%d")
    release_dt = play_dt - timedelta(days=advance)

    # Don't allow auto-book on high-risk courses
    if course.get("risk_tier") == "high":
        auto_book = False

    db = await get_db()
    try:
        await db.execute(
            """INSERT OR REPLACE INTO snipe_requests
            (user_id, course_id, play_date, preferred_time, auto_book,
             release_date, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, 'PENDING', datetime('now'))""",
            (user_id, course_id, target_date, preferred_time,
             int(auto_book), release_dt.strftime("%Y-%m-%d")),
        )
        await db.commit()
    finally:
        await db.close()

    return {
        "course": course["name"],
        "play_date": target_date,
        "preferred_time": preferred_time,
        "release_date": release_dt.strftime("%Y-%m-%d"),
        "release_time": "12:00 AM CT",
        "auto_book": auto_book,
        "advance_days": advance,
    }


async def run_snipe_scan():
    """
    Check if any snipe requests are due (release time is NOW).
    If so, rapid-scan those specific courses.
    """
    if _snipe_lock.locked():
        return

    async with _snipe_lock:
        now = datetime.now()
        today = now.strftime("%Y-%m-%d")

        db = await get_db()
        try:
            # Find snipe requests releasing today that haven't been fulfilled
            rows = await db.execute_fetchall(
                """SELECT sr.*, u.telegram_chat_id, u.name as user_name
                FROM snipe_requests sr
                JOIN users u ON sr.user_id = u.id
                WHERE sr.release_date = ? AND sr.status = 'PENDING'""",
                (today,),
            )

            if not rows:
                return

            snipes = [_row_to_dict(r) for r in rows]
            logger.info("Snipe scan: %d active snipes for today", len(snipes))

            # Group by course
            by_course = {}
            for snipe in snipes:
                cid = snipe["course_id"]
                if cid not in by_course:
                    by_course[cid] = []
                by_course[cid].append(snipe)

            # Scan each course
            for course_id, course_snipes in by_course.items():
                course = COURSES.get(course_id, {})
                play_date = course_snipes[0]["play_date"]
                fid = course.get("golfnow_facility_id")
                platform = course.get("platform", "")

                # Try to actually scrape for slots regardless of platform
                slots = []
                if fid:
                    slots = await search_golfnow_facility(fid, course_id, play_date)
                elif platform == "chronogolf":
                    from app.scrapers.chronogolf import search_chronogolf
                    slots = await search_chronogolf(course_id, play_date)
                elif platform == "foreup":
                    from app.scrapers.foreup import search_foreup
                    slots = await search_foreup(course_id, play_date)
                else:
                    from app.scrapers.direct import search_direct
                    slots = await search_direct(course_id, play_date)

                # Store ALL found slots in seen_slots so dashboard can see them
                for slot in slots:
                    slot_id = generate_slot_id(slot["course_id"], slot["date"], slot["time"])
                    await db.execute(
                        """INSERT OR REPLACE INTO seen_slots
                        (id, course_id, date, time, players_available, price,
                         walk_ride, score, action, booking_url, source,
                         first_seen_at, last_seen_at, alerted_at, raw_data)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'), datetime('now'), ?)""",
                        (
                            slot_id, slot["course_id"], slot["date"], slot["time"],
                            slot.get("players_available"), slot.get("price"),
                            slot.get("walk_ride"), 80,  # snipe-found slots get high score
                            "ALERT", slot.get("booking_url", ""),
                            slot.get("source", "snipe"), "{}",
                        ),
                    )

                if not slots:
                    # No slots found yet — send deep link as fallback
                    for snipe in course_snipes:
                        if snipe.get("telegram_chat_id"):
                            await send_message(
                                snipe["telegram_chat_id"],
                                f"⛳ [SNIPE] {course['name']} tee times for {play_date} "
                                f"should be live now!\n\n"
                                f"🔗 Book here: {course.get('booking_url', '')}"
                            )
                    continue

                logger.info("Snipe: %s on %s — %d slots found!", course_id, play_date, len(slots))

                # Match slots to snipe requests
                for snipe in course_snipes:
                    pref_time = snipe.get("preferred_time", "any")
                    best_slot = _find_best_slot(slots, pref_time)

                    if best_slot:
                        chat_id = snipe.get("telegram_chat_id")
                        if chat_id:
                            price_str = f"${best_slot.get('price', '?')}" if best_slot.get('price') else "Price TBD"
                            booking_url = best_slot.get("booking_url", course.get("booking_url", ""))

                            await send_message(
                                chat_id,
                                f"[SNIPE] {course['name']}\n"
                                f"{play_date} at {best_slot['time']}\n"
                                f"{price_str}/player\n\n"
                                f"Book NOW: {booking_url}"
                            )

                        await db.execute(
                            """UPDATE snipe_requests SET status = 'FOUND',
                            found_time = ?, found_price = ?
                            WHERE user_id = ? AND course_id = ? AND play_date = ?""",
                            (best_slot["time"], best_slot.get("price"),
                             snipe["user_id"], course_id, play_date),
                        )

                await asyncio.sleep(2)

            await db.commit()

        finally:
            await db.close()


async def send_weekly_snipe_menu():
    """
    Send the weekly snipe menu to all users (Sunday evening).
    Shows which courses have tee times opening this week.
    """
    events = get_next_release_events(days_ahead=14)
    if not events:
        return

    db = await get_db()
    try:
        rows = await db.execute_fetchall(
            "SELECT * FROM users WHERE notification_enabled = 1 AND telegram_chat_id IS NOT NULL"
        )
        users = [_row_to_dict(r) for r in rows]

        if not users:
            return

        # Group events by release date
        by_date = {}
        for e in events:
            rd = e["release_date"]
            if rd not in by_date:
                by_date[rd] = []
            by_date[rd].append(e)

        # Build message
        msg = "<b>This week's tee time releases:</b>\n\n"
        for release_date in sorted(by_date.keys())[:7]:
            events_on_date = by_date[release_date]
            rd_dt = datetime.strptime(release_date, "%Y-%m-%d")
            day_name = rd_dt.strftime("%A %b %d")
            msg += f"<b>{day_name}:</b>\n"

            for e in events_on_date:
                play_dt = datetime.strptime(e["play_date"], "%Y-%m-%d")
                play_day = play_dt.strftime("%A %b %d")
                msg += f"  {e['course_name']} ({play_day})\n"

            msg += "\n"

        msg += "Reply <b>SNIPE [course] [day] [time]</b> to set up auto-alerts.\n"
        msg += "Example: SNIPE bolingbrook sat 7am"

        for user in users:
            await send_message(user["telegram_chat_id"], msg)

    finally:
        await db.close()


async def send_release_headsup():
    """
    Send heads-up alerts the evening before a release.
    "Bolingbrook Saturday times open tonight at midnight"
    """
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

    events = get_next_release_events(days_ahead=14)
    tomorrow_events = [e for e in events if e["release_date"] == tomorrow]

    if not tomorrow_events:
        return

    db = await get_db()
    try:
        rows = await db.execute_fetchall(
            "SELECT * FROM users WHERE notification_enabled = 1 AND telegram_chat_id IS NOT NULL"
        )
        users = [_row_to_dict(r) for r in rows]

        for user in users:
            msg = "<b>Tee times opening tomorrow:</b>\n\n"
            for e in tomorrow_events:
                play_dt = datetime.strptime(e["play_date"], "%Y-%m-%d")
                play_day = play_dt.strftime("%A %b %d")
                msg += (
                    f"{e['course_name']}\n"
                    f"  For: {play_day}\n"
                    f"  Opens: midnight tonight\n"
                    f"  Window: {e['advance_days']} days advance\n\n"
                )

            msg += "Reply <b>SNIPE [course] sat [time]</b> to auto-alert.\n"
            msg += "Example: SNIPE bolingbrook sat 7am"

            await send_message(user["telegram_chat_id"], msg)

    finally:
        await db.close()


def _find_best_slot(slots: list[dict], preferred_time: str) -> dict | None:
    """Find the best matching slot for a preferred time."""
    if not slots:
        return None

    if preferred_time == "any":
        # Return earliest morning slot
        morning = [s for s in slots if s.get("time", "99:99") < "09:00"]
        return morning[0] if morning else slots[0]

    # Try to find exact match first
    for s in slots:
        if s.get("time") == preferred_time:
            return s

    # Find closest match
    try:
        pref_minutes = int(preferred_time.split(":")[0]) * 60 + int(preferred_time.split(":")[1])
        best = None
        best_diff = 9999

        for s in slots:
            slot_time = s.get("time", "")
            if ":" not in slot_time:
                continue
            parts = slot_time.split(":")
            slot_minutes = int(parts[0]) * 60 + int(parts[1])
            diff = abs(slot_minutes - pref_minutes)
            if diff < best_diff:
                best_diff = diff
                best = s

        return best
    except (ValueError, IndexError):
        return slots[0] if slots else None


def _normalize_time_input(raw: str) -> str:
    """Convert user time input to HH:MM format."""
    raw = raw.strip().upper().replace(".", ":")

    # Handle "7am", "7:30am", "730am"
    raw = raw.replace("AM", " AM").replace("PM", " PM").strip()

    for fmt in ("%I:%M %p", "%I:%M%p", "%I %p", "%I%p", "%H:%M"):
        try:
            t = datetime.strptime(raw, fmt)
            return t.strftime("%H:%M")
        except ValueError:
            continue

    # Handle bare numbers like "7" or "730"
    try:
        num = int(raw.replace(":", ""))
        if num < 24:
            return f"{num:02d}:00"
        else:
            return f"{num // 100:02d}:{num % 100:02d}"
    except ValueError:
        return "07:00"  # Default to 7 AM


def _next_day(day_abbrev: str) -> str:
    """Get the date of the next occurrence of a day."""
    day_map = {
        "mon": 0, "tue": 1, "wed": 2, "thu": 3,
        "fri": 4, "sat": 5, "sun": 6,
        "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
        "friday": 4, "saturday": 5, "sunday": 6,
    }
    target = day_map.get(day_abbrev.lower(), 5)  # Default Saturday
    now = datetime.now()
    days_ahead = (target - now.weekday()) % 7
    if days_ahead == 0:
        days_ahead = 7
    return (now + timedelta(days=days_ahead)).strftime("%Y-%m-%d")


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
