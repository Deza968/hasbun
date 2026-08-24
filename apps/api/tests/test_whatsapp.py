"""Tests de WhatsApp: cola asíncrona, retry con backoff, idempotencia (#F06-09/#F06-10).

El proveedor es Mock (settings por defecto); los tests controlan el fallo
vía WHATSAPP_MOCK_FAIL_RATE para probar backoff 1→5→15 y FAILED final.
"""

from __future__ import annotations

import uuid as uuid_mod
from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace

import pytest
from app.core.config import settings
from sqlalchemy import func, select

OWNER = {"email": "owner@hasbun.dev", "password": "Owner2026!"}


async def _mk_template(db, event_type: str, body: str | None = None):
    from app.modules.whatsapp.domain.models import WhatsAppTemplate

    template = WhatsAppTemplate(
        name=f"T-{event_type}-{uuid_mod.uuid4().hex[:6]}",
        event_type=event_type,
        body=body or "Hola {customer_name}, tu venta {sale_code} total {total}",
        variables=["customer_name", "sale_code", "total"],
        active=True,
    )
    db.add(template)
    await db.flush()
    return template


async def _mk_pending_message(db, *, event_type="NEW_SALE", recipient="51900000001"):
    """Crea un mensaje PENDING listo para procesar por el worker."""
    from app.modules.whatsapp.application.service import render_body
    from app.modules.whatsapp.domain.models import WhatsAppMessage, WhatsAppMessageStatus

    template = await _mk_template(db, event_type)
    variables = {"customer_name": "Cliente Test", "sale_code": "VTA-TEST-1", "total": "100.00"}
    message = WhatsAppMessage(
        recipient=recipient,
        template_id=template.id,
        payload={
            "template": template.name,
            "event_type": event_type,
            "variables": variables,
            "rendered": render_body(template.body, variables),
        },
        status=WhatsAppMessageStatus.PENDING,
        idempotency_key=f"test:{uuid_mod.uuid4().hex}",
    )
    db.add(message)
    await db.flush()
    return message


# ---------------------------------------------------------------------------
# #F06-10 — Hooks de eventos (venta → mensaje encolado)
# ---------------------------------------------------------------------------


async def _make_cash_sale(db):
    """Venta contado vía servicio → dispara hook NEW_SALE post-commit."""

    from app.modules.customers.domain.models import Customer
    from app.modules.products.domain.models import Product
    from app.modules.sales.application.service import create_cash_sale

    product = Product(
        sku=f"WA-{uuid_mod.uuid4().hex[:8].upper()}",
        slug=f"wa-{uuid_mod.uuid4().hex[:12]}",
        name=f"Prod WA {uuid_mod.uuid4().hex[:6]}",
        cost_price=Decimal("500.00"),
        sale_price=Decimal("800.00"),
        currency="PEN",
        price_rule="MANUAL",
        published=False,
        is_serialized=False,
        active=True,
    )
    db.add(product)
    customer = Customer(
        type="PERSON",
        first_name="WhatsApp",
        last_name="Cliente",
        dni=str(10000000 + int(uuid_mod.uuid4().hex[:7], 16) % 89999999),
        phone_whatsapp="51987654321",
        active=True,
    )
    db.add(customer)
    await db.flush()
    from app.modules.inventory.application.service import register_purchase

    await register_purchase(
        db, product_id=product.id, qty=Decimal("5"),
        reference_id=uuid_mod.uuid4(), created_by=None, unit_cost=Decimal("500.00"),
    )
    user = (
        await db.execute(
            select(__import__("app.modules.users.domain.models", fromlist=["User"]).User).where(
                __import__("app.modules.users.domain.models", fromlist=["User"]).User.email == "ventas@hasbun.dev"
            )
        )
    ).scalar_one()
    owner = (
        await db.execute(
            select(__import__("app.modules.users.domain.models", fromlist=["User"]).User).where(
                __import__("app.modules.users.domain.models", fromlist=["User"]).User.email == "owner@hasbun.dev"
            )
        )
    ).scalar_one()
    from app.modules.cash.domain.models import CashRegister, CashSession

    cash_session = (
        await db.execute(
            select(CashSession).where(CashSession.user_id == owner.id, CashSession.status == "OPEN")
        )
    ).scalars().first()
    if cash_session is None:
        register = CashRegister(name=f"REG-{uuid_mod.uuid4().hex[:6]}", user_id=owner.id, active=True, is_general=False)
        db.add(register)
        await db.flush()
        cash_session = CashSession(
            register_id=register.id,
            user_id=owner.id,
            status="OPEN",
            opening_amount=Decimal("0"),
            expected_cash=Decimal("0"),
            counted_cash=Decimal("0"),
            difference=Decimal("0"),
            opened_at=datetime.now(UTC),
            opened_by=owner.id,
        )
        db.add(cash_session)
        await db.flush()
    # plantilla activa para el hook NEW_SALE (si aún no existe)
    from app.modules.whatsapp.domain.models import WhatsAppTemplate

    tpl = (
        await db.execute(
            select(WhatsAppTemplate).where(
                WhatsAppTemplate.event_type == "NEW_SALE", WhatsAppTemplate.active.is_(True)
            )
        )
    ).scalars().first()
    if tpl is None:
        db.add(
            WhatsAppTemplate(
                name=f"T-NS-{uuid_mod.uuid4().hex[:6]}",
                event_type="NEW_SALE",
                body="Hola {customer_name}, venta {sale_code} total {total} registrada",
                variables=["customer_name", "sale_code", "total"],
                active=True,
            )
        )
        await db.flush()
    data = SimpleNamespace(
        customer_id=customer.id,
        items=[SimpleNamespace(product_id=product.id, serialized_unit_id=None, quantity=Decimal("1"), discount_amount=Decimal("0"))],
        payments=[{"method": "CASH", "amount": "800.00"}],
        cash_session_id=cash_session.id,
        currency="PEN",
        discount_authorization_id=None,
        idempotency_key=f"test-sale:{uuid_mod.uuid4().hex}",
        notes=None,
    )
    sale = await create_cash_sale(db, data=data, user=user)
    return sale, customer


