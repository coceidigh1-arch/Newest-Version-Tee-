"""
Tee Time Bot — Main Entry Point
Starts the FastAPI server and, optionally, the APScheduler worker loop.
"""

import logging
import uvicorn

from app.api.routes import app
from app.api.onboarding import *  # registers /join and /invite routes
from app.api.dashboard import router as dashboard_router
app.include_router(dashboard_router)
from app.services.telegram_handler import *  # registers /telegram/webhook route
from app.models.database import init_db
from app.services.scheduler import start_scheduler, stop_scheduler
from app.config import settings

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


@app.on_event("startup")
async def on_startup():
    await init_db()
    logger.info("Database initialized")
    if settings.ENABLE_SCHEDULER:
        await start_scheduler()
    else:
        logger.info("Scheduler disabled for this process (ENABLE_SCHEDULER=false)")


@app.on_event("shutdown")
async def on_shutdown():
    await stop_scheduler()


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=False,
        log_level=settings.LOG_LEVEL.lower(),
    )
