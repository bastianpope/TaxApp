"""Shared pytest fixtures for integration tests.

Key design decisions:
- A SINGLE session-scoped asyncio event loop prevents asyncpg
  "Future attached to a different loop" errors.
- The test engine uses NullPool to prevent connection recycling across loops.
- FastAPI's DB dependency is overridden so every request uses the test DB.
- The overridden session commits on success and rolls back on error,
  matching the production get_db behaviour so data persists between tests.
"""

from __future__ import annotations

import asyncio
import os
from typing import TYPE_CHECKING

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from db.models import Base

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

TEST_DB_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://taxapp:dev_password@localhost:5432/taxapp",
)


# ---------------------------------------------------------------------------
# Session-scoped event loop — ONE loop for all tests in the suite
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def event_loop():
    """Override default function-scoped loop with a session-scoped one."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ---------------------------------------------------------------------------
# Session-scoped DB engine and session factory
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture(scope="session")
async def db_engine():
    """Create the test DB engine once for the session."""
    engine = create_async_engine(TEST_DB_URL, echo=False, poolclass=NullPool)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture(scope="session")
async def test_session_factory(db_engine):
    """Return a session-factory bound to the test engine."""
    return async_sessionmaker(db_engine, expire_on_commit=False, class_=AsyncSession)


# ---------------------------------------------------------------------------
# Per-test HTTP client — DB dependency overridden to use test DB
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture()
async def client(test_session_factory) -> AsyncGenerator[AsyncClient, None]:
    """Yield an AsyncClient whose requests hit the test DB.

    The overridden get_db commits on success and rolls back on exceptions,
    matching the production implementation in db/engine.py.
    """
    from db.engine import get_db
    from main import app

    async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with test_session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = _override_get_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac
    app.dependency_overrides.clear()
