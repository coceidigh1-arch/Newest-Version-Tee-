"""
ForeUP Scraper — API + Playwright fallback
Covers: Highlands of Elgin, Bowes Creek CC
Tries ForeUP's public API first, falls back to Playwright if needed.
"""

import asyncio
import httpx
import logging
import re
import random
from datetime import datetime
from playwright.async_api import TimeoutError as PlaywrightTimeout
from app.models.courses import COURSES
from app.scrapers.golfnow_v2 import _get_browser, _create_stealth_context

logger = logging.getLogger(__name__)

# ForeUP API booking class IDs (discovered via site inspection)
FOREUP_BOOKING_CLASSES = {
    "highlands_elgin": "1281",
    "bowes_creek": "1280",
}

FOREUP_URLS = {
    "highlands_elgin": "https://highlandsofelgin.com/book-a-tee-time/",
    "bowes_creek": "https://bowescreekcc.com/",
}

FOREUP_API = "https://foreupsoftware.com/index.php/api/booking/times"


async def search_foreup(course_id: str, date: str, players: int = 4) -> list[dict]:
    """Search ForeUP - try API first, fall back to Playwright."""
    # Try API first (fastest)
    slots = await _try_foreup_api(course_id, date, players)
    if slots:
        return slots

    # Fall back to Playwright
    return await _try_foreup_playwright(course_id, date, players)


async def _try_foreup_api(course_id: str, date: str, players: int) -> list[dict]:
    """Try the ForeUP public API endpoint."""
    booking_class = FOREUP_BOOKING_CLASSES.get(course_id)
    if not booking_class:
        return []

    slots = []
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(
                FOREUP_API,
                params={
                    "date": date,
                    "holes": 18,
                    "booking_class": booking_class,
                    "schedule_id": "",
                    "api_key": "no_limits",
                },
                headers={
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                    "Accept": "application/json",
                    "X-Requested-With": "XMLHttpRequest",
                },
            )

            if response.status_code == 200:
                data = response.json()
                items = data if isinstance(data, list) else data.get("times", data.get("teetimes", []))
                course = COURSES.get(course_id, {})

                for item in items:
                    if not isinstance(item, dict):
                        continue
                    time_raw = str(item.get("time", ""))
                    normalized = _normalize_time(time_raw)
                    if not normalized:
                        continue

                    price = float(item.get("green_fee", 0) or item.get("price", 0) or 0)
                    avail = int(item.get("available_spots", 4) or item.get("spots", 4) or 4)

                    if avail >= players:
                        slots.append({
                            "course_id": course_id,
                            "date": date,
                            "time": normalized,
                            "price": price,
                            "players_available": avail,
                            "walk_ride": course.get("walk_ride", "unknown"),
                            "booking_url": course.get("booking_url", ""),
                            "source": "foreup_api",
                            "is_new": True,
                        })

                logger.info("ForeUP API: %s on %s -> %d slots", course_id, date, len(slots))

    except Exception as e:
        logger.warning("ForeUP API failed for %s: %s — will try Playwright", course_id, str(e))

    return slots


async def _try_foreup_playwright(course_id: str, date: str, players: int) -> list[dict]:
    """Fall back to Playwright scraping."""
    base_url = FOREUP_URLS.get(course_id)
    if not base_url:
        return []

    slots = []
    context = None

    try:
        browser = await _get_browser()
        context = await _create_stealth_context(browser)
        page = await context.new_page()

        await page.route(
            re.compile(r"\.(png|jpg|jpeg|gif|svg|woff|woff2|ttf|eot|ico)$"),
            lambda route: route.abort(),
        )

        await page.goto(base_url, wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(random.randint(6000, 10000))

        # Look for ForeUP iframe
        foreup_frame = None
        for frame in page.frames:
            if "foreupsoftware" in frame.url or "foreup" in frame.url:
                foreup_frame = frame
                break

        target = foreup_frame or page

        # Scroll to load
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await page.wait_for_timeout(3000)

        raw_slots = await target.evaluate(r"""() => {
            const slots = [];
            const allText = document.body.innerText;
            const timePattern = /(\d{1,2}:\d{2}\s*(?:AM|PM))/gi;
            const pricePattern = /\$(\d+(?:\.\d{2})?)/g;
            const times = [...allText.matchAll(timePattern)].map(m => m[1]);
            const prices = [...allText.matchAll(pricePattern)].map(m => parseFloat(m[1]));

            const selectors = [
                '.booking-slot', '.tee-time-slot', '.time-slot',
                '[class*="teetime"]', '[class*="tee-time"]',
                '[class*="slot"]', '[class*="available"]',
                '.card', '.result', 'tr', 'li'
            ];

            for (const selector of selectors) {
                const elements = document.querySelectorAll(selector);
                for (const el of elements) {
                    const text = el.innerText;
                    if (!text || text.length > 500 || text.length < 5) continue;
                    const tm = text.match(/(\d{1,2}:\d{2}\s*(?:AM|PM))/i);
                    const pm = text.match(/\$(\d+(?:\.\d{2})?)/);
                    const plm = text.match(/(\d)\s*(?:player|golfer|spot|opening|avail)/i);
                    if (tm) {
                        slots.push({
                            time: tm[1],
                            price: pm ? parseFloat(pm[1]) : 0,
                            players: plm ? parseInt(plm[1]) : 4,
                        });
                    }
                }
            }

            if (slots.length === 0 && times.length > 0) {
                for (let i = 0; i < times.length; i++) {
                    const hour = parseInt(times[i].split(':')[0]);
                    const isPM = times[i].toUpperCase().includes('PM');
                    const actualHour = isPM && hour !== 12 ? hour + 12 : (!isPM && hour === 12 ? 0 : hour);
                    if (actualHour >= 5 && actualHour <= 19) {
                        slots.push({
                            time: times[i],
                            price: i < prices.length ? prices[i] : 0,
                            players: 4,
                        });
                    }
                }
            }
            return slots;
        }""")

        course = COURSES.get(course_id, {})
        seen_times = set()

        for raw in raw_slots:
            if raw.get("time"):
                normalized = _normalize_time(raw["time"])
                if normalized and normalized not in seen_times:
                    seen_times.add(normalized)
                    slots.append({
                        "course_id": course_id,
                        "date": date,
                        "time": normalized,
                        "price": raw.get("price", 0),
                        "players_available": raw.get("players", 4),
                        "walk_ride": course.get("walk_ride", "unknown"),
                        "booking_url": base_url,
                        "source": "foreup",
                        "is_new": True,
                    })

        logger.info("ForeUP Playwright: %s on %s -> %d slots", course_id, date, len(slots))

    except PlaywrightTimeout:
        logger.error("ForeUP timeout for %s on %s", course_id, date)
    except Exception as e:
        logger.error("ForeUP error for %s: %s", course_id, str(e))
    finally:
        if context:
            try:
                await context.close()
            except Exception:
                pass

    return slots


def _normalize_time(raw):
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
