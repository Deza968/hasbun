"""Tests de auditoría (#F01-16)."""

from __future__ import annotations

import httpx
from app.modules.users.domain.models import User
from sqlalchemy import select

OWNER = {"email": "owner@hasbun.dev", "password": "Owner2026!"}


async def _login(client: httpx.AsyncClient, creds: dict[str, str]) -> None:
    await client.post("/api/v1/auth/login", json=creds)


async def _audit_actions(client: httpx.AsyncClient) -> list[str]:
    response = await client.get("/api/v1/audit?limit=100")
    assert response.status_code == 200
    return [item["action"] for item in response.json()["items"]]


async def test_login_creates_audit_log(client: httpx.AsyncClient) -> None:
    await _login(client, OWNER)
    actions = await _audit_actions(client)
    assert "LOGIN_SUCCESS" in actions


async def test_failed_login_creates_audit_log(client: httpx.AsyncClient) -> None:
    await client.post(
        "/api/v1/auth/login",
        json={"email": "owner@hasbun.dev", "password": "incorrecta"},
    )
    await _login(client, OWNER)
    actions = await _audit_actions(client)
    assert "LOGIN_FAILED" in actions


async def test_create_user_creates_audit_log(client: httpx.AsyncClient, db) -> None:
    await _login(client, OWNER)
    await client.post(
        "/api/v1/users",
        json={
            "email": "auditado@hasbun.dev",
            "username": "auditado",
            "full_name": "Auditado",
            "password": "Audit2026!",
            "role_codes": [],
        },
    )
    actions = await _audit_actions(client)
    assert "CREATE_USER" in actions


async def test_permission_change_creates_audit_log(client: httpx.AsyncClient, db) -> None:
    await _login(client, OWNER)
    user = (
        await db.execute(select(User).where(User.email == "ventas@hasbun.dev"))
    ).scalar_one()
    response = await client.post(
        f"/api/v1/users/{user.id}/permissions",
        json={"codename": "roles.ver", "granted": True, "reason": "test"},
    )
    assert response.status_code == 204
    actions = await _audit_actions(client)
    assert "SET_PERMISSION_OVERRIDE" in actions


async def test_audit_logs_are_immutable(client: httpx.AsyncClient) -> None:
    await _login(client, OWNER)
    assert (await client.delete("/api/v1/audit")).status_code == 405
    assert (await client.put("/api/v1/audit")).status_code == 405


async def test_audit_filters(client: httpx.AsyncClient) -> None:
    await _login(client, OWNER)
    response = await client.get("/api/v1/audit?module=auth&limit=100")
    assert response.status_code == 200
    items = response.json()["items"]
    assert items and all(item["module"] == "auth" for item in items)
