from collections.abc import Generator
from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.db.base import Base


def _engine_kwargs() -> dict:
    if settings.DATABASE_URL.startswith("sqlite"):
        return {"connect_args": {"check_same_thread": False}}
    return {}


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    return create_engine(
        settings.DATABASE_URL,
        echo=settings.DB_ECHO,
        **_engine_kwargs(),
    )


@lru_cache(maxsize=1)
def get_session_factory() -> sessionmaker[Session]:
    return sessionmaker(
        bind=get_engine(),
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )


def get_db() -> Generator[Session, None, None]:
    session = get_session_factory()()
    try:
        yield session
    finally:
        session.close()


def init_db() -> None:
    from app.models import chat, document, task  # noqa: F401

    Base.metadata.create_all(bind=get_engine())
