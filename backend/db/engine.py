"""Database engine and session factory (async SQLAlchemy 2.0)."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Annotated

from dotenv import load_dotenv
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://taxapp:dev_password@localhost:5432/taxapp",
)

engine = create_async_engine(DATABASE_URL, echo=False, pool_pre_ping=True)

AsyncSessionLocal = async_sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency — yields a DB session, rolls back on error."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# Typed dependency alias for cleaner route signatures
DbDep = Annotated[AsyncSession, Depends(get_db)]
