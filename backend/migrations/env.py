"""Entorno de Alembic: toma la URL de la configuración de la aplicación."""
from alembic import context
from sqlalchemy import create_engine

from prosta_ai.config import get_settings
from prosta_ai.db import Base
import prosta_ai.models  # noqa: F401  (registra las tablas)

config = context.config
target_metadata = Base.metadata


def _url() -> str:
    # Permite sobrescribir con -x url=... o con alembic.config.set_main_option
    return (
        context.get_x_argument(as_dictionary=True).get("url")
        or config.get_main_option("sqlalchemy.url")
        or get_settings().database_url
    )


def run_migrations_offline() -> None:
    context.configure(url=_url(), target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    engine = create_engine(_url())
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
