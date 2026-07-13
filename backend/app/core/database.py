"""Database engine and session management."""

from collections.abc import Generator

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings

settings = get_settings()

_is_sqlite = settings.database_url.startswith("sqlite")
_engine_kwargs: dict = {
    "pool_pre_ping": not _is_sqlite,
    "echo": settings.app_debug and settings.app_env == "development",
}
if _is_sqlite:
    _engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    _engine_kwargs["pool_size"] = 20
    _engine_kwargs["max_overflow"] = 40

engine = create_engine(settings.database_url, **_engine_kwargs)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_vector_extension(connection) -> None:
    """Ensure pgvector is available when using PostgreSQL."""
    if "postgresql" in settings.database_url:
        try:
            connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            connection.commit()
        except Exception:
            connection.rollback()


@event.listens_for(engine, "connect")
def _on_connect(dbapi_conn, connection_record):  # noqa: ARG001
    pass
