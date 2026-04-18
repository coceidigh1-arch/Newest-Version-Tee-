"""
Tee Time Bot — Main Entry Point
Starts the FastAPI server; lifespan in app.api.routes handles DB init and the scheduler.
"""

import logging
import uvicorn

from app.api.routes import app
from app.api.onboarding import *  # registers /join and /invite routes
from app.api.dashboard import router as dashboard_router
app.include_router(dashboard_router)
from app.services.telegram_handler import *  # registers /telegram/webhook route
from app.config import settings

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=False,
        log_level=settings.LOG_LEVEL.lower(),
    )