@pytest.mark.asyncio(loop_scope="session")
async def test_sale_queues_whatsapp_message_pending(db):
    """Tras una venta existe UN mensaje PENDING new-sale:{id} — nunca enviado en-tx."""
    sale, customer = await _make_cash_sale(db)

    from app.modules.whatsapp.domain.models import WhatsAppMessage

    rows = (
        await db.execute(
            select(WhatsAppMessage).where(WhatsAppMessage.idempotency_key == f"new-sale:{sale.id}")
        )
    ).scalars().all()
    assert len(rows) == 1
    assert rows[0].status == "PENDING"  # async: aún no enviado dentro de la operación
    assert rows[0].recipient == "51987654321"


@pytest.mark.asyncio(loop_scope="session")
async def test_sale_whatsapp_hook_is_idempotent(db):
    """Llamar dos veces al hook con la misma key NO duplica el mensaje."""
    sale, _ = await _make_cash_sale(db)
    from app.modules.notifications.application.service import create_notification  # noqa: F401
    from app.modules.whatsapp.application.service import send_event

    first = await send_event(
        db,
        event_type="NEW_SALE",
        recipient="51987654321",
        variables={"sale_code": sale.code},
        idempotency_key=f"new-sale:{sale.id}",
    )
    assert first is not None and first.idempotency_key == f"new-sale:{sale.id}"
    count = (
        await db.execute(select(func.count()).select_from(
            __import__("app.modules.whatsapp.domain.models", fromlist=["WhatsAppMessage"]).WhatsAppMessage
        ).where(
            __import__("app.modules.whatsapp.domain.models", fromlist=["WhatsAppMessage"]).WhatsAppMessage.idempotency_key == f"new-sale:{sale.id}"
        ))
    ).scalar_one()
    assert count == 1


# ---------------------------------------------------------------------------
# #F06-09 — Worker: envío, retry/backoff, FAILED + notificación OWNER
# ---------------------------------------------------------------------------


@pytest.mark.asyncio(loop_scope="session")
async def test_worker_sends_message_and_logs_delivery(db):
    from app.modules.whatsapp.application.service import process_message
    from app.modules.whatsapp.domain.models import WhatsAppDeliveryLog, WhatsAppMessageStatus

    message = await _mk_pending_message(db)
    result = await process_message(db, message.id)
    assert result.status == WhatsAppMessageStatus.SENT
    assert result.sent_at is not None
    assert result.provider_message_id is not None

    logs = (
        await db.execute(select(WhatsAppDeliveryLog).where(WhatsAppDeliveryLog.message_id == message.id))
    ).scalars().all()
    assert len(logs) == 1
    assert logs[0].attempt_number == 1
    assert logs[0].status == "SENT"

    # idempotente si el worker lo reprocesa
    again = await process_message(db, message.id)
    assert again.status == WhatsAppMessageStatus.SENT


