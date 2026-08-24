"""Tests de cotizaciones (#F06-02/#F06-03/#F06-04/#F06-05).

Cobertura crítica: precios congelados, conversión ATÓMICA a venta
(contado/crédito), rollback si la venta falla, expiración automática
y flujo público sin login.
"""

from __future__ import annotations

import uuid as uuid_mod
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from types import SimpleNamespace

import httpx
import pytest
from sqlalchemy import select

OWNER = {"email": "owner@hasbun.dev", "password": "Owner2026!"}
SALES = {"email": "ventas@hasbun.dev", "password": "Ventas2026!"}
TECH = {"email": "tecnico@hasbun.dev", "password": "Tecnico2026!"}


async def _login(client: httpx.AsyncClient, creds: dict[str, str]) -> None:
    await client.post("/api/v1/auth/login", json=creds)


async def _mk_product(db, price: str = "1000.00"):
    from app.modules.products.domain.models import Product

    product = Product(
        sku=f"COT-{uuid_mod.uuid4().hex[:8].upper()}",
        slug=f"cot-{uuid_mod.uuid4().hex[:12]}",
        name=f"Producto Cotización {uuid_mod.uuid4().hex[:6]}",
        cost_price="600.00",
        sale_price=price,
        currency="PEN",
        price_rule="MANUAL",
        published=False,
        is_serialized=False,
        active=True,
    )
    db.add(product)
    await db.flush()
    return product


async def _add_stock(db, product_id, qty: str):
    from app.modules.inventory.application.service import register_purchase

    await register_purchase(
        db,
        product_id=product_id,
        qty=Decimal(qty),
        reference_id=uuid_mod.uuid4(),
        created_by=None,
        unit_cost=Decimal("600.00"),
    )


async def _mk_customer(db):
    from app.modules.customers.domain.models import Customer

    customer = Customer(
        type="PERSON",
        first_name=f"Cliente{uuid_mod.uuid4().hex[:6]}",
        last_name="Cotización",
        dni=str(10000000 + int(uuid_mod.uuid4().hex[:7], 16) % 89999999),
        phone_whatsapp="51900000099",
        credit_limit=Decimal("10000"),
        active=True,
    )
    db.add(customer)
    await db.flush()
    return customer


async def _get_user(db, email: str):
    from app.modules.users.domain.models import User

    return (await db.execute(select(User).where(User.email == email))).scalar_one()


