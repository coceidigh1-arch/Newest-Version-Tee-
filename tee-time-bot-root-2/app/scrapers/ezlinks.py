"""
EZLinks Scraper — Playwright DOM extraction
Covers: The Glen Club, Bridges of Poplar Creek CC, Links at Carillon
EZLinks is a SPA behind Cloudflare. Requires Playwright for rendering.
"""

import asyncio
import logging
import re
import random
from datetime import datetime
from playwright.async_api import TimeoutError as PlaywrightTimeout
from app.models.courses import COURSES
from app.scrapers.golfnow_v2 import _get_browser, _create_stealth_context

logger = logging.getLogger(__name__)

EZLINKS_COURSES = {
    "glen_club": {
        "base_url": "https://theglenclub.ezlinksgolf.com/index.html#/search",
    },
    "bridges_poplar": {
        "base_url": "https://poplarcreekccpp.ezlinksgolf.com/index.html#/search",
    },
    "links_carillon": {
        "base_url": "https://carillon.ezlinksgolf.com/index.html#/search",
    },
}


async def search_ezlinks(course_id: str, date: str, players: int = 4) -> list[dict]:
    """Search an EZLinks-powered course for tee times."""
    config = EZLINKS_COURSES.get(course_id)
    if not config:
        return []

    # EZLinks uses hash-based routing with date params
    url = f"{config['base_url']}?date={date}&players={players}&holes=18"
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

        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(random.randint(8000, 12000))

        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await page.wait_for_timeout(3000)

        raw_slots = await page.evaluate(_EXTRACT_JS)

        course = COURSES.get(course_id, {})
        seen_times = set()

        for raw in raw_slots:
            normalized = _normalize_time(raw.get("time", ""))
            if normalized and normalized not in seen_times:
                seen_times.add(normalized)
                slots.append({
                    "course_id": course_id,
                    "date": date,
                    "time": normalized,
                    "price": raw.get("price", 0),
                    "players_available": raw.get("players", 4),
                    "walk_ride": "ride" if course.get("walk_ride") == "ride_included" else "unknown",
                    "booking_url": course.get("booking_url", ""),
                    "source": "ezlinks",
                    "is_new": True,
                })

        logger.info("EZLinks: %s on %s -> %d slots", course_id, date, len(slots))

    except PlaywrightTimeout:
        logger.error("EZLinks timeout for %s on %s", course_id, date)
    except Exception as e:
        logger.error("EZLinks error for %s: %s", course_id, str(e))
    finally:
        if context:
            try:
                await context.close()
            except Exception:
                pass

    return slots


_EXTRACT_JS = r"""() => {
    const slots = [];
    const allText = document.body.innerText;
    const timePattern = /(\d{1,2}:\d{2}\s*(?:AM|PM))/gi;
    const pricePattern = /\$(\d+(?:\.\d{2})?)/g;

    const selectors = [
        '[class*="teetime"]', '[class*="tee-time"]', '[class*="tee_time"]',
        '[class*="slot"]', '[class*="booking"]', '[class*="available"]',
        '[class*="time-slot"]', '[class*="timeslot"]', '[class*="reservation"]',
        '[class*="search-result"]', '[class*="rate"]',
        '.card', '.result', 'tr', 'li', 'article'
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

    if (slots.length === 0) {
        const times = [...allText.matchAll(timePattern)].map(m => m[1]);
        const prices = [...allText.matchAll(pricePattern)].map(m => parseFloat(m[1]));
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
}"""


def _normalize_time(raw: str) -> str | None:
    if not raw:
        return None
    raw = raw.strip().upper()
    for fmt in ("%I:%M %p", "%I:%M%p", "%H:%M", "%H:%M:%S"):
        try:
            t = datetime.strptime(raw, fmt)
            return t.strftime("%H:%M")
        except ValueError:
            continue
    return None
