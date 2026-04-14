"""
GolfNow Scraper
Searches for tee times on GolfNow by facility ID.
Covers: Bolingbrook, Cantigny, Harborside, Stonewall, Thunderhawk,
        Schaumburg, Prairie Landing, Sanctuary, and more.
"""

import httpx
import logging
import re
import json
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from app.models.courses import get_courses_by_platform, COURSES

logger = logging.getLogger(__name__)

GOLFNOW_BASE = "https://www.golfnow.com"
GOLFNOW_SEARCH = f"{GOLFNOW_BASE}/tee-times/facility"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
}


async def search_golfnow_facility(
    facility_id: str,
    course_id: str,
    date: str,
    players: int = 4,
) -> list[dict]:
    """
    Search a specific GolfNow facility for available tee times.
    Returns normalized slot dicts.
    """
    url = f"{GOLFNOW_SEARCH}/{facility_id}/search"
    params = {
        "date": date,
        "players": players,
    }

    slots = []

    try:
        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            response = await client.get(url, params=params, headers=HEADERS)

            if response.status_code != 200:
                logger.warning(
                    "GolfNow returned %d for %s on %s",
                    response.status_code, course_id, date,
                )
                return []

            html = response.text

            # GolfNow embeds tee time data in JSON within script tags
            # and also renders it in structured HTML elements
            slots = _parse_golfnow_html(html, course_id, date)

            # Also try to extract from embedded JSON/API responses
            json_slots = _parse_golfnow_json(html, course_id, date)
            if json_slots:
                slots.extend(json_slots)

            # Deduplicate by time
            seen_times = set()
            unique_slots = []
            for s in slots:
                key = f"{s['time']}_{s.get('price', 0)}"
                if key not in seen_times:
                    seen_times.add(key)
                    unique_slots.append(s)
            slots = unique_slots

    except httpx.TimeoutException:
        logger.error("GolfNow timeout for %s on %s", course_id, date)
    except Exception as e:
        logger.error("GolfNow error for %s: %s", course_id, str(e))

    return slots


def _parse_golfnow_html(html: str, course_id: str, date: str) -> list[dict]:
    """Parse tee time cards from GolfNow HTML response."""
    slots = []
    soup = BeautifulSoup(html, "html.parser")

    # GolfNow uses various class patterns for tee time results
    # Look for time/price/player elements
    time_elements = soup.select(
        "[data-time], .time-meridian, .tee-time-card, "
        ".rate-row, [class*='teetime'], [class*='tee-time']"
    )

    for elem in time_elements:
        slot = _extract_slot_from_element(elem, course_id, date)
        if slot:
            slots.append(slot)

    return slots


def _parse_golfnow_json(html: str, course_id: str, date: str) -> list[dict]:
    """Extract tee time data from embedded JSON in script tags."""
    slots = []

    # Look for JSON data embedded in script tags
    json_pattern = re.compile(
        r'(?:window\.__NEXT_DATA__|window\.__data__|teeTimes|teeTimeResults)\s*=\s*({.*?});',
        re.DOTALL,
    )
    matches = json_pattern.findall(html)

    for match in matches:
        try:
            data = json.loads(match)
            extracted = _walk_json_for_slots(data, course_id, date)
            slots.extend(extracted)
        except json.JSONDecodeError:
            continue

    return slots


def _walk_json_for_slots(data, course_id: str, date: str, depth: int = 0) -> list[dict]:
    """Recursively walk JSON structure looking for tee time data."""
    slots = []
    if depth > 10:
        return slots

    if isinstance(data, dict):
        # Check if this dict looks like a tee time
        has_time = any(k in data for k in ("time", "teeTime", "startTime", "teetime"))
        has_price = any(k in data for k in ("price", "rate", "greenFee", "totalPrice"))

        if has_time and has_price:
            slot = _normalize_json_slot(data, course_id, date)
            if slot:
                slots.append(slot)

        for v in data.values():
            slots.extend(_walk_json_for_slots(v, course_id, date, depth + 1))

    elif isinstance(data, list):
        for item in data:
            slots.extend(_walk_json_for_slots(item, course_id, date, depth + 1))

    return slots


