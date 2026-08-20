"""Tests de permisos y RBAC (#F01-15)."""

from __future__ import annotations

import httpx
from app.modules.users.domain.models import User
from sqlalchemy import select

OWNER = {"email": "owner@hasbun.dev", "password": "Owner2026!"}
SALES = {"email": "ventas@hasbun.dev", "password": "Ventas2026!"}
TECH = {"email": "tecnico@hasbun.dev", "password": "Tecnico2026!"}
CUSTOMER = {"email": "cliente@hasbun.dev", "password": "Cliente2026!"}


async def _login(client: httpx.AsyncClient, creds: dict[str, str]) -> None:
    await client.post("/api/v1/auth/login", json=creds)


async def _user_id(db, email: str) -> str:
    user = (
        await db.execute(select(User).where(User.email == email))
    ).scalar_one()
    return str(user.id)


async def test_owner_can_create_user(client: httpx.AsyncClient, db) -> None:
    await _login(client, OWNER)
    response = await client.post(
        "/api/v1/users",
        json={
            "email": "nuevo@hasbun.dev",
            "username": "nuevo",
            "full_name": "Usuario Nuevo",
            "password": "Nuevo2026!",
            "role_codes": ["SALES"],
        },
    )
    assert response.status_code == 201
    assert response.json()["roles"] == ["SALES"]


async def test_sales_cannot_create_user(client: httpx.AsyncClient) -> None:
    await _login(client, SALES)
    response = await client.post(
        "/api/v1/users",
        json={
            "email": "x@hasbun.dev",
            "username": "x",
            "full_name": "X",
            "password": "Xxxxx2026!",
            "role_codes": [],
        },
    )
    assert response.status_code == 403


async def test_technician_cannot_see_audit(client: httpx.AsyncClient) -> None:
    await _login(client, TECH)
    response = await client.get("/api/v1/audit")
    assert response.status_code == 403


async def test_customer_cannot_access_users(client: httpx.AsyncClient) -> None:
    await _login(client, CUSTOMER)
    response = await client.get("/api/v1/users")
    assert response.status_code == 403


async def test_superuser_can_do_everything(client: httpx.AsyncClient) -> None:
    await _login(client, OWNER)
    assert (await client.get("/api/v1/users")).status_code == 200
    assert (await client.get("/api/v1/roles")).status_code == 200
    assert (await client.get("/api/v1/permissions")).status_code == 200


async def test_unauthenticated_request(client: httpx.AsyncClient) -> None:
    assert (await client.get("/api/v1/users")).status_code == 401
    assert (await client.get("/api/v1/audit")).status_code == 401


async def test_permission_override_grant_then_revoke(
    client: httpx.AsyncClient, db
) -> None:
    """SALES no ve roles; con override granted=True sí; con revoked no."""
    await _login(client, OWNER)
    sales_id = await _user_id(db, SALES["email"])

    # Limpiar overrides previos (otros tests pudieron dejar granted=True)
    await client.post(
        f"/api/v1/users/{sales_id}/permissions",
        json={"codename": "roles.ver", "granted": False, "reason": "reset"},
    )

    # Antes: SALES no tiene roles.ver → 403
    await _login(client, SALES)
    assert (await client.get("/api/v1/roles")).status_code == 403

    # OWNER concede override roles.ver a SALES
    await _login(client, OWNER)
    grant = await client.post(
        f"/api/v1/users/{sales_id}/permissions",
        json={"codename": "roles.ver", "granted": True, "reason": "test"},
    )
    assert grant.status_code == 204

    await _login(client, SALES)
    assert (await client.get("/api/v1/roles")).status_code == 200

    # OWNER revoca el override
    await _login(client, OWNER)
    revoke = await client.post(
        f"/api/v1/users/{sales_id}/permissions",
        json={"codename": "roles.ver", "granted": False, "reason": "test"},
    )
    assert revoke.status_code == 204

    await _login(client, SALES)
    assert (await client.get("/api/v1/roles")).status_code == 403


async def test_assign_role_to_user(client: httpx.AsyncClient, db) -> None:
    await _login(client, OWNER)
    user_id = await _user_id(db, CUSTOMER["email"])

    response = await client.post(
        f"/api/v1/users/{user_id}/roles", json={"role_code": "SALES"}
    )
    assert response.status_code == 200
    assert "SALES" in response.json()["roles"]

    # Restaurar estado
    await client.delete(f"/api/v1/users/{user_id}/roles/SALES")
    assert "SALES" not in (await client.get(f"/api/v1/users/{user_id}")).json()["roles"]
