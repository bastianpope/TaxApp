"""SQLAlchemy ORM models — users, tax_returns, sessions."""

from __future__ import annotations

import uuid
from datetime import datetime  # noqa: TC003  SQLAlchemy resolves Mapped[datetime] at runtime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)

    # TOTP 2FA — nullable until user enables it
    totp_secret: Mapped[str | None] = mapped_column(String(64), nullable=True)
    totp_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    tax_returns: Mapped[list[TaxReturn]] = relationship(
        "TaxReturn", back_populates="user", cascade="all, delete-orphan"
    )
    sessions: Mapped[list[Session]] = relationship(
        "Session", back_populates="user", cascade="all, delete-orphan"
    )


class TaxReturn(Base):
    __tablename__ = "tax_returns"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    label: Mapped[str] = mapped_column(String(120), nullable=False, default="My Return")
    tax_year: Mapped[int] = mapped_column(nullable=False, default=2025)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="draft"
    )  # draft | complete

    # Full return payload as JSONB — mirrors frontend TaxReturn type
    return_data: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)  # type: ignore[type-arg]

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    user: Mapped[User] = relationship("User", back_populates="tax_returns")


class Session(Base):
    """Refresh token revocation table — one row per issued refresh token."""

    __tablename__ = "sessions"

    jti: Mapped[str] = mapped_column(String(36), primary_key=True)  # JWT ID (UUID string)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped[User] = relationship("User", back_populates="sessions")


class TotpPending(Base):
    """Temporary storage for TOTP secrets during setup (before confirmed)."""

    __tablename__ = "totp_pending"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    secret: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