@pytest.mark.asyncio(loop_scope="session")
async def test_worker_retries_with_backoff_then_fails(db, monkeypatch):
    """3 intentos fallidos → PENDING(+1min) → PENDING(+5min) → FAILED + aviso OWNER."""
    monkeypatch.setattr(settings, "WHATSAPP_MOCK_FAIL_RATE", 1.0)
    from app.modules.whatsapp.application.service import process_message
    from app.modules.whatsapp.domain.models import WhatsAppMessageStatus

    message = await _mk_pending_message(db)

    m1 = await process_message(db, message.id)
    assert m1.status == WhatsAppMessageStatus.PENDING
    assert m1.retry_count == 1
    assert m1.next_retry_at is not None and m1.next_retry_at > datetime.now(UTC)

    m2 = await process_message(db, message.id)
    assert m2.status == WhatsAppMessageStatus.PENDING
    assert m2.retry_count == 2

    m3 = await process_message(db, message.id)
    assert m3.status == WhatsAppMessageStatus.FAILED
    assert m3.next_retry_at is None

    # notificación interna al OWNER tras agotar reintentos
    from app.modules.notifications.domain.models import Notification
    from app.modules.users.domain.models import User
    from sqlalchemy import select as sa_select

    owner = (
        await db.execute(sa_select(User).where(User.email == "owner@hasbun.dev"))
    ).scalar_one()
    notif = (
        await db.execute(
            sa_select(Notification).where(
                Notification.user_id == owner.id, Notification.type == "whatsapp_failed"
            )
        )
    ).scalars().first()
    assert notif is not None
    assert notif.priority == "HIGH"


@pytest.mark.asyncio(loop_scope="session")
async def test_manual_retry_resets_failed_message(db, monkeypatch):
    monkeypatch.setattr(settings, "WHATSAPP_MOCK_FAIL_RATE", 1.0)
    from app.modules.whatsapp.application.service import process_message, retry_failed
    from app.modules.whatsapp.domain.models import WhatsAppMessageStatus

    message = await _mk_pending_message(db)
    for _ in range(3):
        await process_message(db, message.id)
    await db.refresh(message)
    assert message.status == WhatsAppMessageStatus.FAILED

    monkeypatch.setattr(settings, "WHATSAPP_MOCK_FAIL_RATE", 0.0)
    retried = await retry_failed(db, message.id)
    assert retried.status == WhatsAppMessageStatus.PENDING
    assert retried.retry_count == 0

    sent = await process_message(db, message.id)
    assert sent.status == WhatsAppMessageStatus.SENT


# ---------------------------------------------------------------------------
# Render y config del módulo
# ---------------------------------------------------------------------------


def test_render_body_replaces_variables():
    from app.modules.whatsapp.application.service import render_body

    out = render_body("Hola {name}, total {total}", {"name": "Ana", "total": "99.50"})
    assert out == "Hola Ana, total 99.50"
    missing = render_body("Hola {name} {desconocida}", {"name": "Ana"})
    assert missing == "Hola Ana {desconocida}"  # claves ausentes quedan literales


@pytest.mark.asyncio(loop_scope="session")
async def test_module_switch_disables_queueing(db):
    from app.modules.whatsapp.application.service import module_enabled, send_event

    assert await module_enabled(db) is True  # crea fila por defecto enabled=True

    from app.modules.whatsapp.domain.models import WhatsAppConfig

    config = (await db.execute(select(WhatsAppConfig).limit(1))).scalar_one()
    config.enabled = False
    await db.commit()

    result = await send_event(
        db,
        event_type="NEW_SALE",
        recipient="51900000009",
        variables={"x": "y"},
        idempotency_key=f"switch-off:{uuid_mod.uuid4().hex}",
    )
    assert result is None  # módulo apagado → no encola

    config.enabled = True  # restaurar para otros tests
    await db.commit()
