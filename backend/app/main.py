"""
Charlie — Cognitive Operating System
Main FastAPI application.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import engine, Base
from app.api import api_router

logger = logging.getLogger(__name__)


def _run_migrations() -> None:
    """
    Run Alembic migrations synchronously at startup.

    Handles three scenarios gracefully:

    1. Fresh DB (no tables at all)
       → Run all migrations from scratch (001 → 002 → … → head)

    2. Stale DB (core tables exist, but no alembic_version table)
       → Create any missing tables via create_all (adds task_events, notes, etc.)
       → Stamp as 001_initial (tells Alembic the base schema is in place)
       → Upgrade to head (applies 002, 003, … to add new columns)

    3. Partially migrated DB (alembic_version exists)
       → Upgrade to head (idempotent — only applies missing migrations)

    Falls back to SQLAlchemy create_all if Alembic is unavailable.
    """
    from pathlib import Path

    _backend_dir = Path(__file__).resolve().parent.parent
    alembic_ini  = _backend_dir / "alembic.ini"

    if not alembic_ini.exists():
        logger.warning("alembic.ini not found — skipping migrations")
        return

    try:
        from alembic.config import Config
        from alembic import command
        from sqlalchemy import create_engine, inspect

        alembic_cfg = Config(str(alembic_ini))
        alembic_cfg.set_main_option("script_location", str(_backend_dir / "alembic"))
        alembic_cfg.set_main_option("sqlalchemy.url", settings.DATABASE_URL_SYNC)

        connect_args = (
            {"check_same_thread": False}
            if settings.DATABASE_URL_SYNC.startswith("sqlite")
            else {}
        )
        sync_engine = create_engine(
            settings.DATABASE_URL_SYNC, connect_args=connect_args
        )

        with sync_engine.connect() as _conn:
            inspector = inspect(sync_engine)
            existing_tables     = set(inspector.get_table_names())
            has_alembic_version = "alembic_version" in existing_tables
            has_tasks_table     = "tasks" in existing_tables

        if has_tasks_table and not has_alembic_version:
            # Stale DB: core tables exist but Alembic has never run.
            # First, create any tables that are missing (e.g. task_events,
            # notes, decision_logs) using SQLAlchemy's create_all — this is
            # safe because create_all skips tables that already exist.
            logger.info(
                "Stale DB detected — creating missing tables via create_all…"
            )
            Base.metadata.create_all(sync_engine)

            # Now stamp as 001_initial so Alembic knows the base is in place.
            logger.info("Stamping stale DB as 001_initial…")
            command.stamp(alembic_cfg, "001_initial")

        sync_engine.dispose()

        # Upgrade to head — applies any migrations newer than the current stamp.
        logger.info("Running Alembic upgrade to head…")
        command.upgrade(alembic_cfg, "head")
        logger.info("Migrations complete.")

    except Exception as exc:
        logger.error(
            "Alembic migration failed (%s) — falling back to create_all", exc
        )
        import asyncio

        async def _create_all() -> None:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

        try:
            asyncio.run(_create_all())
        except RuntimeError:
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                pool.submit(asyncio.run, _create_all()).result()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run migrations and set up the database on startup."""
    _run_migrations()
    yield
    await engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "Charlie is a personal Cognitive Operating System. "
        "It captures inputs, organizes execution (GTD), structures knowledge "
        "(Second Brain / PARA), supports deep thinking (System 2), "
        "and amplifies cognition using AI."
    ),
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all API routers
app.include_router(api_router)


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "system": "Charlie", "version": settings.APP_VERSION}
