import asyncio
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.health import router as health_router
from backend.api.research import router as research_router
from backend.config import get_settings
from backend.database.session import init_db
from backend.services.recovery import recovery_service

app = FastAPI(title="ARGUS Backend", version="0.1.0")
settings = get_settings()
allowed_origins = [origin.strip() for origin in settings.cors_allowed_origins.split(",") if origin.strip()]
logger = logging.getLogger(__name__)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=r"https://.*\.(vercel\.app|up\.railway\.app)",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        init_db()
        return

    if settings.argus_production_safe_mode:
        loop.create_task(_production_safe_startup())
        return

    init_db()
    loop.create_task(_recover_safely())


async def _production_safe_startup() -> None:
    """Keep Render health checks fast by moving startup DB work off the critical path."""

    try:
        await asyncio.to_thread(init_db)
    except Exception:
        logger.exception("production_safe_init_db_failed")


async def _recover_safely() -> None:
    try:
        await recovery_service.recover()
    except Exception:
        logger.exception("startup_recovery_failed")


app.include_router(health_router, prefix="/api")
app.include_router(research_router, prefix="/api")
