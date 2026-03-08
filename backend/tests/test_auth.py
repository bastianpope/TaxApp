"""Integration tests for auth endpoints.

Uses httpx.AsyncClient against the real FastAPI app (no mocks).
Requires the PostgreSQL container to be running (docker compose up -d db).
A separate test DB URL can be set via DATABASE_URL env var.

Event loop and DB setup are in conftest.py.
All test emails use uuid suffixes to avoid conflicts between runs.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from httpx import AsyncClient


def _email(prefix: str) -> str:
    """Generate a unique email for each test run."""
    return f"{prefix}_{uuid.uuid4().hex[:8]}@example.com"


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_register_success(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/auth/register",
        json={"email": _email("newuser"), "password": "secret123"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"
    # Refresh cookie must be set
    assert "refresh_token" in resp.cookies


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient) -> None:
    email = _email("dup")
    await client.post("/api/auth/register", json={"email": email, "password": "pass"})
    resp = await client.post("/api/auth/register", json={"email": email, "password": "pass"})
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient) -> None:
    email = _email("logintest")
    await client.post("/api/auth/register", json={"email": email, "password": "mypassword"})

    resp = await client.post("/api/auth/login", json={"email": email, "password": "mypassword"})
    assert resp.status_code == 200
    assert "access_token" in resp.json()


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient) -> None:
    email = _email("wrongpw")
    await client.post("/api/auth/register", json={"email": email, "password": "correct"})

    resp = await client.post("/api/auth/login", json={"email": email, "password": "wrong"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_me_requires_auth(client: AsyncClient) -> None:
    resp = await client.get("/api/auth/me")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_me_with_token(client: AsyncClient) -> None:
    email = _email("metest")
    reg = await client.post("/api/auth/register", json={"email": email, "password": "pw"})
    token = reg.json()["access_token"]

    resp = await client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["email"] == email
    assert body["totp_enabled"] is False


@pytest.mark.asyncio
async def test_refresh_token(client: AsyncClient) -> None:
    email = _email("refreshtest")
    reg = await client.post("/api/auth/register", json={"email": email, "password": "pw"})
    # Cookie is set automatically in the client
    assert "refresh_token" in reg.cookies

    resp = await client.post("/api/auth/refresh")
    assert resp.status_code == 200
    assert "access_token" in resp.json()


@pytest.mark.asyncio
async def test_logout(client: AsyncClient) -> None:
    email = _email("logouttest")
    await client.post("/api/auth/register", json={"email": email, "password": "pw"})

    resp = await client.post("/api/auth/logout")
    assert resp.status_code == 204

    # After logout, refresh should fail
    resp2 = await client.post("/api/auth/refresh")
    assert resp2.status_code == 401
