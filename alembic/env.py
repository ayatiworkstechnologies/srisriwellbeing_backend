import asyncio
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config


# =========================================================
# PROJECT ROOT
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(PROJECT_ROOT),
    )


# =========================================================
# APPLICATION IMPORTS
# =========================================================

from app.core.config import settings  # noqa: E402
from app.models.base import Base  # noqa: E402

# Import all existing models so Alembic can discover them.
import app.models.model_registry  # noqa: F401, E402

# Appointment and patient-booking models live outside model_registry.
import app.modules.appointments.model  # noqa: F401, E402
import app.modules.patient_bookings.model  # noqa: F401, E402


# =========================================================
# ALEMBIC CONFIGURATION
# =========================================================

config = context.config

config.set_main_option(
    "sqlalchemy.url",
    settings.DATABASE_URL,
)


# Configure Python logging using alembic.ini
if config.config_file_name is not None:
    fileConfig(
        config.config_file_name,
    )


# SQLAlchemy metadata used by Alembic autogenerate.
target_metadata = Base.metadata


# =========================================================
# OFFLINE MIGRATIONS
# =========================================================

def run_migrations_offline() -> None:
    """
    Run migrations without creating a database connection.
    """

    url = config.get_main_option(
        "sqlalchemy.url"
    )

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
        compare_server_default=False,
        dialect_opts={
            "paramstyle": "named",
        },
    )

    with context.begin_transaction():
        context.run_migrations()


# =========================================================
# SYNCHRONOUS MIGRATION CALLBACK
# =========================================================

def do_run_migrations(connection) -> None:
    """
    Run Alembic migrations using the synchronous connection
    provided by SQLAlchemy's async engine.
    """

    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=False,
    )

    with context.begin_transaction():
        context.run_migrations()


# =========================================================
# ONLINE MIGRATIONS
# =========================================================

async def run_migrations_online() -> None:
    """
    Run migrations using an asynchronous SQLAlchemy engine.
    """

    connectable = async_engine_from_config(
        config.get_section(
            config.config_ini_section,
        )
        or {},
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    try:
        async with connectable.connect() as connection:
            await connection.run_sync(
                do_run_migrations
            )

    finally:
        await connectable.dispose()


# =========================================================
# START MIGRATION
# =========================================================

if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(
        run_migrations_online()
    )
