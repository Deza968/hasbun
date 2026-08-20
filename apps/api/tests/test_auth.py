"""Tests de autenticación (#F01-14)."""

from __future__ import annotations

import httpx
from app.modules.users.domain.models import User


async def test_login_success_sets_cookies(client: httpx.AsyncClient) -> None:
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "owner@hasbun.dev", "password": "Owner2026!"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "owner@hasbun.dev"
    assert data["is_superuser"] is True
    assert "access_token" in response.cookies
    assert "refresh_token" in response.cookies
    assert response.cookies["access_token"] != ""
    # HttpOnly no se puede verificar desde el cliente, pero la cookie existe.


async def test_login_wrong_password(client: httpx.AsyncClient) -> None:
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "owner@hasbun.dev", "password": "incorrecta"},
    )
    assert response.status_code == 401
    body = response.json()
    assert "existe" not in body["error"]["message"].lower()


async def test_login_nonexistent_email_same_error(client: httpx.AsyncClient) -> None:
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "nadie@hasbun.dev", "password": "Cualquiera2026!"},
    )
    assert response.status_code == 401
    assert "credenciales" in response.json()["error"]["message"].lower()


async def test_login_inactive_user(
    client: httpx.AsyncClient, db
) -> None:
    from app.core.security import hash_password

    user = User(
        email="inactivo@hasbun.dev",
        username="inactivo",
        full_name="Usuario Inactivo",
        password_hash=hash_password("Inactivo2026!"),
        is_active=False,
    )
    db.add(user)
    await db.commit()

    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "inactivo@hasbun.dev", "password": "Inactivo2026!"},
    )
    assert response.status_code == 401


async def test_login_rate_limit_blocks(db) -> None:
    """10 intentos fallidos desde la misma IP → bloqueo temporal (LOGIN_BLOCKED)."""
    from app.core.exceptions import AuthenticationError, BusinessRuleError
    from app.modules.auth.application.service import login

    blocked = False
    for _ in range(11):
        try:
            await login(
                db,
                email="ventas@hasbun.dev",
                password="incorrecta",  # noqa: S106
                ip_address="9.9.9.9",
                user_agent=None,
            )
        except BusinessRuleError:
            blocked = True
            break
        except AuthenticationError:
            continue
    assert blocked is True


async def test_logout_invalidates_session(client: httpx.AsyncClient) -> None:
    await client.post(
        "/api/v1/auth/login",
        json={"email": "tecnico@hasbun.dev", "password": "Tecnico2026!"},
    )
    me = await client.get("/api/v1/auth/me")
    assert me.status_code == 200

    logout = await client.post("/api/v1/auth/logout")
    assert logout.status_code == 200

    me_after = await client.get("/api/v1/auth/me")
    assert me_after.status_code == 401


async def test_refresh_token_rotates(client: httpx.AsyncClient) -> None:
    await client.post(
        "/api/v1/auth/login",
        json={"email": "owner@hasbun.dev", "password": "Owner2026!"},
    )
    old_refresh = client.cookies.get("refresh_token")

    response = await client.post("/api/v1/auth/refresh")
    assert response.status_code == 200
    assert client.cookies.get("refresh_token") != old_refresh

    me = await client.get("/api/v1/auth/me")
    assert me.status_code == 200


async def test_refresh_after_logout_fails(client: httpx.AsyncClient) -> None:
    await client.post(
        "/api/v1/auth/login",
        json={"email": "software@hasbun.dev", "password": "Software2026!"},
    )
    await client.post("/api/v1/auth/logout")
    response = await client.post("/api/v1/auth/refresh")
    assert response.status_code == 401


async def test_get_me_authenticated(client: httpx.AsyncClient) -> None:
    await client.post(
        "/api/v1/auth/login",
        json={"email": "cliente@hasbun.dev", "password": "Cliente2026!"},
    )
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "cliente"
    assert data["roles"] == ["CUSTOMER"]
    assert "permissions" in data


async def test_get_me_unauthenticated(client: httpx.AsyncClient) -> None:
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401


async def test_change_password_rejects_weak_password(client: httpx.AsyncClient) -> None:
    await client.post(
        "/api/v1/auth/login",
        json={"email": "cliente@hasbun.dev", "password": "Cliente2026!"},
    )
    response = await client.post(
        "/api/v1/auth/change-password",
        json={"current_password": "Cliente2026!", "new_password": "corta1"},
    )
    assert response.status_code == 422


async def test_get_own_profile(client: httpx.AsyncClient) -> None:
    await client.post(
        "/api/v1/auth/login",
        json={"email": "cliente@hasbun.dev", "password": "Cliente2026!"},
    )
    response = await client.get("/api/v1/users/me")
    assert response.status_code == 200
    assert response.json()["username"] == "cliente"


async def test_update_own_profile(client: httpx.AsyncClient) -> None:
    await client.post(
        "/api/v1/auth/login",
        json={"email": "cliente@hasbun.dev", "password": "Cliente2026!"},
    )
    response = await client.put(
        "/api/v1/users/me", json={"full_name": "Cliente Actualizado", "phone": "999888777"}
    )
    assert response.status_code == 200
    assert response.json()["full_name"] == "Cliente Actualizado"
    assert response.json()["phone"] == "999888777"


async def test_change_password_invalidates_sessions(client: httpx.AsyncClient, db) -> None:
    from app.core.security import hash_password

    user = User(
        email="cambio@hasbun.dev",
        username="cambio",
        full_name="Cambio Pass",
        password_hash=hash_password("Original2026!"),
        is_active=True,
    )
    db.add(user)
    await db.commit()

    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "cambio@hasbun.dev", "password": "Original2026!"},
    )
    assert login.status_code == 200

    response = await client.post(
        "/api/v1/auth/change-password",
        json={"current_password": "Original2026!", "new_password": "NuevaPass2026!"},
    )
    assert response.status_code == 200

    # El access token actual quedó en blocklist → 401
    me = await client.get("/api/v1/auth/me")
    assert me.status_code == 401

    # Con la nueva contraseña se puede volver a entrar
    relogin = await client.post(
        "/api/v1/auth/login",
        json={"email": "cambio@hasbun.dev", "password": "NuevaPass2026!"},
    )
    assert relogin.status_code == 200
