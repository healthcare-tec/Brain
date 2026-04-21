"""
Alembic environment configuration.
Works with SQLite (default) and PostgreSQL.
"""

import os
import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import engine_from_config, pool
from alembic import context

# Add backend directory to path so app modules can be imported
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import Base
from app.models import *  # noqa: F401, F403 — ensure all models are registered

alembic_config = context.config

# ── Resolve database URL ──────────────────────────────────────────────────────
# Priority: DATABASE_URL_SYNC env var → alembic.ini → config default (SQLite)
db_url = os.getenv("DATABASE_URL_SYNC")
if not db_url:
    # Fall back to the sync URL from app config
    from app.config import settings
    db_url = settings.DATABASE_URL_SYNC

alembic_config.set_main_option("sqlalchemy.url", db_url)

if alembic_config.config_file_name is not None:
    fileConfig(alembic_config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (generates SQL without a live connection)."""
    url = alembic_config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,  # required for SQLite ALTER TABLE support
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode (applies directly to the database)."""
    connectable = engine_from_config(
        alembic_config.get_section(alembic_config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.StaticPool,  # StaticPool works for both SQLite and Postgres
        connect_args={"check_same_thread": False}
        if db_url.startswith("sqlite")
        else {},
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True,  # required for SQLite ALTER TABLE support
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
