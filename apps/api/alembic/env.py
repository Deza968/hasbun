"""Alembic async para PostgreSQL usando asyncpg.

Lee DATABASE_URL de la variable de entorno (configuración central).
"""

from __future__ import annotations

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from app.core.config import settings
from app.database.base import Base

# Importar todos los modelos para que Alembic los detecte
import app.modules.users.domain.models  # noqa: F401
import app.modules.roles.domain.models  # noqa: F401
import app.modules.permissions.domain.models  # noqa: F401
import app.modules.audit.domain.models  # noqa: F401
import app.modules.exchange_rates.domain.models  # noqa: F401
import app.modules.files.domain.models  # noqa: F401
import app.modules.brands.domain.models  # noqa: F401
import app.modules.categories.domain.models  # noqa: F401
import app.modules.attributes.domain.models  # noqa: F401
import app.modules.products.domain.models  # noqa: F401

config = context.config
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Corre migraciones en modo offline (SQL puro, sin conexión)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Corre migraciones en modo online usando engine async."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    """Runs migrations in 'online' mode."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()