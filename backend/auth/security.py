"""JWT + password security utilities.

Uses argon2-cffi for password hashing (OWASP-recommended, thread-safe).
Uses python-jose for JWT generation/validation.
"""

from __future__ import annotations

import os
import uuid
from datetime import UTC, datetime, timedelta

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from dotenv import load_dotenv
from jose import JWTError, jwt

load_dotenv()

_SECRET = os.getenv("JWT_SECRET_KEY", "dev_secret_change_in_production")
_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
_ACCESS_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
_REFRESH_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

_ph = PasswordHasher()


# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------


def hash_password(plain: str) -> str:
    return _ph.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return _ph.verify(hashed, plain)
    except VerifyMismatchError:
        return False


# ---------------------------------------------------------------------------
# JWT helpers
# ---------------------------------------------------------------------------


def _make_token(
    sub: str,
    jti: str,
    token_type: str,
    expire_delta: timedelta,
) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": sub,
        "jti": jti,
        "type": token_type,
        "iat": now,
        "exp": now + expire_delta,
    }
    return jwt.encode(payload, _SECRET, algorithm=_ALGORITHM)


def create_access_token(user_id: str, jti: str | None = None) -> str:
    return _make_token(
        sub=user_id,
        jti=jti or str(uuid.uuid4()),
        token_type="access",
        expire_delta=timedelta(minutes=_ACCESS_EXPIRE_MINUTES),
    )


def create_refresh_token(user_id: str, jti: str | None = None) -> tuple[str, str, datetime]:
    """Return (token, jti, expires_at)."""
    _jti = jti or str(uuid.uuid4())
    expires_at = datetime.now(UTC) + timedelta(days=_REFRESH_EXPIRE_DAYS)
    token = _make_token(
        sub=user_id,
        jti=_jti,
        token_type="refresh",
        expire_delta=timedelta(days=_REFRESH_EXPIRE_DAYS),
    )
    return token, _jti, expires_at


def decode_token(token: str) -> dict:
    """Decode and validate a JWT. Raises ValueError on failure."""
    try:
        payload = jwt.decode(token, _SECRET, algorithms=[_ALGORITHM])
        return payload  # type: ignore[return-value]
    except JWTError as exc:
        raise ValueError(f"Invalid token: {exc}") from exc
