"""Tests de notificaciones internas (#F06-11/#F06-12/#F06-13).

Cobertura: creación por rol, visibilidad solo de las propias (403 en
ajenas), unread-count, mark-read/read-all y prioridades.
"""

from __future__ import annotations

import httpx
import pytest
from sqlalchemy import select

OWNER = {"email": "owner@hasbun.dev", "password": "Owner2026!"}
SALES = {"email": "ventas@hasbun.dev", "password": "Ventas2026!"}


async def _login(client: httpx.AsyncClient, creds: dict[str, str]) -> None:
    await client.post("/api/v1/auth/login", json=creds)


async def _get_user(db, email: str):
    from app.modules.users.domain.models import User

    return (await db.execute(select(User).where(User.email == email))).scalar_one()


@pytest.mark.asyncio(loop_scope="session")
async def test_notify_roles_creates_for_each_role_user(db):
    """notify_roles OWNER+SALES crea notificación para owner Y ventas."""
    from app.modules.notifications.application.service import notify_roles

    created = await notify_roles(
        db,
        role_codes=["OWNER", "SALES"],
        type_="quote_accepted",
        title="Cotización aceptada",
        message="El cliente aceptó la cotización",
        priority="HIGH",
    )
    emails = set()
    for n in created:
        user = await _get_user_by_id(db, n.user_id)
        emails.add(user.email)
        assert n.read is False
        assert n.priority == "HIGH"
    assert emails == {"owner@hasbun.dev", "ventas@hasbun.dev"}


async def _get_user_by_id(db, user_id):
    from app.modules.users.domain.models import User

    return await db.get(User, user_id)


@pytest.mark.asyncio(loop_scope="session")
async def test_notification_priority_urgent(db):
    from app.modules.notifications.application.service import create_notification

    owner = await _get_user(db, "owner@hasbun.dev")
    n = await create_notification(
        db,
        user_id=owner.id,
        type_="cash_closure_request",
        title="Cierre con diferencia",
        message="Diferencia S/ 50.00",
        priority="URGENT",
    )
    await db.commit()
    assert n.priority == "URGENT"
    assert n.read is False
    assert n.read_at is None


@pytest.mark.asyncio(loop_scope="session")
async def test_list_and_unread_count_flow(client: httpx.AsyncClient, db):
    from app.modules.notifications.application.service import create_notification

    owner = await _get_user(db, "owner@hasbun.dev")
    for i in range(3):
        await create_notification(
            db, user_id=owner.id, type_="test", title=f"N{i}", message=f"m{i}", priority="LOW"
        )
    await db.commit()

    await _login(client, OWNER)
    resp = await client.get("/api/v1/notifications/unread-count")
    assert resp.status_code == 200
    base_unread = resp.json()["unread"]
    assert base_unread >= 3

    listed = await client.get("/api/v1/notifications?per_page=5&unread_only=true")
    assert listed.status_code == 200
    items = listed.json()["items"]
    assert len(items) >= 3
    first = items[0]
    assert first["read"] is False

    # marcar leída → unread baja
    read_resp = await client.post(f"/api/v1/notifications/{first['id']}/read")
    assert read_resp.status_code == 200
    after = (await client.get("/api/v1/notifications/unread-count")).json()["unread"]
    assert after == base_unread - 1

    # read-all → unread 0
    all_resp = await client.post("/api/v1/notifications/read-all")
    assert all_resp.status_code == 200
    final = (await client.get("/api/v1/notifications/unread-count")).json()["unread"]
    assert final == 0


@pytest.mark.asyncio(loop_scope="session")
async def test_cannot_read_other_users_notification(client: httpx.AsyncClient, db):
    """SALES no puede marcar como leída una notificación del OWNER → 403."""
    from app.modules.notifications.application.service import create_notification

    owner = await _get_user(db, "owner@hasbun.dev")
    n = await create_notification(
        db, user_id=owner.id, type_="test", title="Solo owner", message="privada", priority="MEDIUM"
    )
    await db.commit()

    await _login(client, SALES)
    resp = await client.post(f"/api/v1/notifications/{n.id}/read")
    assert resp.status_code == 403


@pytest.mark.asyncio(loop_scope="session")
async def test_sales_does_not_see_owner_notifications(client: httpx.AsyncClient, db):
    from app.modules.notifications.application.service import create_notification

    owner = await _get_user(db, "owner@hasbun.dev")
    await create_notification(
        db, user_id=owner.id, type_="test", title="Owner only", message="x", priority="LOW"
    )
    await db.commit()

    await _login(client, SALES)
    listed = await client.get("/api/v1/notifications?per_page=100")
    titles = [i["title"] for i in listed.json()["items"]]
    assert "Owner only" not in titles


@pytest.mark.asyncio(loop_scope="session")
async def test_notification_model_defaults(db):
    from app.modules.notifications.domain.models import Notification

    owner = await _get_user(db, "owner@hasbun.dev")
    n = Notification(user_id=owner.id, type="t", title="t", message="m")
    db.add(n)
    await db.flush()
    await db.refresh(n)
    assert n.priority == "MEDIUM"
    assert n.read is False
    await db.rollback()  # no persistir este ruido de prueba
