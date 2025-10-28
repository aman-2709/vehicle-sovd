"""Alembic environment configuration for async SQLAlchemy 2.0.

This module configures Alembic to work with SQLAlchemy 2.0's async engine
using asyncpg driver for PostgreSQL. It reads the database URL from the
DATABASE_URL environment variable and supports both offline (SQL generation)
and online (database execution) migration modes.

Environment Variables:
    DATABASE_URL: PostgreSQL connection string in format:
                  postgresql+asyncpg://user:pass@host:port/database

Usage:
    alembic upgrade head    # Run migrations
    alembic downgrade base  # Rollback all migrations
    alembic revision -m "description"  # Create new migration
"""

import asyncio
import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Override sqlalchemy.url with environment variable if present
# This allows the database URL to be configured via environment variables
# instead of hardcoding it in alembic.ini
database_url = os.getenv("DATABASE_URL")
if database_url:
    config.set_main_option("sqlalchemy.url", database_url)

# Add your model's MetaData object here for 'autogenerate' support
# Import all models to ensure they are registered with Base.metadata
from app.models import Base

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL and not an Engine, though an
    Engine is acceptable here as well. By skipping the Engine creation we don't
    even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the script output.

    This mode is useful for generating SQL scripts without connecting to the
    database, which can be executed manually later.
    """
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
    """Execute migrations using the provided connection.

    This is called by run_sync() from the async connection, allowing us to use
    Alembic's synchronous API within an async context.

    Args:
        connection: SQLAlchemy connection object (will be synchronous when
                   called via run_sync)
    """
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations in 'online' mode using async engine.

    In this scenario we need to create an async Engine and acquire a connection
    from it. We then use run_sync() to execute the migrations within a
    synchronous context, as Alembic's migration API is synchronous.

    This is the recommended pattern for SQLAlchemy 2.0 async applications.
    """
    # Create async engine from configuration
    # NullPool is used to avoid connection pooling during migrations
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    # Use async context manager to acquire connection
    async with connectable.connect() as connection:
        # Run migrations in sync context using run_sync
        await connection.run_sync(do_run_migrations)

    # Dispose of the engine to close all connections
    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    This is the entry point for online migrations. It creates an event loop
    (if needed) and runs the async migration function.
    """
    # Get or create event loop and run async migrations
    asyncio.run(run_async_migrations())


# Determine which mode to use based on context
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
