"""Returns CRUD router — create, list, read, update, delete saved tax returns."""

from __future__ import annotations

from datetime import datetime  # noqa: TC003 — Pydantic v2 needs this at class-definition time
from typing import TYPE_CHECKING

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select

from auth.deps import CurrentUser, DbDep  # noqa: TC001 — FastAPI resolves Depends() at runtime
from db.models import TaxReturn

if TYPE_CHECKING:
    import uuid

router = APIRouter(prefix="/api/returns", tags=["returns"])

# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class ReturnSummary(BaseModel):
    id: str
    label: str
    tax_year: int
    status: str
    created_at: datetime
    updated_at: datetime


class ReturnDetail(ReturnSummary):
    return_data: dict  # type: ignore[type-arg]


class CreateReturnIn(BaseModel):
    label: str = "My Return"
    tax_year: int = 2025
    return_data: dict = {}  # type: ignore[type-arg]


class UpdateReturnIn(BaseModel):
    label: str | None = None
    status: str | None = None
    return_data: dict | None = None  # type: ignore[type-arg]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _to_summary(r: TaxReturn) -> ReturnSummary:
    return ReturnSummary(
        id=str(r.id),
        label=r.label,
        tax_year=r.tax_year,
        status=r.status,
        created_at=r.created_at,
        updated_at=r.updated_at,
    )


def _to_detail(r: TaxReturn) -> ReturnDetail:
    return ReturnDetail(
        id=str(r.id),
        label=r.label,
        tax_year=r.tax_year,
        status=r.status,
        return_data=r.return_data,
        created_at=r.created_at,
        updated_at=r.updated_at,
    )


async def _get_own_return(return_id: str, user_id: uuid.UUID, db: DbDep) -> TaxReturn:
    result = await db.execute(
        select(TaxReturn).where(
            TaxReturn.id == return_id,
            TaxReturn.user_id == user_id,
        )
    )
    r = result.scalar_one_or_none()
    if r is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Return not found")
    return r


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/", response_model=list[ReturnSummary])
async def list_returns(current_user: CurrentUser, db: DbDep) -> list[ReturnSummary]:
    """List all saved returns for the authenticated user."""
    result = await db.execute(
        select(TaxReturn)
        .where(TaxReturn.user_id == current_user.id)
        .order_by(TaxReturn.updated_at.desc())
    )
    returns = result.scalars().all()
    return [_to_summary(r) for r in returns]


@router.post("/", response_model=ReturnDetail, status_code=status.HTTP_201_CREATED)
async def create_return(body: CreateReturnIn, current_user: CurrentUser, db: DbDep) -> ReturnDetail:
    """Create a new saved return."""
    r = TaxReturn(
        user_id=current_user.id,
        label=body.label,
        tax_year=body.tax_year,
        return_data=body.return_data,
    )
    db.add(r)
    await db.flush()
    await db.refresh(r)
    return _to_detail(r)


@router.get("/{return_id}", response_model=ReturnDetail)
async def get_return(return_id: str, current_user: CurrentUser, db: DbDep) -> ReturnDetail:
    """Load a specific return (must belong to the authenticated user)."""
    r = await _get_own_return(return_id, current_user.id, db)
    return _to_detail(r)


@router.put("/{return_id}", response_model=ReturnDetail)
async def update_return(
    return_id: str, body: UpdateReturnIn, current_user: CurrentUser, db: DbDep
) -> ReturnDetail:
    """Update label, status, and/or return_data."""
    r = await _get_own_return(return_id, current_user.id, db)
    if body.label is not None:
        r.label = body.label
    if body.status is not None:
        r.status = body.status
    if body.return_data is not None:
        r.return_data = body.return_data
    await db.flush()
    await db.refresh(r)
    return _to_detail(r)


@router.delete("/{return_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_return(return_id: str, current_user: CurrentUser, db: DbDep) -> None:
    """Delete a saved return."""
    r = await _get_own_return(return_id, current_user.id, db)
    await db.delete(r)
