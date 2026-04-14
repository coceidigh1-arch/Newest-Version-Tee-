"""
Chronogolf (Lightspeed) Scraper — Playwright Stealth
Covers: Preserve at Oak Meadows, Glen Club
Chronogolf loads tee times via JavaScript — requires a real browser.
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

CHRONOGOLF_URLS = {
    "preserve_oak": "https://www.chronogolf.com/club/oak-meadows-golf-course#teetimes",
    "glen_club": "https://www.chronogolf.com/club/the-glen-club#teetimes",
    "bolingbrook": "https://www.chronogolf.com/club/bolingbrook-golf-club#teetimes",
}


async def search_chronogolf(course_id: str, date: str, players: int = 4) -> list[dict]:
    """Search a Chronogolf-powered course for tee times using Playwright."""
    base_url = CHRONOGOLF_URLS.get(course_id)
    if not base_url:
        return []

    url = f"{base_url}?date={date}&nb_holes=18&nb_players={players}"
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
        await page.wait_for_timeout(random.randint(6000, 10000))

        # Scroll to load all tee times
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await page.wait_for_timeout(3000)

        # Extract tee times from rendered page
        raw_slots = await page.evaluate(r"""() => {
            const slots = [];
            const allText = document.body.innerText;
            const timePattern = /(\d{1,2}:\d{2}\s*(?:AM|PM))/gi;
            const pricePattern = /\$(\d+(?:\.\d{2})?)/g;

            const selectors = [
                '[class*="teetime"]', '[class*="tee-time"]', '[class*="tee_time"]',
                '[class*="slot"]', '[class*="booking"]', '[class*="available"]',
                '[class*="time-slot"]', '[class*="timeslot"]', '[class*="reservation"]',
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
                        "walk_ride": "ride" if course.get("walk_ride") == "ride_included" else "unknown",
                        "booking_url": course.get("chronogolf_url") or course.get("booking_url", ""),
                        "source": "chronogolf",
                        "is_new": True,
                    })

        logger.info("Chronogolf: %s on %s -> %d slots", course_id, date, len(slots))

    except PlaywrightTimeout:
        logger.error("Chronogolf timeout for %s on %s", course_id, date)
    except Exception as e:
        logger.error("Chronogolf error for %s: %s", course_id, str(e))
    finally:
        if context:
            try:
                await context.close()
            except Exception:
                pass

    return slots


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
    try:
        t = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        return t.strftime("%H:%M")
    except (ValueError, TypeError):
        pass
    return None
