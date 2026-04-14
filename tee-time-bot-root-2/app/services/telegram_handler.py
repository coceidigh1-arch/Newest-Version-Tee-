"""
Telegram Webhook Handler
Processes incoming messages and callback buttons from Telegram.
"""

import logging
import uuid
from datetime import datetime, timedelta

from fastapi import Request, HTTPException
from app.api.routes import app
from app.models.database import get_db
from app.models.courses import COURSES
from app.services.notifications import (
    send_message,
    send_roll_call,
    answer_callback_query,
    edit_message_reply_markup,
)
from app.config import settings

logger = logging.getLogger(__name__)


def _normalize_action(action: str) -> str:
    return "CONFIRM" if action == "CONFIRMED" else "ALERT" if action == "ALERTED" else action


async def _assert_webhook_secret(request: Request) -> None:
    if not settings.TELEGRAM_WEBHOOK_SECRET:
        return
    provided = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
    if provided != settings.TELEGRAM_WEBHOOK_SECRET:
        raise HTTPException(status_code=401, detail="Invalid webhook secret")


async def _lookup_user_by_chat(db, chat_id: str):
    return await db.execute_fetchone("SELECT * FROM users WHERE telegram_chat_id = ?", (chat_id,))


async def _get_latest_user_alert(db, user_id: str, slot_id: str | None = None):
    params: list[str] = [user_id]
    query = """
        SELECT sa.*, ss.course_id, ss.date, ss.time, ss.price, ss.players_available, ss.booking_url
        FROM slot_alerts sa
        JOIN seen_slots ss ON ss.id = sa.slot_id
        WHERE sa.user_id = ?
          AND sa.sent_at > datetime('now', ?)
    """
    params.append(f"-{settings.ALERT_LOOKBACK_MINUTES} minutes")
    if slot_id:
        query += " AND sa.slot_id = ?"
        params.append(slot_id)
    query += " ORDER BY sa.sent_at DESC LIMIT 1"
    return await db.execute_fetchone(query, params)


async def _find_latest_roll_call(db):
    return await db.execute_fetchone(
        "SELECT * FROM roll_calls WHERE status = 'PENDING' ORDER BY created_at DESC LIMIT 1"
    )


@app.post("/telegram/webhook")
async def telegram_webhook(request: Request):
    await _assert_webhook_secret(request)
    try:
        data = await request.json()
    except Exception:
        return {"ok": True}

    db = await get_db()
    try:
        callback = data.get("callback_query")
        if callback:
            await _handle_callback(db, callback)
            return {"ok": True}

        message = data.get("message", {})
        text = (message.get("text") or "").strip().upper()
        chat_id = str(message.get("chat", {}).get("id", ""))
        user_name = message.get("from", {}).get("first_name", "Unknown")
        if not text or not chat_id:
            return {"ok": True}

        user = await _lookup_user_by_chat(db, chat_id)
        if not user:
            await send_message(
                chat_id,
                f"Hi {user_name}! I don't recognize your account yet.\n\n"
                "Ask your group admin to add you via the API:\n"
                f"<code>POST /users</code> with your Telegram chat ID: <code>{chat_id}</code>",
            )
            return {"ok": True}

        if text == "BOOK":
            await _handle_book(db, user, chat_id)
        elif text == "SKIP":
            await _handle_skip(db, user, chat_id)
        elif text.startswith("PAUSE"):
            await _handle_pause(db, user, chat_id, text)
        elif text.startswith("SNIPE"):
            await _handle_snipe(db, user, chat_id, text)
        elif text == "RELEASES":
            await _handle_releases(chat_id)
        elif text == "MYSNIPES":
            await _handle_my_snipes(db, user, chat_id)
        elif text == "IN":
            await _handle_roll_call_response(db, user, chat_id, "IN")
        elif text == "OUT":
            await _handle_roll_call_response(db, user, chat_id, "OUT")
        elif text == "STATUS":
            await _handle_status(db, user, chat_id)
        elif text == "STOP":
            await _handle_stop(db, user, chat_id)
        elif text == "RESUME":
            await _handle_resume(db, user, chat_id)
        elif text == "HELP":
            await _handle_help(chat_id)
        elif text.startswith("/START"):
            await _handle_start(chat_id, user_name)
        else:
            await send_message(chat_id, "Commands: BOOK, SKIP, PAUSE, IN, OUT, STATUS, STOP, RESUME, HELP")
    finally:
        await db.close()

    return {"ok": True}