def _extract_slot_from_element(elem, course_id: str, date: str) -> dict | None:
    """Extract slot info from an HTML element."""
    text = elem.get_text(" ", strip=True)

    # Try to find time pattern (e.g., "7:30 AM", "08:00")
    time_match = re.search(r'(\d{1,2}:\d{2}\s*(?:AM|PM|am|pm)?)', text)
    if not time_match:
        return None

    raw_time = time_match.group(1).strip()
    normalized_time = _normalize_time(raw_time)
    if not normalized_time:
        return None

    # Try to find price
    price_match = re.search(r'\$(\d+(?:\.\d{2})?)', text)
    price = float(price_match.group(1)) if price_match else 0

    # Try to find player count
    player_match = re.search(r'(\d)\s*(?:player|golfer|spot)', text, re.IGNORECASE)
    players = int(player_match.group(1)) if player_match else 4

    # Look for booking URL
    link = elem.find("a", href=True)
    booking_url = link["href"] if link else None
    if booking_url and not booking_url.startswith("http"):
        booking_url = f"{GOLFNOW_BASE}{booking_url}"

    course = COURSES.get(course_id, {})

    return {
        "course_id": course_id,
        "date": date,
        "time": normalized_time,
        "price": price,
        "players_available": players,
        "walk_ride": "ride" if course.get("walk_ride") == "ride_included" else "unknown",
        "booking_url": booking_url or course.get("booking_url", ""),
        "source": "golfnow",
        "is_new": True,
        "raw_text": text[:200],
    }


def _normalize_json_slot(data: dict, course_id: str, date: str) -> dict | None:
    """Normalize a JSON tee time object to our standard format."""
    time_raw = (
        data.get("time") or data.get("teeTime") or
        data.get("startTime") or data.get("teetime") or ""
    )
    if not time_raw:
        return None

    normalized_time = _normalize_time(str(time_raw))
    if not normalized_time:
        return None

    price = float(
        data.get("price") or data.get("rate") or
        data.get("greenFee") or data.get("totalPrice") or 0
    )

    players = int(
        data.get("players") or data.get("maxPlayers") or
        data.get("spotsAvailable") or 4
    )

    course = COURSES.get(course_id, {})

    return {
        "course_id": course_id,
        "date": date,
        "time": normalized_time,
        "price": price,
        "players_available": players,
        "walk_ride": "ride" if course.get("walk_ride") == "ride_included" else "unknown",
        "booking_url": data.get("bookingUrl", course.get("booking_url", "")),
        "source": "golfnow",
        "is_new": True,
    }


def _normalize_time(raw: str) -> str | None:
    """Convert various time formats to HH:MM 24hr."""
    raw = raw.strip().upper()

    for fmt in ("%I:%M %p", "%I:%M%p", "%H:%M", "%H:%M:%S"):
        try:
            t = datetime.strptime(raw, fmt)
            return t.strftime("%H:%M")
        except ValueError:
            continue

    # Try ISO datetime
    try:
        t = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        return t.strftime("%H:%M")
    except (ValueError, TypeError):
        pass

    return None


async def search_all_golfnow_courses(date: str, players: int = 4) -> list[dict]:
    """Search all GolfNow-listed courses for a given date."""
    all_slots = []
    courses = get_courses_by_platform("golfnow")

    for course in courses:
        fid = course.get("golfnow_facility_id")
        if not fid:
            continue

        slots = await search_golfnow_facility(fid, course["id"], date, players)
        all_slots.extend(slots)

        logger.info(
            "GolfNow: %s on %s → %d slots",
            course["name"], date, len(slots),
        )

        # Be polite — 3-8 second delay between courses
        import asyncio
        import random
        await asyncio.sleep(random.uniform(3, 8))

    # Also search Harborside Starboard (separate facility ID)
    harborside = COURSES.get("harborside", {})
    starboard_id = harborside.get("golfnow_starboard_id")
    if starboard_id:
        slots = await search_golfnow_facility(starboard_id, "harborside", date, players)
        for s in slots:
            s["sub_course"] = "Starboard"
        all_slots.extend(slots)

    return all_slots
