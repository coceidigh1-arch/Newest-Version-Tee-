"""
Universal Golf Course Scraper — Playwright Stealth
Goes directly to each course's own website/booking page and extracts tee times.
No GolfNow facility ID needed — works with any booking platform.
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

# Direct booking URLs for courses without GolfNow facility IDs
DIRECT_URLS = {
    "balmoral_woods": "https://www.balmoralwoods.com",
    "bartlett_hills": "https://www.bartletthillsgc.com",
    "bridges_poplar": "https://www.bridgesofpoplarcreek.com",
    "broken_arrow": "https://www.brokenarrowgolfclub.com",
    "chevy_chase": "https://www.chevychasegolf.org",
    "coyote_run": "https://www.coyoterungolf.com",
    "fox_run": "https://www.foxrungolflinks.com",
    "green_garden": "https://www.greengardencc.com",
    "hilldale": "https://www.hilldalegolf.com",
    "links_carillon": "https://www.carillongolf.com",
    "lost_marsh": "https://www.lostmarsh.com",
    "pine_meadow": "https://www.pinemeadowgc.com",
    "prairie_bluff": "https://www.prairiebluff.com",
    "ruffled_feathers": "https://www.ruffledfeathersgc.com",
    "st_andrews": "https://www.standrewsgc.com",
    "seven_bridges": "https://www.sevenbridgesgolfclub.com",
    "sunset_valley": "https://www.sunsetvalleygolfcourse.org",
    "waters_edge": "https://www.watersedgegolf.com",
    "sanctuary": "https://www.golfsanctuary.com",
    "cantigny": "https://www.cantignygolf.com",
    "cog_hill_123": "https://www.coghillgolf.com",
    "cog_hill_4": "https://www.coghillgolf.com",
}


async def search_direct(course_id, date, players=4):
    """Search a course's own website for tee times using Playwright stealth."""
    base_url = DIRECT_URLS.get(course_id)
    if not base_url:
        return []

    course = COURSES.get(course_id, {})
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

        # Look for booking/tee-time links and navigate to them
        booking_link = await page.evaluate("""() => {
            var links = document.querySelectorAll('a');
            for (var i = 0; i < links.length; i++) {
                var text = (links[i].innerText || '').toLowerCase();
                var href = (links[i].href || '').toLowerCase();
                if (text.indexOf('tee time') >= 0 || text.indexOf('book') >= 0 ||
                    text.indexOf('reserve') >= 0 || text.indexOf('tee-time') >= 0 ||
                    href.indexOf('tee-time') >= 0 || href.indexOf('teetime') >= 0 ||
                    href.indexOf('booking') >= 0 || href.indexOf('reserve') >= 0 ||
                    href.indexOf('golfnow') >= 0 || href.indexOf('foreup') >= 0 ||
                    href.indexOf('chronogolf') >= 0 || href.indexOf('quick18') >= 0 ||
                    href.indexOf('teesnap') >= 0) {
                    return links[i].href;
                }
            }
            return null;
        }""")

        if booking_link:
            try:
                await page.goto(booking_link, wait_until="domcontentloaded", timeout=30000)
                await page.wait_for_timeout(random.randint(6000, 10000))
            except Exception:
                pass

        # Scroll to trigger lazy loading
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2)")
        await page.wait_for_timeout(2000)
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await page.wait_for_timeout(3000)

        # Check for iframes (many courses embed booking in iframe)
        frames = page.frames
        target = page
        for frame in frames:
            frame_url = frame.url.lower()
            if any(p in frame_url for p in ["foreup", "golfnow", "chronogolf", "teesnap",
                                              "quick18", "tee-time", "booking", "reserve"]):
                target = frame
                break

        # Extract tee time data from the page
        raw_slots = await target.evaluate("""() => {
            var slots = [];
            var allText = document.body.innerText;
            var timePattern = /(\\d{1,2}:\\d{2}\\s*(?:AM|PM))/gi;
            var pricePattern = /\\$(\\d+(?:\\.\\d{2})?)/g;
            var times = [];
            var match;
            while ((match = timePattern.exec(allText)) !== null) { times.push(match[1]); }
            var prices = [];
            while ((match = pricePattern.exec(allText)) !== null) { prices.push(parseFloat(match[1])); }

            // Try structured elements first
            var selectors = [
                '[class*="teetime"]', '[class*="tee-time"]', '[class*="tee_time"]',
                '[class*="slot"]', '[class*="booking"]', '[class*="available"]',
                '[class*="time-slot"]', '[class*="timeslot"]',
                '.card', '.result', 'tr', 'li'
            ];

            for (var s = 0; s < selectors.length; s++) {
                var elements = document.querySelectorAll(selectors[s]);
                for (var e = 0; e < elements.length; e++) {
                    var text = elements[e].innerText;
                    if (!text || text.length > 500 || text.length < 5) continue;
                    var tm = text.match(/(\\d{1,2}:\\d{2}\\s*(?:AM|PM))/i);
                    var pm = text.match(/\\$(\\d+(?:\\.\\d{2})?)/);
                    var plm = text.match(/(\\d)\\s*(?:player|golfer|spot|opening|avail)/i);
                    if (tm) {
                        slots.push({
                            time: tm[1],
                            price: pm ? parseFloat(pm[1]) : 0,
                            players: plm ? parseInt(plm[1]) : 4
                        });
                    }
                }
            }

            // Fallback to raw text extraction
            if (slots.length === 0 && times.length > 0) {
                for (var i = 0; i < times.length; i++) {
                    var hour = parseInt(times[i].split(':')[0]);
                    var isPM = times[i].toUpperCase().indexOf('PM') >= 0;
                    var actualHour = isPM && hour !== 12 ? hour + 12 : (!isPM && hour === 12 ? 0 : hour);
                    if (actualHour >= 5 && actualHour <= 19) {
                        slots.push({
                            time: times[i],
                            price: i < prices.length ? prices[i] : 0,
                            players: 4
                        });
                    }
                }
            }

            // Also capture any GolfNow facility ID if embedded
            var golfnowLinks = document.querySelectorAll('a[href*="golfnow.com/tee-times/facility/"]');
            var facilityId = null;
            if (golfnowLinks.length > 0) {
                var m = golfnowLinks[0].href.match(/facility\\/(\\d+)-/);
                if (m) facilityId = m[1];
            }

            return {slots: slots, facilityId: facilityId, url: window.location.href};
        }""")

        # If we found a GolfNow facility ID, log it for future use
        if raw_slots.get("facilityId"):
            logger.info("DISCOVERED GolfNow facility ID for %s: %s", course_id, raw_slots["facilityId"])

        seen_times = set()
        for raw in raw_slots.get("slots", []):
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
                        "booking_url": raw_slots.get("url", base_url),
                        "source": "direct",
                        "is_new": True,
                    })

        logger.info("Direct: %s on %s -> %d slots", course_id, date, len(slots))

    except PlaywrightTimeout:
        logger.error("Direct timeout for %s on %s", course_id, date)
    except Exception as e:
        logger.error("Direct error for %s: %s", course_id, str(e))
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
    return None
