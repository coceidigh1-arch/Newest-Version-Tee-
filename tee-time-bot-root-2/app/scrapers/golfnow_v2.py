"""
GolfNow Scraper v3.1 — Direct POST API (TIMEZONE FIX DEPLOYED)
Uses GolfNow's internal JSON API. No Playwright needed.
Returns ALL tee times with prices, hot deals, cart info, and booking URLs.
"""

SCRAPER_VERSION = "3.1-tz-fix"

import httpx
import logging
import asyncio
import random
from datetime import datetime, timedelta
from app.models.courses import COURSES, get_courses_by_platform

logger = logging.getLogger(__name__)

GOLFNOW_API = "https://www.golfnow.com/api/tee-times/tee-time-results"

HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Origin": "https://www.golfnow.com",
    "Referer": "https://www.golfnow.com/tee-times/",
}

# Month name map for API date format
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def _format_api_date(date_str: str) -> str:
    """Convert YYYY-MM-DD to 'Apr 19 2026' format for GolfNow API."""
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    return f"{MONTHS[dt.month - 1]} {dt.day} {dt.year}"


async def search_golfnow_facility(
    facility_id: str,
    course_id: str,
    date: str,
    players: int = 4,
) -> list[dict]:
    """Search GolfNow API for tee times at a specific facility."""
    slots = []
    course = COURSES.get(course_id, {})

    payload = {
        "Radius": 50,
        "PageSize": 50,
        "PageNumber": 0,
        "SearchType": 1,
        "SortBy": "Date",
        "SortDirection": 0,
        "Date": _format_api_date(date),
        "BestDealsOnly": False,
        "PriceMin": "0",
        "PriceMax": "10000",
        "Players": str(players),
        "Holes": "3",
        "FacilityId": int(facility_id),
        "SortByRollup": "Date.MinDate",
        "View": "Grouping",
        "TeeTimeCount": 50,
        "ExcludeFeaturedFacilities": True,
    }

    try:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(
                GOLFNOW_API,
                json=payload,
                headers=HEADERS,
            )

            if response.status_code != 200:
                logger.error("GolfNow API %s: HTTP %d", course_id, response.status_code)
                return []

            data = response.json()
            tee_times = data.get("ttResults", {}).get("teeTimes", [])

            for tt in tee_times:
                time_obj = tt.get("time", {})
                if not isinstance(time_obj, dict):
                    continue

                time_iso = time_obj.get("date", "")
                time_formatted = time_obj.get("formatted", "")
                time_meridian = time_obj.get("formattedTimeMeridian", "")

                # Parse time to HH:MM 24h format
                normalized_time = _normalize_time(time_iso, time_formatted, time_meridian)
                if not normalized_time:
                    continue

                # Extract price
                display_rate = tt.get("displayRate", {})
                price = display_rate.get("value", 0) if isinstance(display_rate, dict) else 0

                # Extract rate details
                rates = tt.get("teeTimeRates", [])
                is_hot_deal = any(r.get("isHotDeal", False) for r in rates)
                is_cart_included = any(r.get("isCartIncluded", False) for r in rates)
                is_trade = any(r.get("isTradeOffer", False) for r in rates)
                rate_name = rates[0].get("rateName", "") if rates else ""

                # Build booking URL
                fac = tt.get("facility", {})
                slug = fac.get("seoFriendlyName", f"{facility_id}-{course_id}")
                detail_url = tt.get("detailUrl", "")
                booking_url = f"https://www.golfnow.com{detail_url}" if detail_url else f"https://www.golfnow.com/tee-times/facility/{slug}/search?date={date}&players={players}"

                # Player availability
                player_rule = tt.get("playerRule", {})
                max_players = player_rule.get("maxPlayers", 4) if isinstance(player_rule, dict) else 4

                slots.append({
                    "course_id": course_id,
                    "date": date,
                    "time": normalized_time,
                    "price": float(price),
                    "players_available": max_players,
                    "walk_ride": "ride" if is_cart_included else "walk",
                    "booking_url": booking_url,
                    "source": "golfnow_api",
                    "is_new": True,
                    "is_hot_deal": is_hot_deal,
                    "is_trade_offer": is_trade,
                    "rate_name": rate_name,
                    "raw_data": {
                        "price": price,
                        "is_hot_deal": is_hot_deal,
                        "is_cart_included": is_cart_included,
                        "rate_name": rate_name,
                    },
                })

            logger.info("GolfNow API: %s on %s -> %d slots", course_id, date, len(slots))

    except httpx.TimeoutException:
        logger.error("GolfNow API timeout for %s on %s", course_id, date)
    except Exception as e:
        logger.error("GolfNow API error for %s: %s", course_id, str(e))

    return slots


