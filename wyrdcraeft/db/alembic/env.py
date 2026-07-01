"""Alembic environment for the canonical wyrdcraeft SQLite database."""

from __future__ import annotations

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

#: Alembic configuration loaded from ``alembic.ini``.
config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

#: SQLAlchemy metadata registry for autogeneration. Phase 2 keeps this unset.
target_metadata = None


def run_migrations_offline() -> None:
    """
    Run Alembic migrations without a live database connection.

    Side Effects:
        Configures the Alembic migration context for SQL script generation.

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


def run_migrations_online() -> None:
    """
    Run Alembic migrations with a live SQLAlchemy connection.

    Side Effects:
        Opens a SQLAlchemy engine and runs the migration environment.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
