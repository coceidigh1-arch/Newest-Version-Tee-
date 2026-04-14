"""
CPS Golf Scraper — Playwright DOM extraction
Covers: Mistwood Golf Club
CPS Golf uses a custom .NET booking system with JavaScript-rendered tee times.
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

CPS_COURSES = {
    "mistwood": {
        "base_url": "https://mistwood.cps.golf/onlineresweb/search-teetime",
        "params": "TeeOffTimeMin=0&TeeOffTimeMax=23",
    },
}


async def search_cps_golf(course_id: str, date: str, players: int = 4) -> list[dict]:
    """Search a CPS Golf-powered course for tee times."""
    config = CPS_COURSES.get(course_id)
    if not config:
        return []

    # CPS Golf ignores URL date params — must click calendar dates
    url = f"{config['base_url']}?{config['params']}"
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

        # Navigate to the correct date by clicking the calendar
        target = datetime.strptime(date, "%Y-%m-%d")
        today = datetime.now()

        # If target month is ahead of current, click forward arrow
        months_ahead = (target.year - today.year) * 12 + (target.month - today.month)
        for _ in range(months_ahead):
            try:
                await page.click('[class*="calendar"] [class*="next"], [class*="right-arrow"], button:has-text("›")', timeout=3000)
                await page.wait_for_timeout(1000)
            except Exception:
                break

        # Click the target day number in the calendar
        day_str = str(target.day)
        try:
            # Find calendar day cells and click the matching one
            await page.evaluate(f"""() => {{
                const cells = document.querySelectorAll('[class*="calendar"] td, [class*="calendar"] [class*="day"], [class*="date-cell"]');
                for (const cell of cells) {{
                    const text = cell.innerText.trim();
                    if (text === '{day_str}' && !cell.classList.contains('disabled') && !cell.classList.contains('past')) {{
                        cell.click();
                        return true;
                    }}
                }}
                // Fallback: find any clickable element with just the day number
                const allEls = document.querySelectorAll('span, div, td, a, button');
                for (const el of allEls) {{
                    if (el.innerText.trim() === '{day_str}' && el.offsetParent !== null) {{
                        const rect = el.getBoundingClientRect();
                        if (rect.width < 60 && rect.height < 60 && rect.width > 10) {{
                            el.click();
                            return true;
                        }}
                    }}
                }}
                return false;
            }}""")
            await page.wait_for_timeout(5000)
        except Exception as e:
            logger.warning("CPS Golf: could not click date %s: %s", date, e)

        # Scroll to trigger lazy loading
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
                    "source": "cps_golf",
                    "is_new": True,
                })

        logger.info("CPS Golf: %s on %s -> %d slots", course_id, date, len(slots))

    except PlaywrightTimeout:
        logger.error("CPS Golf timeout for %s on %s", course_id, date)
    except Exception as e:
        logger.error("CPS Golf error for %s: %s", course_id, str(e))
    finally:
        if context:
            try:
                await context.close()
            except Exception:
                pass

    return slots


_EXTRACT_JS = r"""() => {
    const slots = [];

    // CPS Golf uses teetimeitem-container__item elements
    // Time is split as "2:50\nP\nM" so we normalize newlines to spaces
    const teeItems = document.querySelectorAll('[class*="teetimeitem-container"]');
    
    for (const el of teeItems) {
        const text = el.innerText.replace(/\n/g, ' ').replace(/\s+/g, ' ').trim();
        if (!text || text.length < 5) continue;
        
        // Match time like "2:50 P M" or "10:30 A M" (CPS splits P and M)
        const tm = text.match(/(\d{1,2}:\d{2})\s*([AP])\s*M/i);
        const pm = text.match(/\$(\d+(?:\.\d{2})?)/);
        // Match golfers like "1 - 4 GOLFERS" or "1 GOLFERS"
        const plm = text.match(/(\d)\s*(?:-\s*(\d))?\s*GOLFER/i);
        
        if (tm) {
            const timeStr = tm[1] + ' ' + tm[2] + 'M';
            slots.push({
                time: timeStr,
                price: pm ? parseFloat(pm[1]) : 0,
                players: plm && plm[2] ? parseInt(plm[2]) : (plm ? parseInt(plm[1]) : 4),
            });
        }
    }

    // Fallback: try generic extraction with normalized text
    if (slots.length === 0) {
        const allText = document.body.innerText.replace(/\n/g, ' ').replace(/\s+/g, ' ');
        const timePattern = /(\d{1,2}:\d{2})\s*([AP])\s*M/gi;
        const pricePattern = /\$(\d+(?:\.\d{2})?)/g;
        const times = [...allText.matchAll(timePattern)].map(m => m[1] + ' ' + m[2] + 'M');
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