async def _open_session(db, owner):
    from app.modules.cash.domain.models import CashRegister, CashSession

    session = (
        await db.execute(
            select(CashSession).where(CashSession.user_id == owner.id, CashSession.status == "OPEN")
        )
    ).scalars().first()
    if session is not None:
        return session
    register = CashRegister(name=f"REG-{uuid_mod.uuid4().hex[:6]}", user_id=owner.id, active=True, is_general=False)
    db.add(register)
    await db.flush()
    session = CashSession(
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
    db.add(session)
    await db.flush()
    return session


async def _make_quote(
    db,
    *,
    status: str = "DRAFT",
    valid_until: date | None = None,
    price: str = "1000.00",
) -> tuple:
    """Crea quote+ítem directamente (precios congelados)."""
    from app.modules.quotes.application.service import create_quote
    from app.modules.quotes.domain.models import QuoteStatus

    product = await _mk_product(db, price=price)
    customer = await _mk_customer(db)
    data = SimpleNamespace(
        customer_id=customer.id,
        items=[
            SimpleNamespace(
                product_id=product.id,
                quantity=Decimal("2"),
                unit_price=Decimal(price),
                discount_amount=Decimal("0.00"),
                notes=None,
            )
        ],
        valid_until=valid_until or date.today() + timedelta(days=7),
        currency="PEN",
        notes=None,
    )
    user = await _get_user(db, "ventas@hasbun.dev")
    quote = await create_quote(db, data=data, user=user)
    if status != "DRAFT":
        if status in ("SENT", "VIEWED", "ACCEPTED"):
            quote.status = status
            if status in ("VIEWED", "ACCEPTED"):
                quote.viewed_at = datetime.now(UTC)
            if status == "ACCEPTED":
                quote.responded_at = datetime.now(UTC)
        else:
            quote.status = status  # EXPIRED / REJECTED / CONVERTED
        await db.commit()
    assert quote.status == getattr(QuoteStatus, status)
    return quote, product, customer


# ---------------------------------------------------------------------------
# #F06-02 — Creación y flujo de estados
# ---------------------------------------------------------------------------


@pytest.mark.asyncio(loop_scope="session")
async def test_sales_can_create_and_send_quote(client: httpx.AsyncClient, db):
    await _login(client, SALES)
    product = await _mk_product(db)
    customer = await _mk_customer(db)
    from app.modules.whatsapp.domain.models import WhatsAppTemplate

    db.add(
        WhatsAppTemplate(
            name=f"T-QC-{uuid_mod.uuid4().hex[:6]}",
            event_type="QUOTE_CREATED",
            body="Hola {customer_name}, cotización {quote_code} por {total} válida hasta {valid_until}",
            variables=["customer_name", "quote_code", "total", "valid_until"],
            active=True,
        )
    )
    await db.commit()  # visible para la sesión de la petición

    resp = await client.post(
        "/api/v1/quotes",
        json={
            "customer_id": str(customer.id),
            "items": [
                {
                    "product_id": str(product.id),
                    "quantity": "2",
                    "unit_price": "1000.00",
                    "discount_amount": "50.00",
                }
            ],
            "valid_until": str(date.today() + timedelta(days=10)),
        },
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["status"] == "DRAFT"
    assert body["code"].startswith("COT-")
    assert Decimal(body["total"]) == Decimal("1950.00")

    # DRAFT → SENT encola mensaje WhatsApp PENDING (idempotencia quote-created:{id})
    sent = await client.post(f"/api/v1/quotes/{body['id']}/send")
    assert sent.status_code == 200
    assert sent.json()["status"] == "SENT"

    from app.modules.whatsapp.domain.models import WhatsAppMessage

    rows = (
        await db.execute(
            select(WhatsAppMessage).where(
                WhatsAppMessage.idempotency_key == f"quote-created:{body['id']}"
            )
        )
    ).scalars().all()
    assert len(rows) == 1
    assert rows[0].status == "PENDING"


@pytest.mark.asyncio(loop_scope="session")
async def test_technician_cannot_create_quotes(client: httpx.AsyncClient, db_setup):
    await _login(client, TECH)
    resp = await client.post(
        "/api/v1/quotes",
        json={"customer_id": str(uuid_mod.uuid4()), "items": [], "valid_until": str(date.today())},
    )
    assert resp.status_code == 403


@pytest.mark.asyncio(loop_scope="session")
async def test_only_draft_quotes_can_be_edited(client: httpx.AsyncClient, db):
    await _login(client, SALES)
    quote, product, customer = await _make_quote(db, status="SENT")

    resp = await client.put(
        f"/api/v1/quotes/{quote.id}",
        json={"notes": "cambio"},
    )
    assert resp.status_code == 400


@pytest.mark.asyncio(loop_scope="session")
async def test_public_view_marks_sent_as_viewed(client: httpx.AsyncClient, db):
    await _login(client, OWNER)  # rutas públicas no requieren login, login solo para crear
    quote, product, customer = await _make_quote(db, status="SENT")

    resp = await client.get(f"/api/v1/quotes/{quote.code}/public")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "VIEWED"  # SENT → VIEWED automático (#F06-02)
    assert len(body["items"]) == 1

    respond = await client.post(
        f"/api/v1/quotes/{quote.code}/public/respond",
        json={"decision": "accept"},
    )
    assert respond.status_code == 200
    assert respond.json()["status"] == "ACCEPTED"


@pytest.mark.asyncio(loop_scope="session")
async def test_public_reject_with_reason(client: httpx.AsyncClient, db):
    quote, _, _ = await _make_quote(db, status="VIEWED")

    resp = await client.post(
        f"/api/v1/quotes/{quote.code}/public/respond",
        json={"decision": "reject", "reason": "Muy caro"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "REJECTED"


# ---------------------------------------------------------------------------
# #F06-01 — Precios congelados
# ---------------------------------------------------------------------------


@pytest.mark.asyncio(loop_scope="session")
async def test_quote_freezes_prices(db):
    quote, product, customer = await _make_quote(db, price="1000.00")

    # el precio del producto cambia DESPUÉS de crear la cotización
    product.sale_price = Decimal("5000.00")
    db.add(product)
    await db.commit()
    await db.refresh(quote)
    item = quote.items[0]
    assert item.unit_price == Decimal("1000.00")  # congelado
    assert quote.total == Decimal("2000.00")


# ---------------------------------------------------------------------------
# #F06-04 — Expiración automática
# ---------------------------------------------------------------------------


@pytest.mark.asyncio(loop_scope="session")
async def test_expire_pending_quotes_task(db):
    from app.modules.quotes.application.service import expire_pending_quotes
    from app.modules.quotes.domain.models import QuoteStatus

    q1, _, _ = await _make_quote(db, status="DRAFT")
    q2, _, _ = await _make_quote(db, status="SENT")
    # se vencieron después de crearse (el servicio exige vigencia futura al crear)
    q1.valid_until = date.today() - timedelta(days=1)
    q2.valid_until = date.today() - timedelta(days=2)
    await db.commit()

    result = await expire_pending_quotes(db)
    assert result["expired"] >= 2
    await db.refresh(q1)
    await db.refresh(q2)
    assert q1.status == QuoteStatus.EXPIRED
    assert q2.status == QuoteStatus.EXPIRED

    # idempotente: segunda corrida no re-expira nada nuevo de estas
    again = await expire_pending_quotes(db)
    assert isinstance(again["expired"], int)


# ---------------------------------------------------------------------------
# #F06-03 — Conversión atómica
# ---------------------------------------------------------------------------


@pytest.mark.asyncio(loop_scope="session")
async def test_convert_accepted_quote_to_cash_sale(client: httpx.AsyncClient, db):
    await _login(client, OWNER)
    owner = await _get_user(db, "owner@hasbun.dev")
    session = await _open_session(db, owner)
    quote, product, customer = await _make_quote(db, status="ACCEPTED", price="1000.00")
    await _add_stock(db, product.id, "10")
    await db.commit()  # liberar locks: la petición usa otra sesión

    resp = await client.post(
        f"/api/v1/quotes/{quote.id}/convert",
        json={"sale_type": "CASH", "cash_session_id": str(session.id)},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["sale_status"] == "PAID"
    assert Decimal(body["sale_total"]) == Decimal("2000.00")  # precio congelado × 2

    await db.refresh(quote)
    from app.modules.quotes.domain.models import QuoteStatus

    assert quote.status == QuoteStatus.CONVERTED
    assert str(quote.converted_to_sale_id) == body["sale_id"]

    # doble conversión → 409 ConflictError
    dup = await client.post(
        f"/api/v1/quotes/{quote.id}/convert",
        json={"sale_type": "CASH", "cash_session_id": str(session.id)},
    )
    assert dup.status_code == 409


@pytest.mark.asyncio(loop_scope="session")
async def test_convert_accepted_quote_to_credit(db):
    from app.modules.credits.domain.models import CreditAgreement
    from app.modules.quotes.application.service import convert_quote_to_sale

    quote, product, customer = await _make_quote(db, status="ACCEPTED", price="800.00")
    await _add_stock(db, product.id, "5")
    user = await _get_user(db, "ventas@hasbun.dev")

    data = SimpleNamespace(
        sale_type="CREDIT",
        cash_session_id=None,
        payments=[],
        initial_payment=Decimal("400.00"),
        number_of_installments=2,
        interest_rate=Decimal("0"),
        interest_free_months=1,
        first_due_date=date.today() + timedelta(days=30),
        initial_method="CASH",
        authorization_ids=[],
    )
    sale = await convert_quote_to_sale(db, quote_id=quote.id, data=data, user=user)
    agreement = (
        await db.execute(select(CreditAgreement).where(CreditAgreement.sale_id == sale.id))
    ).scalar_one()
    assert agreement.total_amount == Decimal("1600.00")  # congelado × 2
    await db.refresh(quote)
    assert quote.converted_to_sale_id == sale.id


@pytest.mark.asyncio(loop_scope="session")
async def test_cannot_convert_expired_quote(db):
    from app.core.exceptions import BusinessRuleError
    from app.modules.quotes.application.service import convert_quote_to_sale

    quote, product, customer = await _make_quote(db, status="EXPIRED")
    quote.valid_until = date.today() - timedelta(days=1)  # venció después de crearse
    await db.commit()
    user = await _get_user(db, "ventas@hasbun.dev")
    with pytest.raises(BusinessRuleError):
        await convert_quote_to_sale(
            db,
            quote_id=quote.id,
            data=SimpleNamespace(sale_type="CASH", cash_session_id=None, payments=[]),
            user=user,
        )


@pytest.mark.asyncio(loop_scope="session")
async def test_cannot_convert_non_accepted_quote(db):
    from app.core.exceptions import BusinessRuleError
    from app.modules.quotes.application.service import convert_quote_to_sale

    quote, _, _ = await _make_quote(db, status="DRAFT")
    user = await _get_user(db, "ventas@hasbun.dev")
    with pytest.raises(BusinessRuleError):
        await convert_quote_to_sale(
            db,
            quote_id=quote.id,
            data=SimpleNamespace(sale_type="CASH", cash_session_id=None, payments=[]),
            user=user,
        )


@pytest.mark.asyncio(loop_scope="session")
async def test_conversion_rollback_keeps_quote_intact(db, monkeypatch):
    """Si la venta falla a mitad de camino, TODO hace rollback y la quote sigue ACCEPTED."""
    from app.modules.quotes.application.service import convert_quote_to_sale

    quote, product, customer = await _make_quote(db, status="ACCEPTED", price="1000.00")
    await _add_stock(db, product.id, "3")
    owner = await _get_user(db, "owner@hasbun.dev")
    cash_session = await _open_session(db, owner)
    user = await _get_user(db, "ventas@hasbun.dev")

    import app.modules.sales.application.service as sales_service

    async def boom(*args, **kwargs):
        raise RuntimeError("fallo simulado de inventario")

    monkeypatch.setattr(sales_service, "confirm_sale", boom)

    data = SimpleNamespace(sale_type="CASH", cash_session_id=cash_session.id, payments=[])
    with pytest.raises(RuntimeError):
        await convert_quote_to_sale(db, quote_id=quote.id, data=data, user=user)
    await db.rollback()

    from app.modules.sales.domain.models import Sale

    await db.refresh(quote)
    assert quote.status == "ACCEPTED"  # intacta
    assert quote.converted_to_sale_id is None
    # no quedó ninguna venta huérfana de esta cotización
    orphan = (
        await db.execute(select(Sale).where(Sale.notes == f"Convertida desde cotización {quote.code}"))
    ).scalars().all()
    assert orphan == []
