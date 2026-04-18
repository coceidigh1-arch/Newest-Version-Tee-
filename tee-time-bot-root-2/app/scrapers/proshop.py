"""
ProShopTeetimes scraper — Playwright stealth

ProShop uses a multi-step ASP.NET flow that we have to click through:

    SelectPlayers.aspx?CourseID={id}
        │   click "Foursome" / "Threesome" / "Twosome" / "Single"
        ▼
    SelectDate.aspx (session token baked into URL path)
        │   click a[href*="dt=M/D/YYYY"]
        ▼
    SelectTime.aspx?dt=M/D/YYYY
        │   scrape a[href*="TeeTimeSelected.aspx?TTID=…"]

Each tee-time anchor's inner text is shaped roughly like:
    "9:40am 18H w Cart:$115.00 Includes Sales Tax Plus $2.99 Booking Fee …"

We pull the time and price with regex, normalize to 24h, and hand back a
slot dict. Booking URL is the anchor href so it round-trips the user's
click directly to the right tee time.

Verified against live site 2026-04-17: Bowes Creek (CourseID=94) Sat Apr 18
returned 41 slots ($115 → $75 sliding scale), which matches what the course
shows to a human browsing the site.
"""

from __future__ import annotations

import logging
import re
from datetime import datetime

from playwright.async_api import TimeoutError as PlaywrightTimeout

from app.models.courses import COURSES
from app.scrapers.golfnow_v2 import _get_browser, _create_stealth_context

logger = logging.getLogger(__name__)

PROSHOP_BASE = "https://booking.proshopteetimes.com"

_PLAYER_LABEL = {1: "Single", 2: "Twosome", 3: "Threesome", 4: "Foursome"}
_TIME_RE = re.compile(r"(\d{1,2}:\d{2})\s*(am|pm)", re.IGNORECASE)
_PRICE_RE = re.compile(r"\$(\d+(?:\.\d{2})?)")
_COURSE_ID_FROM_URL_RE = re.compile(r"CourseID=(\d+)")


def _proshop_course_id(course: dict) -> str | None:
    """Prefer an explicit `proshop_course_id` in courses.py; fall back to
    extracting `CourseID=…` from the configured booking URL."""
    explicit = course.get("proshop_course_id")
    if explicit:
        return str(explicit)
    m = _COURSE_ID_FROM_URL_RE.search(course.get("booking_url", "") or "")
    return m.group(1) if m else None


def _format_proshop_date(date: str) -> str:
    """YYYY-MM-DD → M/D/YYYY (no zero-padding; matches the site's link format)."""
    dt = datetime.strptime(date, "%Y-%m-%d")
    return f"{dt.month}/{dt.day}/{dt.year}"


def _normalize_time(am_pm_time: str) -> str | None:
    """'9:40am' → '09:40', '12:50pm' → '12:50'. Returns None on malformed input."""
    m = _TIME_RE.search(am_pm_time)
    if not m:
        return None
    hour, minute = m.group(1).split(":")
    hour_i = int(hour)
    minute_i = int(minute)
    mer = m.group(2).lower()
    if mer == "pm" and hour_i != 12:
        hour_i += 12
    elif mer == "am" and hour_i == 12:
        hour_i = 0
    return f"{hour_i:02d}:{minute_i:02d}"


def _parse_anchor(href: str, text: str, course_id: str, date: str) -> dict | None:
    """Turn one `<a href=...TTID=...>text</a>` into a slot dict."""
    normalized = _normalize_time(text)
    if not normalized:
        return None
    price_m = _PRICE_RE.search(text)
    price = float(price_m.group(1)) if price_m else 0.0
    return {
        "course_id": course_id,
        "date": date,
        "time": normalized,
        "price": price,
        # We clicked a specific player-count button before landing on the
        # listing, so every time shown can accommodate that many golfers.
        "players_available": 4,
        "walk_ride": "ride" if "cart" in text.lower() else "unknown",
        "booking_url": href,
        "source": "proshop_teetimes",
        "is_new": True,
    }


async def search_proshop(course_id: str, date: str, players: int = 4) -> list[dict]:
    """Scrape one (course, date) via the ProShop three-step flow."""
    course = COURSES.get(course_id, {})
    proshop_id = _proshop_course_id(course)
    if not proshop_id:
        logger.info("proshop: no CourseID for %s (check proshop_course_id or booking_url)", course_id)
        return []

    slots: list[dict] = []
    context = None

    try:
        browser = await _get_browser()
        context = await _create_stealth_context(browser)
        page = await context.new_page()

        # Step 1: SelectPlayers.aspx, click player count
        start_url = f"{PROSHOP_BASE}/SelectPlayers.aspx?CourseID={proshop_id}"
        await page.goto(start_url, wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(1500)

        player_label = _PLAYER_LABEL.get(players, "Foursome")
        try:
            await page.get_by_text(player_label, exact=False).first.click(timeout=10000)
        except PlaywrightTimeout:
            logger.warning("proshop: couldn't find %s button for %s", player_label, course_id)
            return []

        # Step 2: SelectDate.aspx — wait for the URL to redirect, then click
        # the anchor for our target date. If the date isn't in the site's
        # visible window, there's no anchor and we return empty for that day.
        try:
            await page.wait_for_url(re.compile(r"SelectDate\.aspx"), timeout=15000)
        except PlaywrightTimeout:
            logger.warning("proshop: never reached SelectDate for %s", course_id)
            return []
        await page.wait_for_timeout(1200)

        dt_param = _format_proshop_date(date)
        # href contains "dt=4/18/2026" — use a CSS partial match
        date_selector = f'a[href*="dt={dt_param}"]'
        try:
            await page.locator(date_selector).first.click(timeout=8000)
        except PlaywrightTimeout:
            logger.info("proshop: no date link for %s on %s (outside booking window?)", course_id, date)
            return []

        # Step 3: SelectTime.aspx — wait for navigation, then extract anchors
        try:
            await page.wait_for_url(re.compile(r"SelectTime\.aspx"), timeout=15000)
        except PlaywrightTimeout:
            logger.warning("proshop: never reached SelectTime for %s on %s", course_id, date)
            return []
        await page.wait_for_timeout(2000)

        raw_anchors = await page.evaluate(
            """() => Array.from(document.querySelectorAll('a[href*="TeeTimeSelected.aspx?TTID="]'))
                 .map(a => ({href: a.href, text: (a.innerText || '').trim()}))"""
        )

        seen_times: set[str] = set()
        for a in raw_anchors:
            slot = _parse_anchor(a.get("href", ""), a.get("text", ""), course_id, date)
            if slot and slot["time"] not in seen_times:
                seen_times.add(slot["time"])
                slots.append(slot)

        logger.info("proshop: %s on %s -> %d slots", course_id, date, len(slots))

    except PlaywrightTimeout:
        logger.error("proshop timeout for %s on %s", course_id, date)
    except Exception as exc:
        logger.error("proshop error for %s on %s: %s", course_id, date, exc)
    finally:
        if context:
            try:
                await context.close()
            except Exception:
                pass

    return slots
