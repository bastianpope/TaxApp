"""TaxApp — FastAPI entry point.

Configures CORS, mounts API routes, and exposes /docs.
Run: uvicorn main:app --reload
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.auth import router as auth_router
from api.calculate import router as calculate_router
from api.export import router as export_router
from api.returns import router as returns_router
from db.engine import engine
from db.models import Base

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Create all DB tables on startup (dev convenience — use Alembic in prod)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(
    title="TaxApp API",
    description=(
        "Freemium tax preparation engine — Federal + IL + MN "
        "with aggressiveness dial and audit risk scoring."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

# CORS — allow any origin in dev; tighten in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(calculate_router)
app.include_router(auth_router)
app.include_router(returns_router)
app.include_router(export_router)


@app.get("/")
async def root() -> dict:
    """Root redirect to docs."""
    return {
        "message": "TaxApp API",
        "docs": "/docs",
        "health": "/api/health",
    }
