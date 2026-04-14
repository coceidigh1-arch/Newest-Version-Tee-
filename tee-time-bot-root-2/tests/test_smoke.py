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


if __name__ == "__main__":
    unittest.main()
