"""Integration tests for the returns CRUD endpoints.

Event loop and DB setup are in conftest.py.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

import pytest
import pytest_asyncio

if TYPE_CHECKING:
    from httpx import AsyncClient


@pytest_asyncio.fixture()
async def authed_client(client: AsyncClient) -> AsyncClient:
    """Returns the shared AsyncClient pre-authenticated as a unique test user."""
    email = f"ret_{uuid.uuid4().hex[:8]}@example.com"
    reg = await client.post("/api/auth/register", json={"email": email, "password": "pw"})
    token = reg.json()["access_token"]
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_empty_list(authed_client: AsyncClient) -> None:
    resp = await authed_client.get("/api/returns/")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_create_and_get(authed_client: AsyncClient) -> None:
    body = {"label": "2025 Return", "tax_year": 2025, "return_data": {"wages": 50000}}
    resp = await authed_client.post("/api/returns/", json=body)
    assert resp.status_code == 201
    data = resp.json()
    assert data["label"] == "2025 Return"
    assert data["return_data"]["wages"] == 50000

    # Get by id
    ret_id = data["id"]
    get_resp = await authed_client.get(f"/api/returns/{ret_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == ret_id


@pytest.mark.asyncio
async def test_update_return(authed_client: AsyncClient) -> None:
    create = await authed_client.post(
        "/api/returns/", json={"label": "Draft", "tax_year": 2025, "return_data": {}}
    )
    ret_id = create.json()["id"]

    resp = await authed_client.put(
        f"/api/returns/{ret_id}",
        json={"label": "Updated", "status": "complete", "return_data": {"wages": 75000}},
    )
    assert resp.status_code == 200
    updated = resp.json()
    assert updated["label"] == "Updated"
    assert updated["status"] == "complete"
    assert updated["return_data"]["wages"] == 75000


@pytest.mark.asyncio
async def test_delete_return(authed_client: AsyncClient) -> None:
    create = await authed_client.post(
        "/api/returns/", json={"label": "To Delete", "tax_year": 2025, "return_data": {}}
    )
    ret_id = create.json()["id"]

    del_resp = await authed_client.delete(f"/api/returns/{ret_id}")
    assert del_resp.status_code == 204

    get_resp = await authed_client.get(f"/api/returns/{ret_id}")
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_cannot_access_other_users_return(
    authed_client: AsyncClient, client: AsyncClient
) -> None:
    """User2 must not be able to read User1's return."""
    # User1 creates a return
    create = await authed_client.post(
        "/api/returns/", json={"label": "Private", "tax_year": 2025, "return_data": {}}
    )
    ret_id = create.json()["id"]

    # User2 registers and logs in using the shared client (overriding the auth header)
    email2 = f"other_{uuid.uuid4().hex[:8]}@example.com"
    reg2 = await client.post(
        "/api/auth/register",
        json={"email": email2, "password": "pw"},
        headers={},  # no auth header for registration
    )
    token2 = reg2.json()["access_token"]

    resp = await client.get(
        f"/api/returns/{ret_id}",
        headers={"Authorization": f"Bearer {token2}"},
    )
    assert resp.status_code == 404  # Not leaked, treated as "not found"


@pytest.mark.asyncio
async def test_unauthenticated_returns_access(client: AsyncClient) -> None:
    # Make sure no auth header is present
    resp = await client.get("/api/returns/", headers={"Authorization": ""})
    assert resp.status_code == 401
