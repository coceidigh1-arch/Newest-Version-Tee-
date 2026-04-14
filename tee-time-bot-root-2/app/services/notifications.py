"""
Telegram Notification Service
Sends tee time alerts, roll calls, booking confirmations, and handles replies.
"""

import asyncio
import logging
import httpx
from app.config import settings
from app.models.courses import COURSES

logger = logging.getLogger(__name__)


def _clean_text(text: str) -> str:
    try:
        return text.encode("utf-16", "surrogatepass").decode("utf-16")
    except Exception:
        return text.encode("utf-8", "replace").decode("utf-8")


def _get_api_url() -> str:
    token = settings.TELEGRAM_BOT_TOKEN.strip()
    return f"https://api.telegram.org/bot{token}"


async def _telegram_request(method: str, payload: dict) -> dict | None:
    if not settings.TELEGRAM_BOT_TOKEN or settings.TELEGRAM_BOT_TOKEN.strip() == "placeholder":
        logger.warning("Telegram bot token not configured")
        return None

    api_url = _get_api_url()
    attempts = 3
    for attempt in range(1, attempts + 1):
        try:
            async with httpx.AsyncClient(timeout=settings.TELEGRAM_TIMEOUT_SEC) as client:
                response = await client.post(f"{api_url}/{method}", json=payload)
            if response.status_code == 200:
                return response.json()
            logger.error("Telegram %s failed (%s): %s", method, response.status_code, response.text)
        except Exception as exc:
            logger.error("Telegram %s error on attempt %s: %s", method, attempt, exc)
        if attempt < attempts:
            await asyncio.sleep(0.5 * attempt)
    return None


