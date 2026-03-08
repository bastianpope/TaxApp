"""FastAPI auth dependencies — extract and validate current user from request."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from auth.security import decode_token
from db.engine import get_db
from db.models import User


async def _get_current_user(request: Request, db: AsyncSession) -> User:
    """Read Bearer token from Authorization header and return authenticated User."""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = auth_header.removeprefix("Bearer ").strip()

    try:
        payload = decode_token(token)
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalid or expired",
            headers={"WWW-Authenticate": "Bearer"},
        ) from err

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Expected access token",
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    return user


async def get_current_user(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    return await _get_current_user(request, db)


# Typed dep alias for clean route signatures
CurrentUser = Annotated[User, Depends(get_current_user)]
DbDep = Annotated[AsyncSession, Depends(get_db)]