async def _handle_callback(db, callback: dict) -> None:
    data = callback.get("data") or ""
    callback_id = callback.get("id", "")
    message = callback.get("message", {})
    chat_id = str(message.get("chat", {}).get("id", ""))
    message_id = str(message.get("message_id", ""))
    if not chat_id or not data:
        if callback_id:
            await answer_callback_query(callback_id, "Nothing to do.")
        return

    user = await _lookup_user_by_chat(db, chat_id)
    if not user:
        if callback_id:
            await answer_callback_query(callback_id, "Connect your Telegram first.", show_alert=True)
        return

    action, _, value = data.partition(":")
    if action == "book":
        await _handle_book(db, user, chat_id, slot_id=value, callback_id=callback_id, message_id=message_id)
    elif action == "skip":
        await _handle_skip(db, user, chat_id, slot_id=value, callback_id=callback_id, message_id=message_id)
    elif action == "pause":
        await _handle_pause(db, user, chat_id, f"PAUSE {value}", callback_id=callback_id, message_id=message_id)
    elif action == "rcin":
        await _handle_roll_call_response(db, user, chat_id, "IN", roll_call_id=value, callback_id=callback_id)
    elif action == "rcout":
        await _handle_roll_call_response(db, user, chat_id, "OUT", roll_call_id=value, callback_id=callback_id)
    else:
        if callback_id:
            await answer_callback_query(callback_id, "Unknown action.", show_alert=True)


async def _start_roll_call_for_alert(db, user, chat_id: str, alert_row, callback_id: str | None = None, message_id: str | None = None):
    if not alert_row:
        if callback_id:
            await answer_callback_query(callback_id, "No recent alert found.", show_alert=True)
        else:
            await send_message(chat_id, "No recent tee time alert to book. Alerts expire after 30 minutes.")
        return

    slot_id = alert_row["slot_id"]
    slot = await db.execute_fetchone("SELECT * FROM seen_slots WHERE id = ?", (slot_id,))
    if not slot:
        if callback_id:
            await answer_callback_query(callback_id, "That tee time is no longer available.", show_alert=True)
        else:
            await send_message(chat_id, "That tee time is no longer available.")
        return

    course = COURSES.get(slot["course_id"], {})
    if course.get("risk_tier") == "high":
        msg = (
            f"⚠️ <b>{course['name']}</b> is a prepaid / no-refund course.\n\n"
            f"Book manually to be safe:\n🔗 <a href=\"{slot['booking_url']}\">Book here</a>\n\n"
            f"{course.get('cancel_details', '')}"
        )
        await send_message(chat_id, msg)
        await db.execute(
            "UPDATE slot_alerts SET status = 'MANUAL_ONLY', response = 'BOOK', responded_at = datetime('now'), updated_at = datetime('now') WHERE id = ?",
            (alert_row["id"],),
        )
        await db.commit()
        if callback_id:
            await answer_callback_query(callback_id, "Manual booking only for this course.", show_alert=True)
        return

    existing_roll_call = await db.execute_fetchone(
        "SELECT * FROM roll_calls WHERE slot_id = ? AND status IN ('PENDING', 'READY') ORDER BY created_at DESC LIMIT 1",
        (slot_id,),
    )
    if existing_roll_call:
        await db.execute(
            "INSERT OR REPLACE INTO roll_call_responses (roll_call_id, user_id, response, responded_at) VALUES (?, ?, 'IN', datetime('now'))",
            (existing_roll_call["id"], user["id"]),
        )
        await db.execute(
            "UPDATE slot_alerts SET status = 'ROLL_CALL_STARTED', response = 'BOOK', responded_at = datetime('now'), updated_at = datetime('now') WHERE id = ?",
            (alert_row["id"],),
        )
        await db.commit()
        if callback_id:
            await answer_callback_query(callback_id, "Joined existing roll call.")
            if message_id:
                await edit_message_reply_markup(chat_id, message_id)
        await send_message(chat_id, "✅ You joined the existing roll call.")
        return

    roll_call_id = str(uuid.uuid4())[:8]
    expires_at = (datetime.now() + timedelta(minutes=15)).isoformat()

    await db.execute(
        "INSERT INTO roll_calls (id, slot_id, initiated_by, min_players, expires_at) VALUES (?, ?, ?, ?, ?)",
        (roll_call_id, slot_id, user["id"], 3, expires_at),
    )
    await db.execute(
        "INSERT OR REPLACE INTO roll_call_responses (roll_call_id, user_id, response, responded_at) VALUES (?, ?, 'IN', datetime('now'))",
        (roll_call_id, user["id"]),
    )
    await db.execute(
        "UPDATE slot_alerts SET status = 'ROLL_CALL_STARTED', response = 'BOOK', responded_at = datetime('now'), updated_at = datetime('now') WHERE id = ?",
        (alert_row["id"],),
    )
    await db.commit()

    all_users = await db.execute_fetchall(
        "SELECT * FROM users WHERE notification_enabled = 1 AND telegram_chat_id IS NOT NULL AND id != ?",
        (user["id"],),
    )
    chat_ids = [u["telegram_chat_id"] for u in all_users]
    await send_roll_call(chat_ids, dict(slot), roll_call_id, user["name"], 3)

    if callback_id:
        await answer_callback_query(callback_id, "Roll call started.")
        if message_id:
            await edit_message_reply_markup(chat_id, message_id)
    await send_message(
        chat_id,
        "✅ Roll call started! You're in.\nWaiting for 2 more players to confirm.\nRoll call expires in 15 minutes.",
    )


