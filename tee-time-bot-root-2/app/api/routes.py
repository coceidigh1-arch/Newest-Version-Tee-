"""
FastAPI Application
REST API for the tee time bot — serves the mobile app / PWA.
"""

import json
import uuid
import logging
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.models.database import init_db, get_db, generate_api_token
from app.models.courses import COURSES, get_all_courses, get_autobook_safe_courses, get_deep_link_only_courses
from app.services.scanner import run_scan_cycle, is_surge_mode
from app.utils.crypto import encrypt, decrypt
from app.config import settings
from app.services.auth import require_admin_key, authorize_user_request

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    logger.info("Database initialized")
    yield

app = FastAPI(
    title="Tee Time Bot API",
    description="Golf tee time search, alert, and booking agent for Chicago A-group courses",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Pydantic Models ---

class UserCreate(BaseModel):
    name: str
    email: str | None = None
    telegram_chat_id: str | None = None
    is_admin: bool = False

class UserPreferencesUpdate(BaseModel):
    players: int = 4
    preferred_days: list[str] = ["saturday", "sunday"]
    earliest_time: str = "05:00"
    latest_time: str = "08:00"
    max_price: int = 150
    walk_ride: str = "ride"
    max_rounds_week: int = 2
    monthly_budget: int = 600
    must_play_courses: list[str] = []
    nice_to_have_courses: list[str] = []
    deal_only_courses: list[str] = []
    course_overrides: dict = {}
    alert_threshold: int = 55
    confirm_threshold: int = 75
    autobook_threshold: int = 90

class PlatformAccountLink(BaseModel):
    platform: str  # golfnow, chronogolf, foreup
    username: str
    password: str

class TriggerScanRequest(BaseModel):
    course_ids: list[str] | None = None
    date: str | None = None


# --- Health ---

@app.get("/health")
async def health():
    db_ok = True
    last_scan = None
    try:
        db = await get_db()
        try:
            await db.execute_fetchone("SELECT 1")
            last_scan_row = await db.execute_fetchone(
                "SELECT timestamp, status, course_id, platform FROM search_log ORDER BY timestamp DESC LIMIT 1"
            )
            if last_scan_row:
                last_scan = dict(last_scan_row)
        finally:
            await db.close()
    except Exception:
        db_ok = False

    try:
        from app.scrapers.golfnow_v2 import SCRAPER_VERSION
        scraper_version = SCRAPER_VERSION
    except ImportError:
        scraper_version = "unknown"

    return {
        "status": "ok" if db_ok else "degraded",
        "database": "ok" if db_ok else "error",
        "timestamp": datetime.now().isoformat(),
        "surge_mode": is_surge_mode(),
        "scheduler_enabled": settings.ENABLE_SCHEDULER,
        "scraper_version": scraper_version,
        "last_scan": last_scan,
    }


# --- Courses ---

@app.get("/courses")
async def list_courses():
    """List all monitored courses with metadata."""
    return {
        "courses": [
            {
                "id": k,
                "name": v.get("name", k),
                "tier": v.get("tier", "B"),
                "platform": v.get("platform", "unknown"),
                "advance_days": v.get("advance_booking_days", 7),
                "advance_days_phone": v.get("advance_booking_phone"),
                "risk_tier": v.get("risk_tier", "low"),
                "cancel_type": v.get("cancel_type", "free_cancel"),
                "cancel_details": v.get("cancel_details", "Check course policy"),
                "prepaid": v.get("prepaid", False),
                "booking_url": v.get("booking_url", ""),
                "direct_url": v.get("direct_url", v.get("booking_url", "")),
                "distance_miles": v.get("distance_miles"),
                "direction": v.get("direction"),
                "range_included": v.get("range_included", False),
                "walk_ride": v.get("walk_ride"),
                "notes": v.get("notes"),
                "autobook_eligible": v.get("risk_tier", "low") == "low" and v.get("platform") in ("golfnow", "chronogolf"),
            }
            for k, v in COURSES.items()
        ],
        "total": len(COURSES),
        "autobook_safe": len(get_autobook_safe_courses()),
        "deep_link_only": len(get_deep_link_only_courses()),
    }

@app.get("/courses/{course_id}")
async def get_course_detail(course_id: str):
    """Get detailed info for a specific course."""
    course = COURSES.get(course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return {"id": course_id, **course}


# --- Users ---

@app.post("/users")
async def create_user(user: UserCreate, request: Request):
    """Create a new user profile."""
    await require_admin_key(request)
    user_id = str(uuid.uuid4())[:8]
    api_token = generate_api_token()
    db = await get_db()
    try:
        await db.execute(
            "INSERT INTO users (id, name, email, telegram_chat_id, api_token, is_admin) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, user.name, user.email, user.telegram_chat_id, api_token, int(user.is_admin)),
        )
        await db.execute("INSERT INTO user_preferences (user_id) VALUES (?)", (user_id,))
        await db.commit()
        return {
            "id": user_id,
            "name": user.name,
            "api_token": api_token,
            "message": "User created. Set preferences via PUT /users/{id}/preferences",
        }
    finally:
        await db.close()

@app.get("/users")
async def list_users(request: Request):
    """List all users."""
    await require_admin_key(request)
    db = await get_db()
    try:
        rows = await db.execute_fetchall("SELECT id, name, email, telegram_chat_id, is_admin, notification_enabled FROM users")
        return {"users": [dict(r) for r in rows]}
    finally:
        await db.close()

@app.get("/users/{user_id}")
async def get_user(user_id: str, request: Request):
    """Get user profile with preferences."""
    db = await get_db()
    try:
        await authorize_user_request(request, user_id, db)
        user = await db.execute_fetchone("SELECT * FROM users WHERE id = ?", (user_id,))
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        prefs = await db.execute_fetchone("SELECT * FROM user_preferences WHERE user_id = ?", (user_id,))
        accounts = await db.execute_fetchall(
            "SELECT platform, is_active, last_login_at, last_error FROM user_platform_accounts WHERE user_id = ?",
            (user_id,),
        )

        return {
            "user": dict(user),
            "preferences": dict(prefs) if prefs else None,
            "linked_accounts": [dict(a) for a in accounts],
        }
    finally:
        await db.close()

@app.put("/users/{user_id}/preferences")
async def update_preferences(user_id: str, prefs: UserPreferencesUpdate, request: Request):
    """Update user tee time preferences."""
    db = await get_db()
    try:
        await authorize_user_request(request, user_id, db)
        await db.execute(
            """INSERT OR REPLACE INTO user_preferences
            (user_id, players, preferred_days, earliest_time, latest_time,
             max_price, walk_ride, max_rounds_week, monthly_budget,
             must_play_courses, nice_to_have_courses, deal_only_courses,
             course_overrides, alert_threshold, confirm_threshold, autobook_threshold)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                user_id, prefs.players,
                json.dumps(prefs.preferred_days),
                prefs.earliest_time, prefs.latest_time,
                prefs.max_price, prefs.walk_ride,
                prefs.max_rounds_week, prefs.monthly_budget,
                json.dumps(prefs.must_play_courses),
                json.dumps(prefs.nice_to_have_courses),
                json.dumps(prefs.deal_only_courses),
                json.dumps(prefs.course_overrides),
                prefs.alert_threshold, prefs.confirm_threshold, prefs.autobook_threshold,
            ),
        )
        await db.commit()
        return {"message": "Preferences updated"}
    finally:
        await db.close()


# --- Platform Account Linking ---

@app.post("/users/{user_id}/link-account")
async def link_platform_account(user_id: str, account: PlatformAccountLink, request: Request):
    """Link a booking platform account (GolfNow, Chronogolf, etc.)."""
    if account.platform not in ("golfnow", "chronogolf", "foreup", "ezlinks"):
        raise HTTPException(status_code=400, detail="Invalid platform. Use: golfnow, chronogolf, foreup, ezlinks")

    db = await get_db()
    try:
        await authorize_user_request(request, user_id, db)
        enc_user = encrypt(account.username)
        enc_pass = encrypt(account.password)

        await db.execute(
            """INSERT OR REPLACE INTO user_platform_accounts
            (user_id, platform, username_encrypted, password_encrypted, is_active)
            VALUES (?, ?, ?, ?, 1)""",
            (user_id, account.platform, enc_user, enc_pass),
        )
        await db.commit()
        return {"message": f"{account.platform} account linked for user {user_id}"}
    finally:
        await db.close()

@app.delete("/users/{user_id}/link-account/{platform}")
async def unlink_platform_account(user_id: str, platform: str, request: Request):
    """Unlink a booking platform account."""
    db = await get_db()
    try:
        await authorize_user_request(request, user_id, db)
        await db.execute(
            "DELETE FROM user_platform_accounts WHERE user_id = ? AND platform = ?",
            (user_id, platform),
        )
        await db.commit()
        return {"message": f"{platform} account unlinked"}
    finally:
        await db.close()


# --- Tee Time Slots ---

@app.get("/slots")
async def list_slots(
    course_id: str | None = None,
    date: str | None = None,
    min_score: int = 0,
    action: str | None = None,
    limit: int = Query(default=500, le=1000),
):
    """List discovered tee time slots with optional filters."""
    db = await get_db()
    try:
        query = "SELECT * FROM seen_slots WHERE score >= ? AND disappeared_at IS NULL AND date >= date('now')"
        params = [min_score]

        if course_id:
            query += " AND course_id = ?"
            params.append(course_id)
        if date:
            query += " AND date = ?"
            params.append(date)
        if action:
            query += " AND action = ?"
            params.append(action)

        query += " ORDER BY date ASC, time ASC, score DESC LIMIT ?"
        params.append(limit)

        rows = await db.execute_fetchall(query, params)
        return {
            "slots": [
                {**dict(r), "course_name": COURSES.get(r["course_id"], {}).get("name", r["course_id"])}
                for r in rows
            ],
            "count": len(rows),
        }
    finally:
        await db.close()


# --- Bookings ---

@app.get("/bookings")
async def list_bookings(request: Request, user_id: str | None = None, status: str = "CONFIRMED"):
    """List bookings, optionally filtered by user and status."""
    db = await get_db()
    try:
        if user_id:
            await authorize_user_request(request, user_id, db)
        else:
            await require_admin_key(request)
        if user_id:
            rows = await db.execute_fetchall(
                "SELECT * FROM bookings WHERE booked_by = ? AND status = ? ORDER BY date DESC",
                (user_id, status),
            )
        else:
            rows = await db.execute_fetchall(
                "SELECT * FROM bookings WHERE status = ? ORDER BY date DESC",
                (status,),
            )
        return {"bookings": [dict(r) for r in rows]}
    finally:
        await db.close()


# --- Roll Calls ---

@app.get("/rollcalls")
async def list_roll_calls(request: Request, status: str = "PENDING"):
    """List active roll calls."""
    await require_admin_key(request)
    db = await get_db()
    try:
        rows = await db.execute_fetchall(
            """SELECT rc.*, ss.course_id, ss.date, ss.time, ss.price, ss.players_available
            FROM roll_calls rc
            JOIN seen_slots ss ON rc.slot_id = ss.id
            WHERE rc.status = ?
            ORDER BY rc.created_at DESC""",
            (status,),
        )

        result = []
        for r in rows:
            responses = await db.execute_fetchall(
                """SELECT rcr.*, u.name
                FROM roll_call_responses rcr
                JOIN users u ON rcr.user_id = u.id
                WHERE rcr.roll_call_id = ?""",
                (r["id"],),
            )
            result.append({
                **dict(r),
                "course_name": COURSES.get(r["course_id"], {}).get("name", ""),
                "responses": [dict(resp) for resp in responses],
            })

        return {"roll_calls": result}
    finally:
        await db.close()

@app.post("/rollcalls/{roll_call_id}/respond")
async def respond_to_roll_call(roll_call_id: str, user_id: str, response: str, request: Request):
    """Respond to a roll call (IN or OUT)."""
    if response.upper() not in ("IN", "OUT"):
        raise HTTPException(status_code=400, detail="Response must be IN or OUT")

    db = await get_db()
    try:
        await authorize_user_request(request, user_id, db)
        rc = await db.execute_fetchone("SELECT * FROM roll_calls WHERE id = ?", (roll_call_id,))
        if not rc:
            raise HTTPException(status_code=404, detail="Roll call not found")
        if rc["status"] != "PENDING":
            raise HTTPException(status_code=400, detail=f"Roll call is {rc['status']}")

        await db.execute(
            """INSERT OR REPLACE INTO roll_call_responses
            (roll_call_id, user_id, response)
            VALUES (?, ?, ?)""",
            (roll_call_id, user_id, response.upper()),
        )

        # Check if enough players have confirmed
        in_count = await db.execute_fetchone(
            "SELECT COUNT(*) as cnt FROM roll_call_responses WHERE roll_call_id = ? AND response = 'IN'",
            (roll_call_id,),
        )

        await db.commit()

        return {
            "message": f"Response recorded: {response.upper()}",
            "confirmed_players": in_count["cnt"] if in_count else 0,
            "needed": rc["min_players"],
            "ready_to_book": (in_count["cnt"] if in_count else 0) >= rc["min_players"],
        }
    finally:
        await db.close()


# --- Search Logs / Analytics ---

@app.get("/analytics/searches")
async def search_analytics(request: Request, hours: int = 24):
    await require_admin_key(request)
    """Get search activity stats for the last N hours."""
    db = await get_db()
    try:
        rows = await db.execute_fetchall(
            """SELECT course_id, platform, status,
            COUNT(*) as searches,
            SUM(slots_found) as total_slots,
            SUM(new_slots) as total_new,
            AVG(duration_ms) as avg_duration_ms
            FROM search_log
            WHERE timestamp > datetime('now', ? || ' hours')
            GROUP BY course_id, platform, status
            ORDER BY total_new DESC""",
            (f"-{hours}",),
        )
        return {"analytics": [dict(r) for r in rows], "period_hours": hours}
    finally:
        await db.close()

@app.get("/analytics/budget/{user_id}")
async def budget_analytics(user_id: str, request: Request):
    """Get budget tracking for a user."""
    db = await get_db()
    try:
        await authorize_user_request(request, user_id, db)
        month = datetime.now().strftime("%Y-%m")
        budget = await db.execute_fetchone(
            "SELECT * FROM budget_tracking WHERE user_id = ? AND month = ?",
            (user_id, month),
        )
        prefs = await db.execute_fetchone(
            "SELECT monthly_budget, max_rounds_week FROM user_preferences WHERE user_id = ?",
            (user_id,),
        )

        return {
            "month": month,
            "spent": budget["total_spent"] if budget else 0,
            "budget": prefs["monthly_budget"] if prefs else 600,
            "rounds_booked": budget["rounds_booked"] if budget else 0,
            "rounds_played": budget["rounds_played"] if budget else 0,
            "max_rounds_week": prefs["max_rounds_week"] if prefs else 2,
        }
    finally:
        await db.close()


# --- Manual Controls ---

@app.post("/scan/trigger")
async def trigger_scan(req: TriggerScanRequest | None = None, request: Request = None):
    if request is not None:
        await require_admin_key(request)
    """Manually trigger a scan cycle."""
    asyncio.create_task(run_scan_cycle())
    return {"message": "Scan triggered", "timestamp": datetime.now().isoformat()}

@app.post("/alerts/pause")
async def pause_alerts(user_id: str, course_id: str | None = None, hours: int = 12, request: Request = None):
    """Pause alerts for a user, optionally for a specific course."""
    db = await get_db()
    try:
        if request is not None:
            await authorize_user_request(request, user_id, db)
        suppressed_until = (datetime.now() + timedelta(hours=hours)).isoformat()
        await db.execute(
            "INSERT INTO alert_suppressions (user_id, course_id, suppressed_until, reason) VALUES (?, ?, ?, ?)",
            (user_id, course_id, suppressed_until, f"Manual pause for {hours}h"),
        )
        await db.commit()
        return {"message": f"Alerts paused until {suppressed_until}"}
    finally:
        await db.close()

@app.post("/alerts/resume")
async def resume_alerts(user_id: str, course_id: str | None = None, request: Request = None):
    """Resume alerts for a user."""
    db = await get_db()
    try:
        if request is not None:
            await authorize_user_request(request, user_id, db)
        if course_id:
            await db.execute(
                "DELETE FROM alert_suppressions WHERE user_id = ? AND course_id = ?",
                (user_id, course_id),
            )
        else:
            await db.execute(
                "DELETE FROM alert_suppressions WHERE user_id = ?",
                (user_id,),
            )
        await db.commit()
        return {"message": "Alerts resumed"}
    finally:
        await db.close()


# We need this import for the background task
import asyncio
from datetime import timedelta


# ===== SNIPE API =====

class SnipeRequest(BaseModel):
    telegram_chat_id: str
    course_id: str
    play_day: str = "sat"
    preferred_time: str = "07:00"
    players: int = 4


@app.post("/api/snipe")
async def create_snipe(req: SnipeRequest):
    """Create a snipe request from the dashboard."""
    from app.services.snipe import create_snipe_request

    # Find user by telegram chat ID
    db = await get_db()
    try:
        row = await db.execute_fetchone(
            "SELECT * FROM users WHERE telegram_chat_id = ?",
            (req.telegram_chat_id,),
        )
        if not row:
            raise HTTPException(status_code=404, detail="User not found. Connect Telegram first.")

        user_id = row["id"] if hasattr(row, "__getitem__") else dict(row)["id"]

        result = await create_snipe_request(
            user_id=user_id,
            course_id=req.course_id,
            play_day=req.play_day,
            preferred_time=req.preferred_time,
            auto_book=False,
        )
        return result
    finally:
        await db.close()


@app.get("/api/snipes/{telegram_chat_id}")
async def get_snipes(telegram_chat_id: str):
    """Get active snipes for a user."""
    db = await get_db()
    try:
        row = await db.execute_fetchone(
            "SELECT id FROM users WHERE telegram_chat_id = ?",
            (telegram_chat_id,),
        )
        if not row:
            return {"snipes": []}

        user_id = row["id"] if hasattr(row, "__getitem__") else dict(row)["id"]
        rows = await db.execute_fetchall(
            "SELECT * FROM snipe_requests WHERE user_id = ? AND status = 'PENDING' ORDER BY play_date",
            (user_id,),
        )
        snipes = []
        for r in rows:
            try:
                snipes.append({k: r[k] for k in r.keys()})
            except Exception:
                snipes.append(dict(r))
        return {"snipes": snipes}
    finally:
        await db.close()


# ===== CONNECT API (for dashboard user signup) =====

class ConnectRequest(BaseModel):
    name: str
    telegram_chat_id: str
    email: str = ""


@app.post("/api/connect")
async def connect_user(req: ConnectRequest):
    """Register a new user from the dashboard."""
    db = await get_db()
    try:
        existing = await db.execute_fetchone(
            "SELECT id, api_token FROM users WHERE telegram_chat_id = ?",
            (req.telegram_chat_id,),
        )
        if existing:
            uid = existing["id"] if hasattr(existing, "__getitem__") else dict(existing)["id"]
            token = existing["api_token"] if hasattr(existing, "__getitem__") else dict(existing).get("api_token")
            if not token:
                token = generate_api_token()
                await db.execute(
                    "UPDATE users SET api_token = ?, updated_at = datetime('now') WHERE id = ?",
                    (token, uid),
                )
                await db.commit()
            return {"message": "Already connected", "user_id": uid, "api_token": token}

        user_id = str(uuid.uuid4())[:8]
        api_token = generate_api_token()
        await db.execute(
            """INSERT INTO users (id, name, email, telegram_chat_id, api_token, notification_enabled, is_admin)
            VALUES (?, ?, ?, ?, ?, 1, 0)""",
            (user_id, req.name, req.email, req.telegram_chat_id, api_token),
        )
        await db.execute(
            """INSERT INTO user_preferences
            (user_id, players, preferred_days, earliest_time, latest_time, max_price)
            VALUES (?, ?, ?, ?, ?, ?)""",
            (user_id, 4, json.dumps(["saturday", "sunday"]), "06:00", "09:00", 150),
        )
        await db.commit()
        return {"message": "Connected!", "user_id": user_id, "api_token": api_token}
    finally:
        await db.close()


@app.get("/api/releases")
async def get_releases():
    """Get upcoming tee time release events."""
    from app.services.snipe import get_next_release_events
    events = get_next_release_events(days_ahead=21)
    clean = []
    for e in events:
        clean.append({
            "course_id": e["course_id"],
            "course_name": e["course_name"],
            "play_date": e["play_date"],
            "play_day": e["play_day"],
            "release_date": e["release_date"],
            "advance_days": e["advance_days"],
        })
    return {"releases": clean}


@app.post("/admin/discover-facility-ids")
async def discover_facility_ids(request: Request):
    await require_admin_key(request)
    """Use the stealth browser to search GolfNow and discover missing facility IDs."""
    from app.scrapers.golfnow_v2 import _get_browser, _create_stealth_context
    import re as regex

    missing = {k: v for k, v in COURSES.items()
               if v.get("platform") == "golfnow" and not v.get("golfnow_facility_id")}

    if not missing:
        return {"message": "All GolfNow courses already have facility IDs", "found": {}}

    found = {}
    errors = {}
    browser = await _get_browser()

    for course_id, course in missing.items():
        context = None
        try:
            context = await _create_stealth_context(browser)
            page = await context.new_page()

            search_name = course["name"].replace(" GC", "").replace(" CC", "").replace(" Golf Club", "").replace(" Golf Course", "")
            search_url = f"https://www.golfnow.com/tee-times/search#sortby=Recommended&lat=41.87&lng=-87.63&q={search_name}&radius=80"

            await page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(5000)

            # Extract all facility links from the page
            links = await page.evaluate("""() => {
                var anchors = document.querySelectorAll('a[href*="/facility/"]');
                var results = [];
                for (var i = 0; i < anchors.length; i++) {
                    results.push(anchors[i].href);
                }
                // Also check for data attributes
                var cards = document.querySelectorAll('[data-facilityid], [data-facility-id]');
                for (var i = 0; i < cards.length; i++) {
                    var fid = cards[i].getAttribute('data-facilityid') || cards[i].getAttribute('data-facility-id');
                    if (fid) results.push('facility-id:' + fid);
                }
                return results;
            }""")

            for link in links:
                match = regex.search(r'/facility/(\d+)-', link)
                if match:
                    fid = match.group(1)
                    # Check if this looks like the right course
                    slug = link.lower()
                    name_parts = course["name"].lower().split()
                    if any(part in slug for part in name_parts if len(part) > 3):
                        found[course_id] = {"facility_id": fid, "url": link, "name": course["name"]}
                        break

                # Check data attribute format
                if link.startswith("facility-id:"):
                    fid = link.replace("facility-id:", "")
                    found[course_id] = {"facility_id": fid, "name": course["name"]}
                    break

            if course_id not in found:
                # Try getting page text for debugging
                text = await page.evaluate("() => document.body.innerText.substring(0, 500)")
                errors[course_id] = f"No facility link found. Page text: {text[:200]}"

        except Exception as e:
            errors[course_id] = str(e)[:200]
        finally:
            if context:
                try:
                    await context.close()
                except Exception:
                    pass
            await asyncio.sleep(2)

    return {
        "message": f"Found {len(found)} facility IDs out of {len(missing)} missing courses",
        "found": found,
        "errors": errors,
        "instructions": "Update courses.py with the discovered facility IDs to enable scanning",
    }


# ===== WEATHER API (for dashboard) =====

@app.get("/api/weather")
async def get_weather(dates: str = Query("")):
    """Get weather forecasts for comma-separated dates (YYYY-MM-DD)."""
    from app.services.weather import get_forecast

    if not dates:
        return {"forecasts": {}}

    date_list = [d.strip() for d in dates.split(",") if d.strip()]
    forecasts = {}

    for date_str in date_list[:7]:  # max 7 dates
        try:
            forecast = await get_forecast(date_str)
            if forecast:
                forecasts[date_str] = forecast
        except Exception:
            pass

    return {"forecasts": forecasts}


# ===== WEB ALERTS API (browser-based tee time alerts) =====

class WebAlertCreate(BaseModel):
    session_id: str
    course_id: str
    earliest_time: str = "05:00"
    latest_time: str = "14:00"
    date_from: str | None = None
    date_to: str | None = None
    min_players: int = 1


@app.post("/api/web-alerts")
async def create_web_alert(req: WebAlertCreate):
    """Create a web-based tee time alert."""
    if not req.session_id or len(req.session_id) > 64:
        raise HTTPException(status_code=400, detail="Invalid session ID")
    if req.course_id not in COURSES:
        raise HTTPException(status_code=400, detail="Unknown course")

    db = await get_db()
    try:
        count_row = await db.execute_fetchone(
            "SELECT COUNT(*) as cnt FROM web_alerts WHERE session_id = ? AND status = 'ACTIVE'",
            (req.session_id,),
        )
        if count_row and count_row["cnt"] >= 10:
            raise HTTPException(status_code=400, detail="Maximum 10 active alerts per session")

        await db.execute(
            """INSERT INTO web_alerts
            (session_id, course_id, earliest_time, latest_time, date_from, date_to, min_players)
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (req.session_id, req.course_id, req.earliest_time, req.latest_time,
             req.date_from, req.date_to, req.min_players),
        )
        await db.commit()
        row = await db.execute_fetchone("SELECT last_insert_rowid() as id")
        alert_id = row["id"] if row else None
        course = COURSES.get(req.course_id, {})
        return {
            "id": alert_id,
            "course": course.get("name", req.course_id),
            "message": f"Alert set for {course.get('name', req.course_id)}",
        }
    finally:
        await db.close()


@app.get("/api/web-alerts/{session_id}")
async def list_web_alerts(session_id: str):
    """List active web alerts for a session."""
    db = await get_db()
    try:
        rows = await db.execute_fetchall(
            "SELECT * FROM web_alerts WHERE session_id = ? AND status = 'ACTIVE' ORDER BY created_at DESC",
            (session_id,),
        )
        alerts = []
        for r in rows:
            d = {k: r[k] for k in r.keys()}
            d["course_name"] = COURSES.get(d["course_id"], {}).get("name", d["course_id"])
            alerts.append(d)
        return {"alerts": alerts}
    finally:
        await db.close()


@app.delete("/api/web-alerts/{alert_id}")
async def delete_web_alert(alert_id: int, session_id: str = Query(...)):
    """Deactivate a web alert."""
    db = await get_db()
    try:
        row = await db.execute_fetchone(
            "SELECT * FROM web_alerts WHERE id = ? AND session_id = ?",
            (alert_id, session_id),
        )
        if not row:
            raise HTTPException(status_code=404, detail="Alert not found")
        await db.execute(
            "UPDATE web_alerts SET status = 'DELETED' WHERE id = ?",
            (alert_id,),
        )
        await db.commit()
        return {"message": "Alert removed"}
    finally:
        await db.close()


@app.get("/api/web-alerts/check/{session_id}")
async def check_web_alerts(session_id: str):
    """Poll for tee time matches against active web alerts."""
    db = await get_db()
    try:
        alerts = await db.execute_fetchall(
            "SELECT * FROM web_alerts WHERE session_id = ? AND status = 'ACTIVE'",
            (session_id,),
        )
        matches = []
        for alert in alerts:
            a = {k: alert[k] for k in alert.keys()}
            notified = json.loads(a.get("notified_slots") or "[]")

            query = """
                SELECT * FROM seen_slots
                WHERE course_id = ?
                  AND time >= ? AND time <= ?
                  AND disappeared_at IS NULL
                  AND date >= date('now')
                  AND players_available >= ?
            """
            params = [a["course_id"], a["earliest_time"], a["latest_time"], a["min_players"]]

            if a.get("date_from"):
                query += " AND date >= ?"
                params.append(a["date_from"])
            if a.get("date_to"):
                query += " AND date <= ?"
                params.append(a["date_to"])

            query += " ORDER BY date, time LIMIT 20"
            rows = await db.execute_fetchall(query, params)

            new_slots = []
            for r in rows:
                slot = {k: r[k] for k in r.keys()}
                if slot["id"] not in notified:
                    slot["course_name"] = COURSES.get(slot["course_id"], {}).get("name", slot["course_id"])
                    new_slots.append(slot)
                    notified.append(slot["id"])

            if new_slots:
                await db.execute(
                    "UPDATE web_alerts SET notified_slots = ? WHERE id = ?",
                    (json.dumps(notified[-100:]), a["id"]),
                )
                matches.append({
                    "alert_id": a["id"],
                    "course_id": a["course_id"],
                    "course_name": COURSES.get(a["course_id"], {}).get("name", a["course_id"]),
                    "slots": new_slots,
                })

        if matches:
            await db.commit()
        return {"matches": matches}
    finally:
        await db.close()


# ===== ADMIN: Clear stale slot data (run after timezone fix) =====

@app.post("/admin/clear-stale-slots")
async def clear_stale_slots(request: Request):
    await require_admin_key(request)
    """Clear all seen_slots to force fresh data after timezone fix.
    Run this once after deploying the golfnow_v2.py timezone correction.
    Then trigger a scan to repopulate with correct times."""
    db = await get_db()
    try:
        count = await db.execute_fetchone("SELECT COUNT(*) as cnt FROM seen_slots")
        cnt = count["cnt"] if count else 0
        await db.execute("DELETE FROM seen_slots")
        await db.commit()
        return {
            "message": f"Cleared {cnt} stale slots. Now trigger a scan to repopulate with correct times.",
            "cleared": cnt,
            "next_step": "POST /scan/trigger to rescan all courses",
        }
    finally:
        await db.close()
