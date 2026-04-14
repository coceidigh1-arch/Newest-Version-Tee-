import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.config import settings
from app.models.database import get_db
from app.services.notifications import send_message, format_daily_digest
from app.services.snipe import run_snipe_scan, send_weekly_snipe_menu, send_release_headsup
from app.services.scanner import run_scan_cycle

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


def configure_scheduler() -> AsyncIOScheduler:
    if scheduler.get_jobs():
        return scheduler

    scheduler.add_job(
        run_scan_cycle,
        IntervalTrigger(minutes=settings.SCAN_INTERVAL_STANDARD),
        id="standard_scan",
        name="Standard tee time scan",
        replace_existing=True,
    )
    scheduler.add_job(
        run_scan_cycle,
        CronTrigger(hour="5-6", minute="*/5", timezone="America/Chicago"),
        id="morning_scan",
        name="Morning boost scan",
        replace_existing=True,
    )
    scheduler.add_job(
        run_scan_cycle,
        CronTrigger(hour="20-22", minute="*/10", timezone="America/Chicago"),
        id="evening_scan",
        name="Evening scan",
        replace_existing=True,
    )
    scheduler.add_job(
        send_daily_digest,
        CronTrigger(hour=21, minute=0, timezone="America/Chicago"),
        id="daily_digest",
        name="Daily digest",
        replace_existing=True,
    )
    scheduler.add_job(
        expire_stale_rollcalls,
        IntervalTrigger(minutes=5),
        id="expire_rollcalls",
        name="Expire stale roll calls",
        replace_existing=True,
    )
    scheduler.add_job(
        mark_disappeared_slots,
        IntervalTrigger(minutes=30),
        id="mark_disappeared",
        name="Mark disappeared slots",
        replace_existing=True,
    )
    scheduler.add_job(
        run_snipe_scan,
        CronTrigger(hour="23", minute="55-59", second="*/30", timezone="America/Chicago"),
        id="snipe_late",
        name="Snipe scan (pre-midnight)",
        replace_existing=True,
    )
    scheduler.add_job(
        run_snipe_scan,
        CronTrigger(hour="0", minute="0-15", second="*/30", timezone="America/Chicago"),
        id="snipe_midnight",
        name="Snipe scan (post-midnight)",
        replace_existing=True,
    )
    scheduler.add_job(
        run_snipe_scan,
        CronTrigger(hour="5-6", minute="*/2", timezone="America/Chicago"),
        id="snipe_morning",
        name="Snipe scan (early morning)",
        replace_existing=True,
    )
    scheduler.add_job(
        send_weekly_snipe_menu,
        CronTrigger(day_of_week="sun", hour=18, minute=0, timezone="America/Chicago"),
        id="weekly_snipe_menu",
        name="Weekly snipe menu",
        replace_existing=True,
    )
    scheduler.add_job(
        send_release_headsup,
        CronTrigger(hour=20, minute=0, timezone="America/Chicago"),
        id="release_headsup",
        name="Release heads-up alert",
        replace_existing=True,
    )
    return scheduler


async def start_scheduler() -> AsyncIOScheduler:
    configure_scheduler()
    if not scheduler.running:
        scheduler.start()
        logger.info("Scheduler started with %d jobs", len(scheduler.get_jobs()))
        for job in scheduler.get_jobs():
            logger.info("  Job: %s [%s]", job.name, job.trigger)
    return scheduler


async def stop_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler shut down")


async def send_daily_digest():
    db = await get_db()
    try:
        admins = await db.execute_fetchall(
            "SELECT * FROM users WHERE is_admin = 1 AND telegram_chat_id IS NOT NULL"
        )
        stats = await db.execute_fetchone(
            """SELECT COUNT(*) as scans, SUM(slots_found) as slots_found, SUM(new_slots) as new_slots
               FROM search_log WHERE timestamp > datetime('now', '-24 hours')"""
        )
        alerts = await db.execute_fetchone(
            "SELECT COUNT(*) as cnt FROM slot_alerts WHERE sent_at > datetime('now', '-24 hours')"
        )
        bookings = await db.execute_fetchone(
            """SELECT COUNT(*) as cnt, SUM(total_price) as total
               FROM bookings WHERE created_at > datetime('now', '-24 hours')"""
        )
        digest_stats = {
            "scans": stats["scans"] if stats else 0,
            "slots_found": stats["slots_found"] if stats and stats["slots_found"] else 0,
            "alerts_sent": alerts["cnt"] if alerts else 0,
            "bookings": bookings["cnt"] if bookings else 0,
            "monthly_spend": bookings["total"] if bookings and bookings["total"] else 0,
            "weekly_rounds": 0,
        }
        msg = format_daily_digest(digest_stats)
        for admin in admins:
            await send_message(admin["telegram_chat_id"], msg)
    finally:
        await db.close()


async def expire_stale_rollcalls():
    db = await get_db()
    try:
        await db.execute(
            "UPDATE roll_calls SET status = 'EXPIRED', completed_at = datetime('now') WHERE status = 'PENDING' AND expires_at < datetime('now')"
        )
        await db.commit()
    finally:
        await db.close()


async def mark_disappeared_slots():
    db = await get_db()
    try:
        await db.execute(
            """UPDATE seen_slots SET disappeared_at = datetime('now')
               WHERE disappeared_at IS NULL
                 AND last_seen_at < datetime('now', ?)
                 AND date <= date('now')
                 AND action NOT IN ('BOOKED', 'CONFIRMED')""",
            (f"-{settings.SLOT_STALE_MINUTES} minutes",),
        )
        await db.commit()
    finally:
        await db.close()