async def send_message(
    chat_id: str,
    text: str,
    parse_mode: str = "HTML",
    reply_markup: dict | None = None,
) -> bool:
    payload = {
        "chat_id": chat_id,
        "text": _clean_text(text),
        "parse_mode": parse_mode,
        "disable_web_page_preview": True,
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup
    response = await _telegram_request("sendMessage", payload)
    return bool(response and response.get("ok"))


async def answer_callback_query(callback_query_id: str, text: str = "", show_alert: bool = False) -> bool:
    payload = {
        "callback_query_id": callback_query_id,
        "text": _clean_text(text),
        "show_alert": show_alert,
    }
    response = await _telegram_request("answerCallbackQuery", payload)
    return bool(response and response.get("ok"))


async def edit_message_reply_markup(chat_id: str, message_id: str | int, reply_markup: dict | None = None) -> bool:
    payload = {
        "chat_id": chat_id,
        "message_id": int(message_id),
        "reply_markup": reply_markup or {"inline_keyboard": []},
    }
    response = await _telegram_request("editMessageReplyMarkup", payload)
    return bool(response and response.get("ok"))


async def send_message_with_result(
    chat_id: str,
    text: str,
    parse_mode: str = "HTML",
    reply_markup: dict | None = None,
) -> dict | None:
    payload = {
        "chat_id": chat_id,
        "text": _clean_text(text),
        "parse_mode": parse_mode,
        "disable_web_page_preview": True,
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup
    return await _telegram_request("sendMessage", payload)


def build_alert_reply_markup(slot: dict) -> dict:
    slot_id = slot["id"]
    course_id = slot["course_id"]
    return {
        "inline_keyboard": [
            [
                {"text": "✅ BOOK", "callback_data": f"book:{slot_id}"},
                {"text": "⏭️ SKIP", "callback_data": f"skip:{slot_id}"},
            ],
            [
                {"text": "⏸️ PAUSE COURSE", "callback_data": f"pause:{course_id}"},
            ],
        ]
    }


def build_roll_call_reply_markup(roll_call_id: str) -> dict:
    return {
        "inline_keyboard": [
            [
                {"text": "✅ IN", "callback_data": f"rcin:{roll_call_id}"},
                {"text": "❌ OUT", "callback_data": f"rcout:{roll_call_id}"},
            ]
        ]
    }


def format_alert_message(slot: dict, score: int, action: str) -> str:
    course = COURSES.get(slot["course_id"], {})
    course_name = course.get("name", slot["course_id"])
    risk = course.get("risk_tier", "unknown")

    risk_emoji = {"low": "✅", "medium": "⚠️", "high": "🚨"}.get(risk, "❓")
    action_emoji = {
        "ALERT": "⛳",
        "CONFIRM": "🎯",
        "AUTOBOOK": "🚀",
    }.get(action, "⛳")

    price_str = f"${slot.get('price', '?')}/player" if slot.get("price") else "Price TBD"
    ride_info = course.get("walk_ride", "unknown")
    if ride_info == "ride_included":
        ride_str = "Ride (included)"
    elif ride_info == "walk_only":
        ride_str = "Walk only"
    else:
        ride_str = "Walk/Ride available"

    range_str = "\n🎯 Range: Included with round" if course.get("range_included") else ""
    cancel_str = course.get("cancel_details", "Check course policy")[:80]
    booking_url = slot.get("booking_url", course.get("booking_url", ""))

    msg = f"""{action_emoji} <b>TEE TIME {'ALERT' if action == 'ALERT' else 'FOUND'}</b>

📍 <b>{course_name}</b>
📅 {slot['date']}
⏰ {slot['time']}
👥 {slot.get('players_available', '?')} players available
💰 {price_str}
🏃 {ride_str}{range_str}
📊 Score: <b>{score}/100</b>
{risk_emoji} Risk: {risk}
📋 Cancel: {cancel_str}

🔗 <a href="{booking_url}">Book here</a>"""

    if action in {"ALERT", "CONFIRM", "AUTOBOOK"}:
        msg += "\n\nUse the buttons below to respond."
    return msg


def format_roll_call_message(slot: dict, roll_call_id: str, initiator: str, players_needed: int) -> str:
    course = COURSES.get(slot["course_id"], {})
    course_name = course.get("name", slot["course_id"])
    price_str = f"${slot.get('price', '?')}/player" if slot.get("price") else "Price TBD"

    return f"""🏆 <b>ROLL CALL</b>

📍 <b>{course_name}</b>
📅 {slot['date']} at {slot['time']}
💰 {price_str}
👥 Need {players_needed} players

Started by: {initiator}

Tap a button below to respond.
Roll call expires in 15 minutes.
ID: <code>{roll_call_id}</code>"""


def format_booking_confirmation(booking: dict) -> str:
    course = COURSES.get(booking.get("course_id", ""), {})
    course_name = course.get("name", booking.get("course_id", ""))

    return f"""✅ <b>BOOKING CONFIRMED</b>

📍 <b>{course_name}</b>
📅 {booking['date']} at {booking['time']}
👥 {booking['players']} players
💰 ${booking.get('total_price', '?')} total (${booking.get('per_player_price', '?')}/player)
🎫 Confirmation: <code>{booking.get('confirmation_code', 'pending')}</code>
📌 Booked on: {booking.get('platform', 'unknown')}

⚠️ Cancel policy: {course.get('cancel_details', 'Check course website')[:100]}"""


def format_daily_digest(stats: dict) -> str:
    return f"""📊 <b>Daily Digest</b>

🔍 Scans today: {stats.get('scans', 0)}
⛳ Slots found: {stats.get('slots_found', 0)}
📨 Alerts sent: {stats.get('alerts_sent', 0)}
✅ Bookings: {stats.get('bookings', 0)}
💰 Spent this month: ${stats.get('monthly_spend', 0):.0f}
🎯 Rounds this week: {stats.get('weekly_rounds', 0)}

Bot is running normally. ✅"""


async def send_alert(chat_id: str, slot: dict, score: int, action: str) -> dict | None:
    msg = format_alert_message(slot, score, action)
    return await send_message_with_result(chat_id, msg, reply_markup=build_alert_reply_markup(slot))


async def send_roll_call(chat_ids: list[str], slot: dict, roll_call_id: str, initiator: str, players_needed: int) -> list[bool]:
    msg = format_roll_call_message(slot, roll_call_id, initiator, players_needed)
    results = []
    reply_markup = build_roll_call_reply_markup(roll_call_id)
    for chat_id in chat_ids:
        result = await send_message(chat_id, msg, reply_markup=reply_markup)
        results.append(result)
    return results


async def send_booking_confirmation(chat_ids: list[str], booking: dict) -> list[bool]:
    msg = format_booking_confirmation(booking)
    results = []
    for chat_id in chat_ids:
        result = await send_message(chat_id, msg)
        results.append(result)
    return results
