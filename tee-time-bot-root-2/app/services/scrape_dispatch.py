"""
Platform → scraper dispatcher.

A single source of truth for "given a course, which scraper should run it and
what status did the scan finish in." Centralizing this prevents the class of
bug we hit before, where the scanner's outer loop only knew about a handful of
platforms and silently ignored courses on every other platform.

Every dispatch returns:
    (slots: list[dict], status: str, error: str | None)

where `status` is one of the ScanStatus constants below — never None, never
implicit. Callers (the scanner + the /api/course/{id}/week endpoint) rely on
this contract to distinguish "scanner really checked and the course has no
availability" from "scanner didn't run" or "scanner blew up".
"""

from __future__ import annotations

import logging
from typing import Callable, Awaitable

from app.models.courses import COURSES
from app.scrapers.golfnow_v2 import search_golfnow_facility
from app.scrapers.chronogolf import search_chronogolf
from app.scrapers.foreup import search_foreup
from app.scrapers.direct import search_direct

logger = logging.getLogger(__name__)


class ScanStatus:
    """Finite set of outcomes for a single (course, date) scan attempt.

    Used for search_log rows AND surfaced on the /api/course/{id}/week
    endpoint so the dashboard can render an honest state (not just silence)."""

    OK = "ok"                     # scan ran, returned at least one slot
    EMPTY = "empty"               # scan ran, site truly had no availability
    UNSUPPORTED = "unsupported"   # platform has no scraper implementation yet
    CONFIG_MISSING = "config_missing"  # platform supported, but course config incomplete (e.g. missing facility ID)
    ERROR = "error"               # scraper raised an exception
    SKIPPED = "skipped"           # scan intentionally skipped (bad weather, circuit breaker)


ScraperFn = Callable[[str, str, int], Awaitable[list[dict]]]


async def _scan_golfnow(course_id: str, date: str, players: int) -> list[dict]:
    course = COURSES.get(course_id, {})
    facility_id = course.get("golfnow_facility_id")
    if not facility_id:
        # Surface this as CONFIG_MISSING at the dispatcher layer
        raise _ConfigMissing("golfnow_facility_id not set in courses.py")
    return await search_golfnow_facility(facility_id, course_id, date, players)


async def _scan_direct(course_id: str, date: str, players: int) -> list[dict]:
    return await search_direct(course_id, date, players)


async def _scan_chronogolf(course_id: str, date: str, players: int) -> list[dict]:
    return await search_chronogolf(course_id, date, players)


async def _scan_foreup(course_id: str, date: str, players: int) -> list[dict]:
    return await search_foreup(course_id, date, players)


# Platforms known to the dispatcher. Missing from this map => UNSUPPORTED.
# Keep ordering stable (doesn't affect correctness but helps grepping logs).
_SCRAPERS: dict[str, ScraperFn] = {
    "golfnow": _scan_golfnow,
    "chronogolf": _scan_chronogolf,
    "foreup": _scan_foreup,
    "direct": _scan_direct,
    "custom": _scan_direct,
}


class _ConfigMissing(Exception):
    """Raised by a scraper adapter when the course config lacks a required field."""


async def dispatch_scan(course_id: str, date: str, players: int = 4) -> tuple[list[dict], str, str | None]:
    """Run the right scraper for `course_id` on `date`.

    Returns `(slots, status, error)`. Never raises — every failure mode is
    captured in the status so the caller can log a search attempt for every
    (course, date) tuple we tried."""
    course = COURSES.get(course_id)
    if not course:
        return [], ScanStatus.CONFIG_MISSING, "unknown course_id"

    platform = course.get("platform", "unknown")
    scraper = _SCRAPERS.get(platform)

    if scraper is None:
        # Platforms with real scrapers aren't the problem — this is the place
        # where ezlinks/teeitup/whoosh/proshop_teetimes/cps_golf/golfback
        # surface instead of getting silently skipped.
        logger.info("scan[%s/%s]: unsupported platform %r — skipping", course_id, date, platform)
        return [], ScanStatus.UNSUPPORTED, f"No scraper implemented for platform '{platform}'"

    try:
        slots = await scraper(course_id, date, players)
    except _ConfigMissing as exc:
        logger.warning("scan[%s/%s]: config_missing: %s", course_id, date, exc)
        return [], ScanStatus.CONFIG_MISSING, str(exc)
    except Exception as exc:
        logger.error("scan[%s/%s] via %s raised %s: %s", course_id, date, platform, type(exc).__name__, exc)
        return [], ScanStatus.ERROR, f"{type(exc).__name__}: {exc}"

    if not slots:
        return [], ScanStatus.EMPTY, None

    return slots, ScanStatus.OK, None


def resolve_scan_status_for_platform(platform: str) -> str | None:
    """Return what a scan on this platform would immediately resolve to before
    running (useful for UI placeholders). None => platform has a scraper and
    an actual scan is needed to know the status."""
    if platform not in _SCRAPERS:
        return ScanStatus.UNSUPPORTED
    return None


def supported_platforms() -> list[str]:
    return sorted(_SCRAPERS.keys())