def _normalize_time(time_iso: str, time_formatted: str, meridian: str) -> str | None:
    """Convert GolfNow API time to HH:MM 24h local Chicago time.

    VERIFIED against live GolfNow API on 2026-04-14:
      API returns: formatted="6:18" meridian="AM" → booking page shows 6:18 AM ✓
      API returns: formatted="10:00" meridian="AM" → booking page shows 10:00 AM ✓

    The formatted+meridian fields ARE the correct local time. Use them directly.
    The ISO date field has "+00:00" but this is NOT UTC — it is local time
    with a misleading timezone suffix. Never do timezone math on it.
    """
    # PRIMARY: Use formatted + meridian (always correct)
    if time_formatted and meridian:
        raw = f"{time_formatted} {meridian}"
        try:
            t = datetime.strptime(raw, "%I:%M %p")
            return t.strftime("%H:%M")
        except ValueError:
            pass

    # FALLBACK: Strip fake timezone from ISO, use raw time value
    if time_iso:
        try:
            clean = time_iso
            if "T" in clean:
                clean = clean.split("T")[1]
            for char in ("+", "Z"):
                idx = clean.find(char)
                if idx >= 0:
                    clean = clean[:idx]
            idx = clean.find("-", 2)
            if idx > 0:
                clean = clean[:idx]
            parts = clean.split(":")
            if len(parts) >= 2:
                return f"{int(parts[0]):02d}:{parts[1]}"
        except (ValueError, TypeError, IndexError):
            pass

    return None


async def search_all_golfnow_courses(date: str, players: int = 4) -> list[dict]:
    """Search all GolfNow courses."""
    all_slots = []
    courses = get_courses_by_platform("golfnow")
    for course in courses:
        fid = course.get("golfnow_facility_id")
        if not fid:
            continue
        slots = await search_golfnow_facility(fid, course["id"], date, players)
        all_slots.extend(slots)
        await asyncio.sleep(random.uniform(1, 3))
    return all_slots


# Keep for backward compatibility with snipe.py imports
async def cleanup_browser():
    global _browser, _playwright
    if _browser:
        try:
            await _browser.close()
        except Exception:
            pass
        _browser = None
    if _playwright:
        try:
            await _playwright.stop()
        except Exception:
            pass
        _playwright = None


# === Playwright helpers (used by chronogolf.py, foreup.py, direct.py) ===

from playwright.async_api import async_playwright

_browser = None
_playwright = None

USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
]

STEALTH_JS = """
Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
window.chrome = { runtime: {} };
"""

TIMEZONES = ["America/Chicago", "America/New_York", "America/Denver"]


async def _get_browser():
    global _browser, _playwright
    if _browser is None or not _browser.is_connected():
        if _playwright:
            try:
                await _playwright.stop()
            except Exception:
                pass
        _playwright = await async_playwright().start()
        _browser = await _playwright.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--disable-blink-features=AutomationControlled",
            ],
        )
    return _browser


async def _create_stealth_context(browser):
    import random as _rand
    width = _rand.choice([1280, 1366, 1440, 1920])
    height = _rand.choice([800, 900, 1024, 1080])
    context = await browser.new_context(
        user_agent=_rand.choice(USER_AGENTS),
        viewport={"width": width, "height": height},
        locale="en-US",
        timezone_id=_rand.choice(TIMEZONES),
        color_scheme="light",
    )
    await context.add_init_script(STEALTH_JS)
    return context
