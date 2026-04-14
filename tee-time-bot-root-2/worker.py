"""Scheduler-only worker process for scans and notifications."""

import asyncio
import logging

from app.config import settings
from app.models.database import init_db
from app.services.scheduler import start_scheduler, stop_scheduler

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


async def main():
    await init_db()
    await start_scheduler()
    logger.info("Worker running. Press Ctrl+C to stop.")
    try:
        while True:
            await asyncio.sleep(3600)
    finally:
        await stop_scheduler()


if __name__ == "__main__":
    asyncio.run(main())