async def _handle_book(db, user, chat_id, slot_id: str | None = None, callback_id: str | None = None, message_id: str | None = None):
    alert_row = await _get_latest_user_alert(db, user["id"], slot_id)
    await _start_roll_call_for_alert(db, user, chat_id, alert_row, callback_id=callback_id, message_id=message_id)


async def _handle_skip(db, user, chat_id, slot_id: str | None = None, callback_id: str | None = None, message_id: str | None = None):
    alert_row = await _get_latest_user_alert(db, user["id"], slot_id)
    if not alert_row:
        if callback_id:
            await answer_callback_query(callback_id, "No matching alert found.", show_alert=True)
        else:
            await send_message(chat_id, "No recent alert to skip.")
        return

    await db.execute(
        "UPDATE slot_alerts SET status = 'SKIPPED', response = 'SKIP', responded_at = datetime('now'), updated_at = datetime('now') WHERE id = ?",
        (alert_row["id"],),
    )
    await db.commit()
    if callback_id:
        await answer_callback_query(callback_id, "Skipped.")
        if message_id:
            await edit_message_reply_markup(chat_id, message_id)
    await send_message(chat_id, "⏭️ Skipped. I'll keep watching for other slots.")


async def _handle_pause(db, user, chat_id, text, callback_id: str | None = None, message_id: str | None = None):
    hours = 12
    course_id = None
    parts = text.split()
    if len(parts) > 1:
        course_input = " ".join(parts[1:]).lower()
        course_id = _match_course(course_input)
        if not course_id:
            for cid, course in COURSES.items():
                if course_input in course["name"].lower():
                    course_id = cid
                    break

    suppressed_until = (datetime.now() + timedelta(hours=hours)).isoformat()
    await db.execute(
        "INSERT INTO alert_suppressions (user_id, course_id, suppressed_until, reason) VALUES (?, ?, ?, ?)",
        (user["id"], course_id, suppressed_until, "User paused via Telegram"),
    )
    await db.commit()

    course_name = COURSES.get(course_id, {}).get("name", "all courses") if course_id else "all courses"
    if callback_id:
        await answer_callback_query(callback_id, f"Paused {course_name} alerts.")
        if message_id:
            await edit_message_reply_markup(chat_id, message_id)
    await send_message(chat_id, f"⏸️ Alerts paused for {course_name} for {hours} hours.")


