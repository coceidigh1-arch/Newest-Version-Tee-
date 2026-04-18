import aiosqlite
import logging
import secrets
from app.config import settings

logger = logging.getLogger(__name__)

DB_PATH = settings.DB_PATH

BASE_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT UNIQUE,
    telegram_chat_id TEXT,
    api_token TEXT,
    is_admin INTEGER DEFAULT 0,
    notification_enabled INTEGER DEFAULT 1,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS user_preferences (
    user_id TEXT PRIMARY KEY,
    players INTEGER DEFAULT 4,
    preferred_days TEXT DEFAULT '["saturday","sunday"]',
    earliest_time TEXT DEFAULT '05:00',
    latest_time TEXT DEFAULT '08:00',
    max_price INTEGER DEFAULT 150,
    walk_ride TEXT DEFAULT 'ride',
    max_rounds_week INTEGER DEFAULT 2,
    monthly_budget INTEGER DEFAULT 600,
    must_play_courses TEXT DEFAULT '[]',
    nice_to_have_courses TEXT DEFAULT '[]',
    deal_only_courses TEXT DEFAULT '[]',
    course_overrides TEXT DEFAULT '{}',
    alert_threshold INTEGER DEFAULT 55,
    confirm_threshold INTEGER DEFAULT 75,
    autobook_threshold INTEGER DEFAULT 90,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS user_platform_accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    platform TEXT NOT NULL,
    username_encrypted TEXT NOT NULL,
    password_encrypted TEXT NOT NULL,
    session_cookie TEXT,
    session_expires_at TEXT,
    is_active INTEGER DEFAULT 1,
    last_login_at TEXT,
    last_error TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    UNIQUE(user_id, platform),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS seen_slots (
    id TEXT PRIMARY KEY,
    course_id TEXT NOT NULL,
    date TEXT NOT NULL,
    time TEXT NOT NULL,
    players_available INTEGER,
    price REAL,
    walk_ride TEXT,
    sub_course TEXT,
    score INTEGER DEFAULT 0,
    action TEXT DEFAULT 'PENDING',
    booking_url TEXT,
    source TEXT,
    first_seen_at TEXT DEFAULT (datetime('now')),
    last_seen_at TEXT DEFAULT (datetime('now')),
    disappeared_at TEXT,
    alerted_at TEXT,
    booked_at TEXT,
    booking_confirmation TEXT,
    raw_data TEXT
);

CREATE TABLE IF NOT EXISTS slot_alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slot_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    score INTEGER DEFAULT 0,
    recommended_action TEXT NOT NULL,
    status TEXT DEFAULT 'SENT',
    response TEXT,
    telegram_message_id TEXT,
    sent_at TEXT DEFAULT (datetime('now')),
    responded_at TEXT,
    updated_at TEXT DEFAULT (datetime('now')),
    UNIQUE(slot_id, user_id),
    FOREIGN KEY (slot_id) REFERENCES seen_slots(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS search_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT DEFAULT (datetime('now')),
    course_id TEXT NOT NULL,
    platform TEXT NOT NULL,
    status TEXT NOT NULL,
    slots_found INTEGER DEFAULT 0,
    new_slots INTEGER DEFAULT 0,
    duration_ms INTEGER DEFAULT 0,
    error_message TEXT
);

CREATE TABLE IF NOT EXISTS roll_calls (
    id TEXT PRIMARY KEY,
    slot_id TEXT NOT NULL,
    initiated_by TEXT NOT NULL,
    status TEXT DEFAULT 'PENDING',
    min_players INTEGER DEFAULT 3,
    expires_at TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now')),
    completed_at TEXT,
    booking_result TEXT,
    FOREIGN KEY (slot_id) REFERENCES seen_slots(id),
    FOREIGN KEY (initiated_by) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS roll_call_responses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    roll_call_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    response TEXT NOT NULL,
    responded_at TEXT DEFAULT (datetime('now')),
    UNIQUE(roll_call_id, user_id),
    FOREIGN KEY (roll_call_id) REFERENCES roll_calls(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS bookings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slot_id TEXT NOT NULL,
    roll_call_id TEXT,
    booked_by TEXT NOT NULL,
    course_id TEXT NOT NULL,
    date TEXT NOT NULL,
    time TEXT NOT NULL,
    players INTEGER NOT NULL,
    player_names TEXT,
    total_price REAL,
    per_player_price REAL,
    platform TEXT NOT NULL,
    confirmation_code TEXT,
    status TEXT DEFAULT 'CONFIRMED',
    cancelled_at TEXT,
    cancel_result TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (slot_id) REFERENCES seen_slots(id),
    FOREIGN KEY (booked_by) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS budget_tracking (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    month TEXT NOT NULL,
    total_spent REAL DEFAULT 0,
    rounds_booked INTEGER DEFAULT 0,
    rounds_played INTEGER DEFAULT 0,
    UNIQUE(user_id, month),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS alert_suppressions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT,
    course_id TEXT,
    suppressed_until TEXT NOT NULL,
    reason TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS snipe_requests (
    rowid INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    course_id TEXT NOT NULL,
    play_date TEXT NOT NULL,
    preferred_time TEXT DEFAULT 'any',
    auto_book INTEGER DEFAULT 0,
    release_date TEXT NOT NULL,
    status TEXT DEFAULT 'PENDING',
    found_time TEXT,
    found_price REAL,
    created_at TEXT DEFAULT (datetime('now')),
    UNIQUE(user_id, course_id, play_date),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_slots_course_date ON seen_slots(course_id, date);
CREATE INDEX IF NOT EXISTS idx_slots_action ON seen_slots(action);
CREATE INDEX IF NOT EXISTS idx_slot_alerts_user_status ON slot_alerts(user_id, status, sent_at);
CREATE INDEX IF NOT EXISTS idx_slot_alerts_slot_user ON slot_alerts(slot_id, user_id);
CREATE INDEX IF NOT EXISTS idx_search_log_course ON search_log(course_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_bookings_user ON bookings(booked_by, date);
CREATE INDEX IF NOT EXISTS idx_rollcalls_status ON roll_calls(status);
CREATE INDEX IF NOT EXISTS idx_snipe_release ON snipe_requests(release_date, status);

CREATE TABLE IF NOT EXISTS web_alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    course_id TEXT NOT NULL,
    email TEXT,
    earliest_time TEXT DEFAULT '05:00',
    latest_time TEXT DEFAULT '14:00',
    date_from TEXT,
    date_to TEXT,
    min_players INTEGER DEFAULT 1,
    status TEXT DEFAULT 'ACTIVE',
    notified_slots TEXT DEFAULT '[]',
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_web_alerts_session ON web_alerts(session_id, status);
CREATE INDEX IF NOT EXISTS idx_web_alerts_course ON web_alerts(course_id, status);
"""


async def _execute_fetchone(self, sql, parameters=None):
    if parameters:
        cursor = await self.execute(sql, parameters)
    else:
        cursor = await self.execute(sql)
    return await cursor.fetchone()


aiosqlite.Connection.execute_fetchone = _execute_fetchone


async def get_db() -> aiosqlite.Connection:
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row
    await db.execute("PRAGMA journal_mode=WAL")
    await db.execute("PRAGMA foreign_keys=ON")
    return db


async def _column_exists(db: aiosqlite.Connection, table: str, column: str) -> bool:
    rows = await db.execute_fetchall(f"PRAGMA table_info({table})")
    return any(row[1] == column for row in rows)


async def _add_column_if_missing(db: aiosqlite.Connection, table: str, definition: str) -> None:
    column_name = definition.split()[0]
    if not await _column_exists(db, table, column_name):
        await db.execute(f"ALTER TABLE {table} ADD COLUMN {definition}")


async def _migration_1_add_api_token(db: aiosqlite.Connection) -> None:
    await _add_column_if_missing(db, "users", "api_token TEXT")
    rows = await db.execute_fetchall("SELECT id, api_token FROM users")
    for row in rows:
        if not row["api_token"]:
            await db.execute(
                "UPDATE users SET api_token = ?, updated_at = datetime('now') WHERE id = ?",
                (generate_api_token(), row["id"]),
            )


async def _migration_2_create_slot_alerts(db: aiosqlite.Connection) -> None:
    await db.executescript(
        """
        CREATE TABLE IF NOT EXISTS slot_alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slot_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            score INTEGER DEFAULT 0,
            recommended_action TEXT NOT NULL,
            status TEXT DEFAULT 'SENT',
            response TEXT,
            telegram_message_id TEXT,
            sent_at TEXT DEFAULT (datetime('now')),
            responded_at TEXT,
            updated_at TEXT DEFAULT (datetime('now')),
            UNIQUE(slot_id, user_id),
            FOREIGN KEY (slot_id) REFERENCES seen_slots(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        CREATE INDEX IF NOT EXISTS idx_slot_alerts_user_status ON slot_alerts(user_id, status, sent_at);
        CREATE INDEX IF NOT EXISTS idx_slot_alerts_slot_user ON slot_alerts(slot_id, user_id);
        """
    )


async def _migration_3_backfill_legacy_alerts(db: aiosqlite.Connection) -> None:
    rows = await db.execute_fetchall(
        """
        SELECT ss.id AS slot_id, u.id AS user_id, COALESCE(ss.score, 0) AS score,
               COALESCE(ss.action, 'ALERT') AS action, ss.alerted_at
        FROM seen_slots ss
        JOIN users u ON u.notification_enabled = 1
        WHERE ss.alerted_at IS NOT NULL
          AND ss.action IN ('ALERT', 'ALERTED', 'CONFIRM', 'CONFIRMED', 'AUTOBOOK')
          AND NOT EXISTS (
              SELECT 1 FROM slot_alerts sa WHERE sa.slot_id = ss.id AND sa.user_id = u.id
          )
        """
    )
    for row in rows:
        action = row["action"]
        normalized = "CONFIRM" if action == "CONFIRMED" else "ALERT" if action == "ALERTED" else action
        await db.execute(
            """
            INSERT OR IGNORE INTO slot_alerts
            (slot_id, user_id, score, recommended_action, status, sent_at, updated_at)
            VALUES (?, ?, ?, ?, 'SENT', COALESCE(?, datetime('now')), datetime('now'))
            """,
            (row["slot_id"], row["user_id"], row["score"], normalized, row["alerted_at"]),
        )


async def _migration_4_create_web_alerts(db: aiosqlite.Connection) -> None:
    await db.executescript(
        """
        CREATE TABLE IF NOT EXISTS web_alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            course_id TEXT NOT NULL,
            email TEXT,
            earliest_time TEXT DEFAULT '05:00',
            latest_time TEXT DEFAULT '14:00',
            date_from TEXT,
            date_to TEXT,
            min_players INTEGER DEFAULT 1,
            status TEXT DEFAULT 'ACTIVE',
            notified_slots TEXT DEFAULT '[]',
            created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE INDEX IF NOT EXISTS idx_web_alerts_session ON web_alerts(session_id, status);
        CREATE INDEX IF NOT EXISTS idx_web_alerts_course ON web_alerts(course_id, status);
        """
    )


async def _migration_5_create_connect_challenges(db: aiosqlite.Connection) -> None:
    await db.executescript(
        """
        CREATE TABLE IF NOT EXISTS connect_challenges (
            telegram_chat_id TEXT PRIMARY KEY,
            code_hash TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            attempts INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now'))
        );
        """
    )


MIGRATIONS = [
    _migration_1_add_api_token,
    _migration_2_create_slot_alerts,
    _migration_3_backfill_legacy_alerts,
    _migration_4_create_web_alerts,
    _migration_5_create_connect_challenges,
]


async def init_db():
    db = await get_db()
    try:
        await db.executescript(BASE_SCHEMA)
        current_version_row = await db.execute_fetchone("PRAGMA user_version")
        current_version = current_version_row[0] if current_version_row else 0

        for version, migration in enumerate(MIGRATIONS, start=1):
            if current_version < version:
                logger.info("Applying database migration %s", version)
                await migration(db)
                await db.execute(f"PRAGMA user_version = {version}")
                current_version = version

        await db.commit()
        logger.info("Database initialized at %s (schema v%s)", DB_PATH, current_version)
    finally:
        await db.close()


def generate_api_token() -> str:
    return secrets.token_urlsafe(24)
