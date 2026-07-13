from collections.abc import Generator
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import NullPool

from app.core.config import get_settings

_SQLITE_DEFAULT = 'sqlite:///./credara.db'


def _normalize_database_url(url: str) -> str:
    """Use psycopg3 driver; Neon/Vercel often provide postgresql:// (psycopg2)."""
    if url.startswith('postgres://'):
        return 'postgresql+psycopg://' + url[len('postgres://') :]
    if url.startswith('postgresql://'):
        return 'postgresql+psycopg://' + url[len('postgresql://') :]
    if url.startswith('postgresql+psycopg2://'):
        return 'postgresql+psycopg://' + url[len('postgresql+psycopg2://') :]
    return url


def _resolve_database_url(configured: str) -> str:
    # Prefer real Postgres URLs from Neon/Vercel over the local sqlite default.
    env_candidates = [
        os.getenv('DATABASE_URL'),
        os.getenv('POSTGRES_URL'),
        os.getenv('POSTGRES_PRISMA_URL'),
        os.getenv('DATABASE_URL_UNPOOLED'),
        os.getenv('POSTGRES_URL_NON_POOLING'),
    ]
    for candidate in env_candidates:
        if candidate and candidate.strip():
            return _normalize_database_url(candidate.strip())

    if configured and configured.strip() and configured.strip() != _SQLITE_DEFAULT:
        return _normalize_database_url(configured.strip())

    return _SQLITE_DEFAULT


settings = get_settings()
database_url = _resolve_database_url(settings.database_url)
_engine_kwargs: dict = {'pool_pre_ping': True, 'future': True}
if database_url.startswith('sqlite'):
    _engine_kwargs['connect_args'] = {'check_same_thread': False}
elif os.getenv('VERCEL'):
    # Serverless: no persistent connections across invocations.
    _engine_kwargs['poolclass'] = NullPool
else:
    _engine_kwargs.update({'pool_size': 5, 'max_overflow': 10, 'pool_recycle': 300})

engine = create_engine(database_url, **_engine_kwargs)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