async def _handle_roll_call_response(
    db,
    user,
    chat_id,
    response,
    roll_call_id: str | None = None,
    callback_id: str | None = None,
):
    rc = None
    if roll_call_id:
        rc = await db.execute_fetchone("SELECT * FROM roll_calls WHERE id = ?", (roll_call_id,))
    if not rc:
        rc = await _find_latest_roll_call(db)

    if not rc:
        if callback_id:
            await answer_callback_query(callback_id, "No active roll call.", show_alert=True)
        else:
            await send_message(chat_id, "No active roll call right now.")
        return

    await db.execute(
        "INSERT OR REPLACE INTO roll_call_responses (roll_call_id, user_id, response, responded_at) VALUES (?, ?, ?, datetime('now'))",
        (rc["id"], user["id"], response),
    )
    in_count = await db.execute_fetchone(
        "SELECT COUNT(*) as cnt FROM roll_call_responses WHERE roll_call_id = ? AND response = 'IN'",
        (rc["id"],),
    )
    count = in_count["cnt"] if in_count else 0
    await db.commit()

    if callback_id:
        await answer_callback_query(callback_id, f"Recorded: {response}")

    if response == "IN":
        await send_message(chat_id, f"✅ You're in! {count}/{rc['min_players']} players confirmed.")
        if count >= rc["min_players"]:
            slot = await db.execute_fetchone("SELECT * FROM seen_slots WHERE id = ?", (rc["slot_id"],))
            course = COURSES.get(slot["course_id"], {}) if slot else {}
            await db.execute(
                "UPDATE roll_calls SET status = 'READY', completed_at = datetime('now') WHERE id = ?",
                (rc["id"],),
            )
            await db.commit()
            confirmed = await db.execute_fetchall(
                """
                SELECT u.telegram_chat_id, u.name FROM roll_call_responses rcr
                JOIN users u ON rcr.user_id = u.id
                WHERE rcr.roll_call_id = ? AND rcr.response = 'IN'
                """,
                (rc["id"],),
            )
            player_list = ", ".join(r["name"] for r in confirmed)
            booking_url = slot["booking_url"] if slot else ""
            for confirmed_user in confirmed:
                await send_message(
                    confirmed_user["telegram_chat_id"],
                    f"🏌️ <b>Group is ready!</b>\n\n"
                    f"Players: {player_list}\n"
                    f"Course: {course.get('name', '?')}\n"
                    f"Date: {slot['date'] if slot else '?'} at {slot['time'] if slot else '?'}\n\n"
                    f"🔗 <a href=\"{booking_url}\">Book now</a>",
                )
    else:
        await send_message(chat_id, f"👋 No worries. {count}/{rc['min_players']} confirmed so far.")


async def _handle_status(db, user, chat_id):
    scans = await db.execute_fetchone(
        "SELECT COUNT(*) as cnt FROM search_log WHERE timestamp > datetime('now', '-1 hour')"
    )
    alerts = await db.execute_fetchone(
        "SELECT COUNT(*) as cnt FROM slot_alerts WHERE sent_at > datetime('now', '-24 hours')"
    )
    rollcalls = await db.execute_fetchone(
        "SELECT COUNT(*) as cnt FROM roll_calls WHERE status = 'PENDING'"
    )
    bookings = await db.execute_fetchone(
        "SELECT COUNT(*) as cnt FROM bookings WHERE status = 'CONFIRMED' AND date >= date('now')"
    )

    from app.services.scanner import is_surge_mode
    surge = "🔥 Active" if is_surge_mode() else "Normal"

    await send_message(
        chat_id,
        f"📊 <b>Bot status</b>\n\n"
        f"Scans (last hour): {scans['cnt'] if scans else 0}\n"
        f"Alerts (24hr): {alerts['cnt'] if alerts else 0}\n"
        f"Active roll calls: {rollcalls['cnt'] if rollcalls else 0}\n"
        f"Upcoming bookings: {bookings['cnt'] if bookings else 0}\n"
        f"Scan mode: {surge}",
    )


