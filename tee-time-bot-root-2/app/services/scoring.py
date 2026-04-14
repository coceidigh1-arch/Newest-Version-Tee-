"""
Tee Time Scoring Engine
Scores each discovered slot 0-100 based on user preferences.
Determines action: IGNORE / ALERT / CONFIRM / AUTOBOOK
"""

import json
import hashlib
import logging
from datetime import datetime, timedelta
from app.models.courses import get_course

logger = logging.getLogger(__name__)

DAY_MAP = {
    0: "monday", 1: "tuesday", 2: "wednesday", 3: "thursday",
    4: "friday", 5: "saturday", 6: "sunday",
}


def generate_slot_id(course_id: str, date: str, time: str) -> str:
    raw = f"{course_id}|{date}|{time}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def score_tee_time(slot: dict, prefs: dict, course: dict) -> int:
    score = 0

    # 1. COURSE PRIORITY (0-30 points)
    must_play = json.loads(prefs.get("must_play_courses", "[]")) if isinstance(prefs.get("must_play_courses"), str) else prefs.get("must_play_courses", [])
    nice_to_have = json.loads(prefs.get("nice_to_have_courses", "[]")) if isinstance(prefs.get("nice_to_have_courses"), str) else prefs.get("nice_to_have_courses", [])

    course_id = slot.get("course_id", "")
    if course_id in must_play:
        score += 30
    elif course_id in nice_to_have:
        score += 20
    else:
        score += 5  # deal-only tier

    # 2. DAY OF WEEK (0-20 points)
    try:
        slot_date = datetime.strptime(slot["date"], "%Y-%m-%d")
        day_name = DAY_MAP[slot_date.weekday()]
        preferred_days = json.loads(prefs.get("preferred_days", '["saturday","sunday"]')) if isinstance(prefs.get("preferred_days"), str) else prefs.get("preferred_days", ["saturday", "sunday"])

        if day_name in preferred_days:
            score += 20
        elif day_name in ("friday", "thursday"):
            score += 8
        else:
            score += 0
    except (ValueError, KeyError):
        pass

    # 3. TIME WINDOW (0-20 points)
    try:
        slot_time = datetime.strptime(slot["time"], "%H:%M")
        earliest = datetime.strptime(prefs.get("earliest_time", "05:00"), "%H:%M")
        latest = datetime.strptime(prefs.get("latest_time", "08:00"), "%H:%M")

        if earliest <= slot_time <= latest:
            # Bonus for being close to center of preferred window
            center = earliest + (latest - earliest) / 2
            distance_mins = abs((slot_time - center).total_seconds()) / 60
            score += max(20 - int(distance_mins / 10), 15)
        else:
            # Check acceptable extended window (2 hours beyond preferred)
            extended_latest = latest + timedelta(hours=2)
            if earliest <= slot_time <= extended_latest:
                score += 8
            else:
                score -= 5
    except (ValueError, KeyError):
        score += 10  # Unknown time, give benefit of doubt

    # 4. PRICE (0-15 points)
    try:
        max_price = int(prefs.get("max_price", 150))
        slot_price = float(slot.get("price", 0))

        if slot_price <= 0:
            score += 10  # Price unknown
        elif slot_price <= max_price * 0.7:
            score += 15  # Great deal
        elif slot_price <= max_price * 0.85:
            score += 12
        elif slot_price <= max_price:
            score += 8
        elif slot_price <= max_price * 1.15:
            score += 3  # Slightly over
        else:
            score -= 5  # Too expensive
    except (ValueError, TypeError):
        score += 10

    # 5. PLAYER COUNT (0-10 points)
    try:
        needed = int(prefs.get("players", 4))
        available = int(slot.get("players_available", 4))

        if available >= needed:
            score += 10
        elif available >= needed - 1:
            score += 5  # One short
        else:
            score -= 5
    except (ValueError, TypeError):
        score += 5

    # 6. FRESHNESS BONUS (0-5 points)
    if slot.get("is_new", False):
        score += 5

    # 7. WALK/RIDE MATCH (0-3 points)
    pref_ride = prefs.get("walk_ride", "ride")
    slot_ride = slot.get("walk_ride", "unknown")
    if pref_ride == "either" or slot_ride == "unknown" or slot_ride == pref_ride:
        score += 3

    return max(0, min(100, score))


def determine_action(score: int, course: dict, prefs: dict) -> str:
    """
    Determine what action to take based on score and course risk.
    Returns: IGNORE, ALERT, CONFIRM, AUTOBOOK
    """
    alert_thresh = int(prefs.get("alert_threshold", 55))
    confirm_thresh = int(prefs.get("confirm_threshold", 75))
    autobook_thresh = int(prefs.get("autobook_threshold", 90))

    if score < alert_thresh:
        return "IGNORE"

    if score >= autobook_thresh:
        # Only auto-book on safe courses
        if course.get("risk_tier") == "low" and course.get("platform") in ("golfnow", "chronogolf"):
            return "AUTOBOOK"
        elif course.get("risk_tier") == "medium":
            return "CONFIRM"
        else:
            return "ALERT"  # High risk = alert + deep link only

    if score >= confirm_thresh:
        if course.get("platform") in ("custom", "foreup") or course.get("risk_tier") == "high":
            return "ALERT"  # Can't auto-book these, just alert
        return "CONFIRM"

    return "ALERT"
