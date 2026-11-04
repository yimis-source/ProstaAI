"""Motor de base de datos y sesiones."""
from datetime import datetime, timezone

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class Base(DeclarativeBase):
    pass


def ahora() -> datetime:
    return datetime.now(timezone.utc)


def create_db_engine(url: str) -> Engine:
    """Crea el motor; en SQLite (pruebas) activa las llaves foráneas."""
    if url.startswith("sqlite"):
        engine = create_engine(url, connect_args={"check_same_thread": False})

        @event.listens_for(engine, "connect")
        def _activar_fk(dbapi_conn, _):  # pragma: no cover - callback de conexión
            dbapi_conn.execute("PRAGMA foreign_keys=ON")

        return engine
    return create_engine(url, pool_pre_ping=True)


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, expire_on_commit=False)