async def _handle_stop(db, user, chat_id):
    await db.execute("UPDATE users SET notification_enabled = 0 WHERE id = ?", (user["id"],))
    await db.commit()
    await send_message(chat_id, "🛑 All notifications disabled. Reply RESUME to re-enable.")


async def _handle_resume(db, user, chat_id):
    await db.execute("UPDATE users SET notification_enabled = 1 WHERE id = ?", (user["id"],))
    await db.execute("DELETE FROM alert_suppressions WHERE user_id = ?", (user["id"],))
    await db.commit()
    await send_message(chat_id, "✅ Notifications re-enabled. I'm watching for tee times.")


async def _handle_help(chat_id):
    await send_message(
        chat_id,
        "<b>Tee Time Bot Commands</b>\n\n"
        "<b>SNIPE [course] [day] [time]</b>\n"
        "  Auto-alert the second times drop\n"
        "  Ex: SNIPE bolingbrook sat 7am\n"
        "  Ex: SNIPE schaumburg sun earliest\n\n"
        "<b>RELEASES</b> — See when times open this week\n"
        "<b>MYSNIPES</b> — See your active snipe requests\n\n"
        "<b>BOOK</b> — Start a roll call for last alert\n"
        "<b>SKIP</b> — Dismiss the last alert\n"
        "<b>PAUSE</b> — Pause alerts for 12 hours\n"
        "<b>IN / OUT</b> — Respond to roll call\n"
        "<b>STATUS</b> — Check bot status\n"
        "<b>STOP / RESUME</b> — Toggle notifications\n"
        "<b>HELP</b> — Show this message",
    )


async def _handle_start(chat_id, user_name):
    await send_message(
        chat_id,
        f"Welcome to Tee Time Bot, {user_name}!\n\n"
        f"Your Telegram chat ID is: <code>{chat_id}</code>\n\n"
        "Send this to your group admin so they can add you to the system.\n\n"
        "Once added, I'll send you tee time alerts for Chicago's best courses. Reply HELP anytime to see available commands.",
    )


async def _handle_snipe(db, user, chat_id, text):
    from app.services.snipe import create_snipe_request

    parts = text.split()
    if len(parts) < 3:
        await send_message(
            chat_id,
            "<b>SNIPE usage:</b>\n\n"
            "SNIPE [course] [day] [time]\n\n"
            "Examples:\n"
            "  SNIPE bolingbrook sat 7am\n"
            "  SNIPE schaumburg sun earliest\n"
            "  SNIPE harborside sat any",
        )
        return

    course_input = parts[1].lower()
    course_id = _match_course(course_input)
    if not course_id:
        await send_message(chat_id, f"Course '{parts[1]}' not recognized.")
        return

    day = parts[2].lower() if len(parts) > 2 else "sat"
    time_pref = parts[3] if len(parts) > 3 else "earliest"
    result = await create_snipe_request(
        user_id=user["id"],
        course_id=course_id,
        play_day=day,
        preferred_time=time_pref,
        auto_book=False,
    )
    if "error" in result:
        await send_message(chat_id, f"Error: {result['error']}")
        return

    course = COURSES.get(course_id, {})
    await send_message(
        chat_id,
        f"<b>Snipe set!</b>\n\n"
        f"Course: {course.get('name', course_id)}\n"
        f"Play date: {result['play_date']}\n"
        f"Preferred time: {result['preferred_time']}\n"
        f"Times release: {result['release_date']} at midnight\n"
        f"Advance window: {result['advance_days']} days\n\n"
        f"I'll alert you the second those times go live.",
    )


async def _handle_releases(chat_id):
    from app.services.snipe import get_next_release_events
    events = get_next_release_events(days_ahead=14)
    if not events:
        await send_message(chat_id, "No upcoming releases in the next 14 days.")
        return

    by_date = {}
    for event in events:
        by_date.setdefault(event["release_date"], []).append(event)

    msg = "<b>Upcoming tee time releases:</b>\n\n"
    for release_date in sorted(by_date.keys())[:10]:
        items = by_date[release_date]
        rd_dt = datetime.strptime(release_date, "%Y-%m-%d")
        msg += f"<b>{rd_dt.strftime('%a %b %d')}:</b>\n"
        for event in items[:6]:
            play_dt = datetime.strptime(event["play_date"], "%Y-%m-%d")
            msg += f"  {event['course_name'][:20]} -> {play_dt.strftime('%a %b %d')}\n"
        msg += "\n"
    msg += "Reply SNIPE [course] [day] [time] to set alerts."
    await send_message(chat_id, msg)


