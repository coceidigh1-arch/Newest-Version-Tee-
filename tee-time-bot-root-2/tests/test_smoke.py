import os
import tempfile
import unittest
from unittest.mock import AsyncMock, patch

os.environ.setdefault("ENCRYPTION_KEY", "9Nf7PYWwEJsyS7Nn8L8qOHEWmNPI8v5q4tTH-LgN4mg=")

from app.config import settings
import app.models.database as db_module
from app.models.database import init_db, get_db
from app.api.routes import app
from app.services.scanner import _process_slots
from app.services.telegram_handler import _handle_skip
from httpx import ASGITransport, AsyncClient


class TeeTimeBotSmokeTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        settings.DB_PATH = os.path.join(self.tmpdir.name, "test.db")
        db_module.DB_PATH = settings.DB_PATH
        await init_db()

    async def asyncTearDown(self):
        self.tmpdir.cleanup()

    async def test_connect_creates_preferences_and_token(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/connect",
                json={"name": "Cathal", "telegram_chat_id": "12345", "email": "c@example.com"},
            )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["api_token"])
        db = await get_db()
        try:
            user = await db.execute_fetchone("SELECT * FROM users WHERE id = ?", (payload["user_id"],))
            prefs = await db.execute_fetchone("SELECT * FROM user_preferences WHERE user_id = ?", (payload["user_id"],))
        finally:
            await db.close()
        self.assertIsNotNone(user)
        self.assertIsNotNone(prefs)

    async def test_scanner_records_per_user_alerts(self):
        db = await get_db()
        try:
            await db.execute("INSERT INTO users (id, name, telegram_chat_id, api_token) VALUES ('u1', 'A', '100', 'tok1')")
            await db.execute("INSERT INTO users (id, name, telegram_chat_id, api_token) VALUES ('u2', 'B', '200', 'tok2')")
            await db.execute("INSERT INTO user_preferences (user_id, must_play_courses) VALUES ('u1', '[]')")
            await db.execute("INSERT INTO user_preferences (user_id, must_play_courses) VALUES ('u2', '[]')")
            await db.commit()

            slot = {
                "course_id": "bolingbrook",
                "date": "2026-04-18",
                "time": "07:00",
                "players_available": 4,
                "price": 90,
                "walk_ride": "ride",
                "booking_url": "https://example.com",
                "source": "test",
            }
            users = [
                {"id": "u1", "telegram_chat_id": "100"},
                {"id": "u2", "telegram_chat_id": "200"},
            ]
            prefs_by_user = {
                "u1": {"players": 4, "preferred_days": '["saturday"]', "earliest_time": "06:00", "latest_time": "08:00", "max_price": 150, "walk_ride": "ride"},
                "u2": {"players": 4, "preferred_days": '["saturday"]', "earliest_time": "06:00", "latest_time": "08:00", "max_price": 150, "walk_ride": "ride"},
            }
            with patch("app.services.scanner.send_alert", new=AsyncMock(return_value={"ok": True, "result": {"message_id": 11}})):
                await _process_slots(db, [slot], users, prefs_by_user, [])
                await db.commit()
            alerts = await db.execute_fetchall("SELECT * FROM slot_alerts ORDER BY user_id")
        finally:
            await db.close()
        self.assertEqual(len(alerts), 2)
        self.assertEqual(alerts[0]["user_id"], "u1")
        self.assertEqual(alerts[1]["user_id"], "u2")

    async def test_skip_updates_only_calling_users_alert(self):
        db = await get_db()
        try:
            await db.execute("INSERT INTO users (id, name, telegram_chat_id, api_token) VALUES ('u1', 'A', '100', 'tok1')")
            await db.execute("INSERT INTO users (id, name, telegram_chat_id, api_token) VALUES ('u2', 'B', '200', 'tok2')")
            await db.execute("INSERT INTO seen_slots (id, course_id, date, time, alerted_at) VALUES ('slot1', 'bolingbrook', '2026-04-18', '07:00', datetime('now'))")
            await db.execute("INSERT INTO slot_alerts (slot_id, user_id, score, recommended_action, status, sent_at) VALUES ('slot1', 'u1', 80, 'ALERT', 'SENT', datetime('now'))")
            await db.execute("INSERT INTO slot_alerts (slot_id, user_id, score, recommended_action, status, sent_at) VALUES ('slot1', 'u2', 80, 'ALERT', 'SENT', datetime('now'))")
            await db.commit()
            with patch("app.services.telegram_handler.send_message", new=AsyncMock(return_value=True)):
                await _handle_skip(db, {"id": "u1"}, "100", slot_id="slot1")
            first = await db.execute_fetchone("SELECT status FROM slot_alerts WHERE slot_id = 'slot1' AND user_id = 'u1'")
            second = await db.execute_fetchone("SELECT status FROM slot_alerts WHERE slot_id = 'slot1' AND user_id = 'u2'")
        finally:
            await db.close()
        self.assertEqual(first["status"], "SKIPPED")
        self.assertEqual(second["status"], "SENT")

    async def test_webhook_secret_validation(self):
        settings.TELEGRAM_WEBHOOK_SECRET = "secret123"
        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post("/telegram/webhook", json={"message": {"text": "HELP", "chat": {"id": 1}}})
            self.assertEqual(response.status_code, 401)
        finally:
            settings.TELEGRAM_WEBHOOK_SECRET = ""

    async def test_course_week_returns_seven_grouped_days(self):
        """The /api/course/{id}/week endpoint returns every day in the window even when
        some days have no availability, with slots sorted chronologically within each day."""
        from datetime import datetime, timedelta
        try:
            from zoneinfo import ZoneInfo
            tz = ZoneInfo("America/Chicago")
        except Exception:
            import pytz
            tz = pytz.timezone("America/Chicago")
        today = datetime.now(tz).date()
        d0 = today.strftime("%Y-%m-%d")
        d2 = (today + timedelta(days=2)).strftime("%Y-%m-%d")
        d6 = (today + timedelta(days=6)).strftime("%Y-%m-%d")
        d9 = (today + timedelta(days=9)).strftime("%Y-%m-%d")  # outside 7-day window

        db = await get_db()
        try:
            # Two slots on d0 (unsorted), one on d2, one on d6, one outside window.
            await db.execute(
                "INSERT INTO seen_slots (id, course_id, date, time, price, booking_url) "
                "VALUES ('s1', 'bolingbrook', ?, '09:30', 95, 'https://book/1')",
                (d0,),
            )
            await db.execute(
                "INSERT INTO seen_slots (id, course_id, date, time, price, booking_url) "
                "VALUES ('s2', 'bolingbrook', ?, '07:00', 85, 'https://book/2')",
                (d0,),
            )
            await db.execute(
                "INSERT INTO seen_slots (id, course_id, date, time, price, booking_url) "
                "VALUES ('s3', 'bolingbrook', ?, '08:15', 90, 'https://book/3')",
                (d2,),
            )
            await db.execute(
                "INSERT INTO seen_slots (id, course_id, date, time, price, booking_url) "
                "VALUES ('s4', 'bolingbrook', ?, '12:00', 60, 'https://book/4')",
                (d6,),
            )
            await db.execute(
                "INSERT INTO seen_slots (id, course_id, date, time, price, booking_url) "
                "VALUES ('s5', 'bolingbrook', ?, '07:00', 95, 'https://book/5')",
                (d9,),
            )
            # Disappeared slot on d0 — should NOT appear
            await db.execute(
                "INSERT INTO seen_slots (id, course_id, date, time, price, booking_url, disappeared_at) "
                "VALUES ('s6', 'bolingbrook', ?, '06:00', 70, 'https://book/6', datetime('now'))",
                (d0,),
            )
            await db.commit()
        finally:
            await db.close()

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/course/bolingbrook/week?days=7")

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["course_id"], "bolingbrook")
        self.assertEqual(body["timezone"], "America/Chicago")
        self.assertEqual(len(body["days"]), 7)
        self.assertEqual(body["start_date"], d0)

        by_date = {day["date"]: day for day in body["days"]}
        # d0: two slots, sorted earliest-to-latest, disappeared slot excluded
        self.assertEqual([s["time"] for s in by_date[d0]["slots"]], ["07:00", "09:30"])
        self.assertEqual(by_date[d0]["slot_count"], 2)
        # d2 and d6: one slot each
        self.assertEqual(by_date[d2]["slot_count"], 1)
        self.assertEqual(by_date[d6]["slot_count"], 1)
        # Other days: empty placeholders present
        d1 = (today + timedelta(days=1)).strftime("%Y-%m-%d")
        self.assertIn(d1, by_date)
        self.assertEqual(by_date[d1]["slots"], [])
        self.assertEqual(by_date[d1]["slot_count"], 0)
        # d9 is outside the 7-day window, must not appear
        self.assertNotIn(d9, by_date)
        self.assertEqual(body["total_slots"], 4)
        # Every returned slot keeps its booking URL
        for day in body["days"]:
            for slot in day["slots"]:
                self.assertTrue(slot.get("booking_url", "").startswith("https://book/"))

    async def test_course_week_unknown_course_returns_404(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/course/not-a-real-course/week")
        self.assertEqual(response.status_code, 404)

    async def test_dashboard_page_renders(self):
        """Sanity check: /dashboard returns a complete HTML page with the key shell
        elements. Guards against the single-string template regressing in obvious ways."""
        from app.api.dashboard import router as dashboard_router
        # Only mount once — subsequent includes are idempotent for this router.
        if not any(getattr(r, "path", None) == "/dashboard" for r in app.router.routes):
            app.include_router(dashboard_router)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/dashboard")
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/html", response.headers["content-type"])
        body = response.text
        self.assertIn("<!DOCTYPE html>", body)
        self.assertIn("Tee Time Bot", body)
        self.assertIn("id=\"app\"", body)
        # Dark theme + core JS entry points
        self.assertIn("--bg:#0a0d0c", body)
        self.assertIn("function rNow", body)
        self.assertIn("fetchCourseSlots", body)

    async def test_dispatcher_returns_unsupported_for_ezlinks(self):
        """Before this change, ezlinks/teeitup/whoosh/proshop_teetimes/cps_golf/golfback
        courses fell through the scanner's per-platform loops and silently returned
        nothing. The new dispatcher reports UNSUPPORTED so the UI can show it."""
        from app.services.scrape_dispatch import dispatch_scan, ScanStatus
        # bridges_poplar is platform=ezlinks, which has no scraper
        slots, status, err = await dispatch_scan("bridges_poplar", "2026-04-20")
        self.assertEqual(slots, [])
        self.assertEqual(status, ScanStatus.UNSUPPORTED)
        self.assertIn("ezlinks", err)

    async def test_dispatcher_unknown_course_is_config_missing(self):
        from app.services.scrape_dispatch import dispatch_scan, ScanStatus
        slots, status, err = await dispatch_scan("not-a-course", "2026-04-20")
        self.assertEqual(status, ScanStatus.CONFIG_MISSING)

    async def test_dispatcher_returns_ok_when_scraper_returns_slots(self):
        """Path-level test: the dispatcher should pass through slots and mark
        the scan OK when the scraper returns results."""
        from app.services.scrape_dispatch import dispatch_scan, ScanStatus
        fake_slots = [{"course_id": "bolingbrook", "date": "2026-04-20", "time": "07:00"}]
        with patch("app.services.scrape_dispatch.search_golfnow_facility",
                   new=AsyncMock(return_value=fake_slots)):
            slots, status, err = await dispatch_scan("bolingbrook", "2026-04-20")
        self.assertEqual(status, ScanStatus.OK)
        self.assertEqual(slots, fake_slots)
        self.assertIsNone(err)

    async def test_dispatcher_converts_scraper_exception_to_error(self):
        """When a scraper raises, the dispatcher must catch it and report
        ERROR — not propagate and crash the scan cycle."""
        from app.services.scrape_dispatch import dispatch_scan, ScanStatus
        with patch("app.services.scrape_dispatch.search_golfnow_facility",
                   new=AsyncMock(side_effect=RuntimeError("boom"))):
            slots, status, err = await dispatch_scan("bolingbrook", "2026-04-20")
        self.assertEqual(status, ScanStatus.ERROR)
        self.assertEqual(slots, [])
        self.assertIn("boom", err)

    async def test_course_week_surfaces_scan_status_per_day(self):
        """The /api/course/{id}/week endpoint must distinguish a day with no
        availability from a day where the scanner failed. Previously both
        looked identical to the UI."""
        from datetime import datetime, timedelta
        try:
            from zoneinfo import ZoneInfo
            tz = ZoneInfo("America/Chicago")
        except Exception:
            import pytz
            tz = pytz.timezone("America/Chicago")
        today = datetime.now(tz).date()
        d0 = today.strftime("%Y-%m-%d")
        d1 = (today + timedelta(days=1)).strftime("%Y-%m-%d")
        d2 = (today + timedelta(days=2)).strftime("%Y-%m-%d")

        db = await get_db()
        try:
            await db.execute(
                "INSERT INTO seen_slots (id, course_id, date, time, price, booking_url) "
                "VALUES ('s1', 'bridges_poplar', ?, '07:00', 55, 'https://x/1')",
                (d0,),
            )
            # d0: had a successful scan
            await db.execute(
                "INSERT INTO search_log (course_id, platform, status, slots_found, new_slots, duration_ms, search_date) "
                "VALUES ('bridges_poplar', 'ezlinks', 'ok', 1, 1, 800, ?)",
                (d0,),
            )
            # d1: unsupported platform (no scan possible)
            await db.execute(
                "INSERT INTO search_log (course_id, platform, status, slots_found, new_slots, duration_ms, search_date, error_message) "
                "VALUES ('bridges_poplar', 'ezlinks', 'unsupported', 0, 0, 0, ?, 'no scraper')",
                (d1,),
            )
            # d2: scanner errored
            await db.execute(
                "INSERT INTO search_log (course_id, platform, status, slots_found, new_slots, duration_ms, search_date, error_message) "
                "VALUES ('bridges_poplar', 'ezlinks', 'error', 0, 0, 500, ?, 'timeout')",
                (d2,),
            )
            await db.commit()
        finally:
            await db.close()

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/course/bridges_poplar/week")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        by_date = {d["date"]: d for d in body["days"]}
        self.assertEqual(by_date[d0]["scan_status"], "ok")
        self.assertEqual(by_date[d0]["slot_count"], 1)
        self.assertEqual(by_date[d1]["scan_status"], "unsupported")
        self.assertEqual(by_date[d1]["scan_error"], "no scraper")
        self.assertEqual(by_date[d2]["scan_status"], "error")
        # course_platform is surfaced so the UI can say "ezlinks isn't supported"
        self.assertEqual(body["course_platform"], "ezlinks")

    async def test_course_week_rejects_out_of_range_days(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            r0 = await client.get("/api/course/bolingbrook/week?days=0")
            r15 = await client.get("/api/course/bolingbrook/week?days=15")
        self.assertEqual(r0.status_code, 400)
        self.assertEqual(r15.status_code, 400)


if __name__ == "__main__":
    unittest.main()
