"""Async SQLite engine + session management (SQLModel over SQLAlchemy async).

The production engine is created at import but opens no connection until first
use, so importing is side-effect-free. Tests build their own engine against a
temp database and override ``get_session``.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from app.config import settings


def to_async_url(url: str) -> str:
    """Map a sync SQLite URL to its aiosqlite driver form."""
    if url.startswith("sqlite://") and "+aiosqlite" not in url:
        return url.replace("sqlite://", "sqlite+aiosqlite://", 1)
    return url


def make_engine(url: str | None = None) -> AsyncEngine:
    return create_async_engine(to_async_url(url or settings.database_url), future=True)


def make_sessionmaker(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


# Process-wide engine + session factory.
engine: AsyncEngine = make_engine()
SessionLocal: async_sessionmaker[AsyncSession] = make_sessionmaker(engine)


async def init_db(target: AsyncEngine | None = None) -> None:
    """Create tables. Import store so its table models are registered first."""
    import app.store  # noqa: F401  (registers SQLModel tables)

    eng = target or engine
    async with eng.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def get_session() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency yielding an async session."""
    async with SessionLocal() as session:
        yield session
