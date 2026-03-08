"""Auth router — register, login, refresh, logout, /me, TOTP management."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pyotp
from fastapi import APIRouter, Cookie, HTTPException, Response, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError

from auth.deps import CurrentUser, DbDep  # noqa: TC001 — FastAPI resolves Depends() at runtime
from auth.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from db.models import Session, TotpPending, User

router = APIRouter(prefix="/api/auth", tags=["auth"])

REFRESH_COOKIE = "refresh_token"

# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class RegisterIn(BaseModel):
    email: EmailStr
    password: str


class LoginIn(BaseModel):
    email: EmailStr
    password: str
    totp_code: str | None = None


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: str
    email: str
    totp_enabled: bool


class TotpSetupOut(BaseModel):
    secret: str
    otpauth_uri: str


class TotpConfirmIn(BaseModel):
    code: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _set_refresh_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=REFRESH_COOKIE,
        value=token,
        httponly=True,
        secure=False,  # set True in production (HTTPS)
        samesite="lax",
        max_age=7 * 24 * 3600,
        path="/api/auth",
    )


async def _issue_tokens(user: User, db: DbDep, response: Response) -> TokenOut:
    """Create access + refresh tokens, persist session row, set cookie."""
    access_jti = str(uuid.uuid4())
    refresh_token, refresh_jti, expires_at = create_refresh_token(str(user.id))
    access_token = create_access_token(str(user.id), jti=access_jti)

    session = Session(jti=refresh_jti, user_id=user.id, expires_at=expires_at)
    db.add(session)
    await db.flush()

    _set_refresh_cookie(response, refresh_token)
    return TokenOut(access_token=access_token)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/register", response_model=TokenOut, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterIn, db: DbDep, response: Response) -> TokenOut:
    """Create a new account and return tokens."""
    user = User(email=body.email, hashed_password=hash_password(body.password))
    db.add(user)
    try:
        await db.flush()
    except IntegrityError as err:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with that email already exists.",
        ) from err
    return await _issue_tokens(user, db, response)


@router.post("/login", response_model=TokenOut)
async def login(body: LoginIn, db: DbDep, response: Response) -> TokenOut:
    """Authenticate with email + password (+ optional TOTP code)."""
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()

    if user is None or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    if user.totp_enabled:
        if not body.totp_code:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="TOTP code required",
                headers={"X-TOTP-Required": "true"},
            )
        totp = pyotp.TOTP(user.totp_secret or "")
        if not totp.verify(body.totp_code, valid_window=1):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid TOTP code",
            )

    return await _issue_tokens(user, db, response)


@router.post("/refresh", response_model=TokenOut)
async def refresh(
    db: DbDep,
    response: Response,
    refresh_token: str | None = Cookie(default=None, alias=REFRESH_COOKIE),
) -> TokenOut:
    """Exchange a valid refresh cookie for a new access token."""
    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No refresh token")

    try:
        payload = decode_token(refresh_token)
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token expired",
        ) from err

    if payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")

    jti = payload["jti"]
    session_result = await db.execute(select(Session).where(Session.jti == jti))
    session = session_result.scalar_one_or_none()
    if session is None or session.expires_at.replace(tzinfo=UTC) < datetime.now(
        UTC
    ):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired")

    user_id = payload["sub"]
    access_token = create_access_token(user_id)
    return TokenOut(access_token=access_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    db: DbDep,
    response: Response,
    refresh_token: str | None = Cookie(default=None, alias=REFRESH_COOKIE),
) -> None:
    """Revoke the refresh token session."""
    if refresh_token:
        try:
            payload = decode_token(refresh_token)
            jti = payload.get("jti")
            if jti:
                await db.execute(delete(Session).where(Session.jti == jti))
        except ValueError:
            pass  # already invalid — that's fine
    response.delete_cookie(REFRESH_COOKIE, path="/api/auth")


@router.get("/me", response_model=UserOut)
async def me(current_user: CurrentUser) -> UserOut:
    """Return the authenticated user's profile."""
    return UserOut(
        id=str(current_user.id),
        email=current_user.email,
        totp_enabled=current_user.totp_enabled,
    )


# ---------------------------------------------------------------------------
# TOTP Setup
# ---------------------------------------------------------------------------


@router.post("/totp/setup", response_model=TotpSetupOut)
async def totp_setup(current_user: CurrentUser, db: DbDep) -> TotpSetupOut:
    """Generate a new TOTP secret and return the OTPAuth URI for QR code display."""
    if current_user.totp_enabled:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="2FA already enabled")

    secret = pyotp.random_base32()
    totp = pyotp.TOTP(secret)
    uri = totp.provisioning_uri(name=current_user.email, issuer_name="TaxApp")

    # Store secret temporarily until confirmed
    await db.execute(delete(TotpPending).where(TotpPending.user_id == current_user.id))
    db.add(TotpPending(user_id=current_user.id, secret=secret))
    return TotpSetupOut(secret=secret, otpauth_uri=uri)


@router.post("/totp/confirm", status_code=status.HTTP_204_NO_CONTENT)
async def totp_confirm(body: TotpConfirmIn, current_user: CurrentUser, db: DbDep) -> None:
    """Verify TOTP code and activate 2FA on the account."""
    from sqlalchemy import select as sel

    result = await db.execute(sel(TotpPending).where(TotpPending.user_id == current_user.id))
    pending = result.scalar_one_or_none()
    if not pending:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No pending TOTP setup")

    totp = pyotp.TOTP(pending.secret)
    if not totp.verify(body.code, valid_window=1):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid TOTP code")

    current_user.totp_secret = pending.secret
    current_user.totp_enabled = True
    await db.execute(delete(TotpPending).where(TotpPending.user_id == current_user.id))


@router.delete("/totp", status_code=status.HTTP_204_NO_CONTENT)
async def totp_disable(current_user: CurrentUser, db: DbDep) -> None:
    """Disable 2FA."""
    current_user.totp_enabled = False
    current_user.totp_secret = None
