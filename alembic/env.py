"""Alembic environment for Vault migrations."""

from __future__ import annotations

from logging.config import fileConfig

from alembic.config import Config
from sqlalchemy import engine_from_config, pool
from sqlalchemy.engine import Connection

from alembic import context
from vault.config import load_settings
from vault.database import Base

target_metadata = Base.metadata


def get_database_url() -> str:
    """Return Vault's configured database URL for Alembic."""
    return load_settings().database_url


def _configure_database_url(config: Config) -> None:
    config.set_main_option("sqlalchemy.url", get_database_url())


def run_migrations_offline(config: Config) -> None:
    """Run migrations without creating an Engine."""
    _configure_database_url(config)
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online(config: Config) -> None:
    """Run migrations using an Engine created only when Alembic runs."""
    _configure_database_url(config)
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        _run_migrations_with_connection(connection)


def _run_migrations_with_connection(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


def _run_alembic_environment() -> None:
    config = context.config

    if config.config_file_name is not None:
        fileConfig(config.config_file_name)

    if context.is_offline_mode():
        run_migrations_offline(config)
    else:
        run_migrations_online(config)


if hasattr(context, "config"):
    _run_alembic_environment()