async def _handle_my_snipes(db, user, chat_id):
    rows = await db.execute_fetchall(
        "SELECT * FROM snipe_requests WHERE user_id = ? AND status = 'PENDING' ORDER BY play_date",
        (user["id"],),
    )
    if not rows:
        await send_message(chat_id, "No active snipes. Use SNIPE [course] [day] [time] to set one up.")
        return

    msg = "<b>Your active snipes:</b>\n\n"
    for row in rows:
        course = COURSES.get(row["course_id"], {})
        msg += (
            f"{course.get('name', row['course_id'])}\n"
            f"  Play: {row['play_date']}\n"
            f"  Time: {row['preferred_time']}\n"
            f"  Opens: {row['release_date']} at midnight\n\n"
        )
    await send_message(chat_id, msg)


def _match_course(input_text: str) -> str | None:
    aliases = {
        "bolingbrook": "bolingbrook", "bbrook": "bolingbrook", "bb": "bolingbrook",
        "harborside": "harborside", "harbor": "harborside", "hbr": "harborside",
        "stonewall": "stonewall", "stone": "stonewall",
        "thunderhawk": "thunderhawk", "thunder": "thunderhawk",
        "schaumburg": "schaumburg", "schaum": "schaumburg",
        "preserve": "preserve_oak", "oakmeadows": "preserve_oak", "oak": "preserve_oak",
        "glen": "glen_club", "glenclub": "glen_club",
        "highlands": "highlands_elgin",
        "bowes": "bowes_creek", "bowescreek": "bowes_creek",
        "cantigny": "cantigny",
        "coghill": "cog_hill_123", "cog": "cog_hill_123", "dubsdread": "cog_hill_4",
        "mistwood": "mistwood",
        "prairie": "prairie_landing", "prairielanding": "prairie_landing",
        "sanctuary": "sanctuary",
        "arboretum": "arboretum", "arb": "arboretum",
        "balmoral": "balmoral_woods", "balmoralwoods": "balmoral_woods",
        "bartlett": "bartlett_hills", "bartletthills": "bartlett_hills",
        "bridges": "bridges_poplar", "poplar": "bridges_poplar", "poplarcreek": "bridges_poplar",
        "brokenarrow": "broken_arrow", "broken": "broken_arrow",
        "chevychase": "chevy_chase", "chevy": "chevy_chase",
        "coyote": "coyote_run", "coyoterun": "coyote_run",
        "deerfield": "deerfield", "deer": "deerfield",
        "foxrun": "fox_run",
        "foxford": "foxford_hills", "foxfordhills": "foxford_hills",
        "dunne": "george_dunne", "georgedunne": "george_dunne",
        "greengarden": "green_garden",
        "hilldale": "hilldale",
        "carillon": "links_carillon", "linkscarillon": "links_carillon",
        "lostmarsh": "lost_marsh", "marsh": "lost_marsh",
        "makray": "makray", "makraymemorial": "makray",
        "pinemeadow": "pine_meadow", "pine": "pine_meadow",
        "prairiebluff": "prairie_bluff", "bluff": "prairie_bluff",
        "ruffled": "ruffled_feathers", "ruffledfeathers": "ruffled_feathers",
        "standrews": "st_andrews",
        "sevenbridges": "seven_bridges", "7bridges": "seven_bridges",
        "sunset": "sunset_valley", "sunsetvalley": "sunset_valley",
        "watersedge": "waters_edge", "waters": "waters_edge",
    }
    if input_text in aliases:
        return aliases[input_text]
    if input_text in COURSES:
        return input_text
    for alias, course_id in aliases.items():
        if input_text in alias or alias in input_text:
            return course_id
    return None
