"""
ForeUP Scraper — Direct API with correct parameters
Covers: Cog Hill 1-2-3, Cog Hill 4 Dubsdread, Sanctuary GC, Sunset Valley GC

API params discovered via Chrome DevTools network inspection:
- Date format: MM-DD-YYYY (NOT YYYY-MM-DD)
- Requires booking_class + schedule_id
- api_key can be empty
"""

import asyncio
import httpx
import logging
from datetime import datetime
from app.models.courses import COURSES

logger = logging.getLogger(__name__)

FOREUP_API = "https://foreupsoftware.com/index.php/api/booking/times"

# Discovered via Chrome network inspection on each course's booking page
FOREUP_CONFIGS = {
    "cog_hill_123": {
        "booking_class": "43",
        "schedule_ids": ["10960", "10961", "10962", "10963"],
    },
    "cog_hill_4": {
        "booking_class": "42",
        "schedule_ids": ["10964"],
    },
    "sunset_valley": {
        "booking_class": "6510",
        "schedule_ids": ["6510"],
    },
    "sanctuary": {
        "booking_class": "6838",
        "schedule_ids": ["6838"],
    },
}


def _format_date(date_str: str) -> str:
    """Convert YYYY-MM-DD to MM-DD-YYYY for ForeUP API."""
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    return dt.strftime("%m-%d-%Y")


async def search_foreup(course_id: str, date: str, players: int = 4) -> list[dict]:
    """Search ForeUP API for tee times at a specific course."""
    config = FOREUP_CONFIGS.get(course_id)
    if not config:
        logger.debug("ForeUP: no config for %s, skipping", course_id)
        return []

    api_date = _format_date(date)
    all_slots = []
    course = COURSES.get(course_id, {})
    seen_times = set()

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            for schedule_id in config["schedule_ids"]:
                try:
                    response = await client.get(
                        FOREUP_API,
                        params={
                            "time": "all",
                            "date": api_date,
                            "holes": "all",
                            "players": "0",
                            "booking_class": config["booking_class"],
                            "schedule_id": schedule_id,
                            "specials_only": "0",
                            "api_key": "",
                        },
                        headers={
                            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                            "Accept": "application/json",
                            "X-Requested-With": "XMLHttpRequest",
                        },
                    )

                    if response.status_code != 200:
                        logger.warning("ForeUP API %s/%s returned %d", course_id, schedule_id, response.status_code)
                        continue

                    data = response.json()
                    items = data if isinstance(data, list) else data.get("times", [])

                    for item in items:
                        if not isinstance(item, dict):
                            continue
                        time_raw = str(item.get("time", ""))
                        normalized = _normalize_time(time_raw)
                        if not normalized or normalized in seen_times:
                            continue

                        price = float(item.get("green_fee", 0) or item.get("price", 0) or 0)
                        avail = int(item.get("available_spots", 4) or item.get("spots", 4) or 4)

                        if avail > 0:
                            seen_times.add(normalized)
                            all_slots.append({
                                "course_id": course_id,
                                "date": date,
                                "time": normalized,
                                "price": price,
                                "players_available": avail,
                                "walk_ride": "ride" if course.get("walk_ride") == "ride_included" else "unknown",
                                "booking_url": course.get("booking_url", ""),
                                "source": "foreup_api",
                                "is_new": True,
                            })

                except Exception as e:
                    logger.warning("ForeUP API error for %s schedule %s: %s", course_id, schedule_id, e)

                await asyncio.sleep(1)

        logger.info("ForeUP: %s on %s -> %d slots", course_id, date, len(all_slots))

    except Exception as e:
        logger.error("ForeUP error for %s: %s", course_id, str(e))

    return all_slots


def _normalize_time(raw: str) -> str | None:
    if not raw:
        return None
    raw = raw.strip().upper()
    for fmt in ("%I:%M %p", "%I:%M%p", "%H:%M", "%H:%M:%S"):
        try:
            return datetime.strptime(raw, fmt).strftime("%H:%M")
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00")).strftime("%H:%M")
    except (ValueError, TypeError):
        return None
