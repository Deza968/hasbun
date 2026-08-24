"""Tests de créditos, cuotas y mora (#F05-17..#F05-22).

Cobertura crítica financiera: validaciones pre-crédito, creación atómica,
pagos parciales/totales/idempotentes, mora sin capitalización,
reprogramación OWNER-only y entrega anticipada.
"""

from __future__ import annotations

import uuid as uuid_mod
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from types import SimpleNamespace

import httpx
import pytest
from app.modules.credits.application.service import add_months
from sqlalchemy import func, select, text
from sqlalchemy.orm import selectinload

OWNER = {"email": "owner@hasbun.dev", "password": "Owner2026!"}
SALES = {"email": "ventas@hasbun.dev", "password": "Ventas2026!"}


async def _login(client: httpx.AsyncClient, creds: dict[str, str]) -> None:
    await client.post("/api/v1/auth/login", json=creds)


async def _mk_product(db, name: str, price: str = "1000.00", serialized: bool = False):
    from app.modules.products.domain.models import Product

    product = Product(
        sku=f"CRD-{uuid_mod.uuid4().hex[:8].upper()}",
        slug=f"crd-{uuid_mod.uuid4().hex[:12]}",
        name=name,
        cost_price="600.00",
        sale_price=price,
        currency="PEN",
        price_rule="MANUAL",
        published=False,
        is_serialized=serialized,
        active=True,
    )
    db.add(product)
    await db.flush()
    if serialized:
        from app.modules.products.domain.models import SerializedUnit

        unit = SerializedUnit(
            product_id=product.id,
            serial_number=f"SN-{uuid_mod.uuid4().hex[:10].upper()}",
            status="AVAILABLE",
        )
        db.add(unit)
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


async def _mk_customer(db, *, limit: str, frequent: bool = False):
    from app.modules.customers.domain.models import Customer

    customer = Customer(
        type="PERSON",
        first_name=f"Cliente{uuid_mod.uuid4().hex[:6]}",
        last_name="Crédito",
        dni=str(10000000 + int(uuid_mod.uuid4().hex[:7], 16) % 89999999),
        credit_limit=Decimal(limit),
        is_frequent=frequent,
        active=True,
    )
    db.add(customer)
    await db.flush()
    return customer


async def _get_owner(db):
    from app.modules.users.domain.models import User

    return (await db.execute(select(User).where(User.email == "owner@hasbun.dev"))).scalar_one()


async def _open_session(db, owner):
    """Sesión OPEN del owner (reutiliza si existe por índice único parcial)."""
    from app.modules.cash.domain.models import CashRegister, CashSession

    session = (
        await db.execute(select(CashSession).where(CashSession.user_id == owner.id, CashSession.status == "OPEN"))
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


async def _make_credit(
    db,
    *,
    customer,
    product,
    total: str = "2500.00",
    initial: str = "500.00",
    n: int = 4,
    free: int = 0,
    rate: str = "0",
    first_due: date | None = None,
    serialized_unit_id=None,
):
    """Crea un crédito vía servicio (el servicio hace su propio commit)."""
    from app.modules.credits.application.service import create_credit_sale
    from app.modules.credits.domain.models import CreditAgreement

    owner = await _get_owner(db)
    # el servicio calcula el total real desde los ítems (precio × cantidad);
    # alinear el precio del producto con el total esperado por el test
    product.sale_price = Decimal(total)
    db.add(product)
    await db.commit()
    data = SimpleNamespace(
        customer_id=customer.id,
        total_amount=Decimal(total),
        initial_payment=Decimal(initial),
        number_of_installments=n,
        authorization_ids=[],
        items=[
            SimpleNamespace(
                product_id=product.id,
                quantity=Decimal("1"),
                serialized_unit_id=serialized_unit_id,
            )
        ],
        interest_rate=Decimal(rate),
        interest_free_months=free,
        currency="PEN",
        first_due_date=first_due or (date.today() + timedelta(days=30)),
        initial_method="CASH",
        cash_session_id=None,
        notes=None,
    )
    created = await create_credit_sale(db, data=data, user=owner)
    # recargar con cuotas cargadas explícitamente (evita lazy-load en async);
    # el commit cierra la transacción implícita de lectura y, con
    # expire_on_commit=False, conserva los objetos cargados
    res = await db.execute(
        select(CreditAgreement)
        .options(selectinload(CreditAgreement.installments))
        .where(CreditAgreement.id == created.id)
    )
    agreement = res.scalar_one()
    await db.commit()
    return agreement


# ---------------------------------------------------------------------------
# #F05-17 — Validación pre-crédito
# ---------------------------------------------------------------------------


async def test_delinquent_customer_blocked(client: httpx.AsyncClient, db):
    await _login(client, SALES)
    async with db.begin():
        product = await _mk_product(db, "Prod moroso")
        await _add_stock(db, product.id, "5")
        customer = await _mk_customer(db, limit="5000", frequent=True)

    await _make_credit(db, customer=customer, product=product)
    # forzar morosidad: primera cuota vencida el mes pasado
    async with db.begin():
        from app.modules.credits.domain.models import CreditInstallment

        inst = (
            await db.execute(select(CreditInstallment).order_by(CreditInstallment.created_at.desc()).limit(1))
        ).scalar_one()
        inst.due_date = date.today() - timedelta(days=35)

    resp = await client.post(
        "/api/v1/credits/validate",
        json={
            "customer_id": str(customer.id),
            "total_amount": "1000",
            "initial_payment": "200",
            "number_of_installments": 3,
        },
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["approved"] is False
    assert any(b["type"] == "CUSTOMER_DELINQUENT" for b in body["blockers"])

    # crear crédito → bloqueado
    resp2 = await client.post(
        "/api/v1/credits",
        json={
            "customer_id": str(customer.id),
            "total_amount": "1000",
            "initial_payment": "200",
            "number_of_installments": 3,
            "first_due_date": str(date.today() + timedelta(days=30)),
            "items": [{"product_id": str(product.id), "quantity": "1"}],
        },
    )
    assert resp2.status_code == 400
    assert resp2.json()["error"]["code"] == "BUSINESS_RULE_VIOLATION"


async def test_delinquent_override_requires_owner(client: httpx.AsyncClient, db):
    await _login(client, SALES)
    from app.modules.credits.domain.models import AuthorizationType, CreditAuthorization

    async with db.begin():
        product = await _mk_product(db, "Prod override")
        await _add_stock(db, product.id, "5")
        customer = await _mk_customer(db, limit="9000", frequent=True)

    await _make_credit(db, customer=customer, product=product)
    async with db.begin():
        from app.modules.credits.domain.models import CreditInstallment

        inst = (
            await db.execute(select(CreditInstallment).order_by(CreditInstallment.created_at.desc()).limit(1))
        ).scalar_one()
        inst.due_date = date.today() - timedelta(days=35)
        owner = await _get_owner(db)
        auth_delinq = CreditAuthorization(
            customer_id=customer.id,
            type=AuthorizationType.OVERRIDE_DELINQUENCY,
            requested_by=owner.id,
            approved_by=owner.id,
            reason="Autorización especial mora",
            status="APPROVED",
            requested_at=datetime.now(UTC),
            reviewed_at=datetime.now(UTC),
        )
        auth_multiple = CreditAuthorization(
            customer_id=customer.id,
            type=AuthorizationType.MULTIPLE_CREDITS,
            requested_by=owner.id,
            approved_by=owner.id,
            reason="Segundo crédito autorizado",
            status="APPROVED",
            requested_at=datetime.now(UTC),
            reviewed_at=datetime.now(UTC),
        )
        db.add_all([auth_delinq, auth_multiple])
        await db.flush()
        ids = [str(auth_delinq.id), str(auth_multiple.id)]

    resp = await client.post(
        "/api/v1/credits/validate",
        json={
            "customer_id": str(customer.id),
            "total_amount": "1000",
            "initial_payment": "200",
            "number_of_installments": 3,
            "authorization_ids": ids,
        },
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["approved"] is True, body["blockers"]
    assert not any(b["type"] == "CUSTOMER_DELINQUENT" for b in body["blockers"])


async def test_credit_limit_enforced(client: httpx.AsyncClient, db):
    await _login(client, SALES)
    async with db.begin():
        customer = await _mk_customer(db, limit="100", frequent=True)
        cid = str(customer.id)

    resp = await client.post(
        "/api/v1/credits/validate",
        json={"customer_id": cid, "total_amount": "1000", "initial_payment": "100", "number_of_installments": 2},
    )
    body = resp.json()
    assert body["approved"] is False
    assert any(b["authorization"] == "OVERRIDE_LIMIT" for b in body["blockers"])


async def test_multiple_credits_require_authorization(client: httpx.AsyncClient, db):
    await _login(client, SALES)
    async with db.begin():
        product = await _mk_product(db, "Prod multi")
        await _add_stock(db, product.id, "5")
        customer = await _mk_customer(db, limit="20000", frequent=True)
        cid = str(customer.id)

    await _make_credit(db, customer=customer, product=product)

    resp = await client.post(
        "/api/v1/credits/validate",
        json={"customer_id": cid, "total_amount": "1000", "initial_payment": "200", "number_of_installments": 2},
    )
    body = resp.json()
    assert any(b["authorization"] == "MULTIPLE_CREDITS" for b in body["blockers"])


async def test_initial_required_for_non_frequent(client: httpx.AsyncClient, db):
    await _login(client, SALES)
    async with db.begin():
        customer = await _mk_customer(db, limit="5000", frequent=False)
        cid = str(customer.id)

    resp = await client.post(
        "/api/v1/credits/validate",
        json={"customer_id": cid, "total_amount": "1000", "initial_payment": "0", "number_of_installments": 2},
    )
    body = resp.json()
    assert body["approved"] is False
    assert any(b["authorization"] == "WAIVE_INITIAL" for b in body["blockers"])


async def test_frequent_customer_can_waive_initial_with_owner(client: httpx.AsyncClient, db):
    await _login(client, SALES)
    async with db.begin():
        customer = await _mk_customer(db, limit="5000", frequent=True)
        cid = str(customer.id)

    resp = await client.post(
        "/api/v1/credits/validate",
        json={"customer_id": cid, "total_amount": "1000", "initial_payment": "0", "number_of_installments": 2},
    )
    body = resp.json()
    assert body["approved"] is True, body["blockers"]
    assert not any(b["authorization"] == "WAIVE_INITIAL" for b in body["blockers"])


# ---------------------------------------------------------------------------
# #F05-18 — Creación atómica
# ---------------------------------------------------------------------------


async def test_credit_creates_correct_installments(client: httpx.AsyncClient, db):
    async with db.begin():
        product = await _mk_product(db, "Laptop cuotas")
        await _add_stock(db, product.id, "5")
        customer = await _mk_customer(db, limit="20000", frequent=True)
    first_due = date.today() + timedelta(days=30)

    agreement = await _make_credit(
        db, customer=customer, product=product, total="2500.00", initial="500.00", n=4, rate="0", first_due=first_due
    )
    assert agreement.code.startswith("CRD-")
    assert len(agreement.code.split("-")[-1]) == 5
    assert Decimal(agreement.financed_amount) == Decimal("2000.00")
    installments = sorted(agreement.installments, key=lambda i: i.number)
    assert len(installments) == 4
    assert [Decimal(i.amount) for i in installments] == [Decimal("500.00")] * 4
    assert installments[0].due_date == first_due
    assert installments[1].due_date == add_months(first_due, 1)
    assert all(i.status == "PENDING" for i in installments)
    assert agreement.status == "ACTIVE"


async def test_credit_interest_free_months_applied(client: httpx.AsyncClient, db):
    async with db.begin():
        product = await _mk_product(db, "Free months")
        await _add_stock(db, product.id, "5")
        customer = await _mk_customer(db, limit="20000", frequent=True)

    agreement = await _make_credit(
        db, customer=customer, product=product, total="2500.00", initial="500.00", n=4, free=2, rate="0.03"
    )
    installments = sorted(agreement.installments, key=lambda i: i.number)
    assert Decimal(installments[0].amount) == Decimal("500.00")
    assert Decimal(installments[1].amount) == Decimal("500.00")


async def test_credit_interest_applied_after_free_months(client: httpx.AsyncClient, db):
    async with db.begin():
        product = await _mk_product(db, "Interest after")
        await _add_stock(db, product.id, "5")
        customer = await _mk_customer(db, limit="20000", frequent=True)

    agreement = await _make_credit(
        db, customer=customer, product=product, total="2500.00", initial="500.00", n=4, free=2, rate="0.03"
    )
    installments = sorted(agreement.installments, key=lambda i: i.number)
    # interés flat: 500 + 2000 * 0.03 = 560
    assert Decimal(installments[2].amount) == Decimal("560.00")
    assert Decimal(installments[3].amount) == Decimal("560.00")


async def test_credit_atomic_rollback(client: httpx.AsyncClient, db):
    """Si un ítem falla (stock insuficiente) NADA se persiste."""
    from app.core.exceptions import BusinessRuleError
    from app.database.session import AsyncSessionLocal
    from app.modules.credits.application.service import create_credit_sale
    from app.modules.credits.domain.models import CreditAgreement
    from app.modules.sales.domain.models import Sale

    async with AsyncSessionLocal() as session:
        async with session.begin():
            p_ok = await _mk_product(session, "Atomic ok")
            await _add_stock(session, p_ok.id, "5")
            p_fail = await _mk_product(session, "Atomic fail")
            customer = await _mk_customer(session, limit="20000", frequent=True)
            owner = await _get_owner(session)

    async with AsyncSessionLocal() as session:
        base_sales = (await session.execute(select(func.count(Sale.id)))).scalar()
        base_agreements = (await session.execute(select(func.count(CreditAgreement.id)))).scalar()

    data = SimpleNamespace(
        customer_id=customer.id,
        total_amount=Decimal("3000"),
        initial_payment=Decimal("500"),
        number_of_installments=3,
        authorization_ids=[],
        items=[
            SimpleNamespace(product_id=p_ok.id, quantity=Decimal("1"), serialized_unit_id=None),
            SimpleNamespace(product_id=p_fail.id, quantity=Decimal("1"), serialized_unit_id=None),
        ],
        interest_rate=Decimal("0"),
        interest_free_months=0,
        currency="PEN",
        first_due_date=date.today() + timedelta(days=30),
        initial_method="CASH",
        cash_session_id=None,
        notes=None,
    )

    with pytest.raises(BusinessRuleError):
        async with AsyncSessionLocal() as session:
            try:
                await create_credit_sale(session, data=data, user=owner)
            except Exception:
                await session.rollback()
                raise

    async with AsyncSessionLocal() as session:
        after_sales = (await session.execute(select(func.count(Sale.id)))).scalar()
        after_agreements = (await session.execute(select(func.count(CreditAgreement.id)))).scalar()
    assert after_sales == base_sales
    assert after_agreements == base_agreements


async def test_credit_freezes_exchange_rate(client: httpx.AsyncClient, db):
    from app.core.config import settings

    async with db.begin():
        product = await _mk_product(db, "TC congelado")
        await _add_stock(db, product.id, "5")
        customer = await _mk_customer(db, limit="20000", frequent=True)

    agreement = await _make_credit(db, customer=customer, product=product)
    assert Decimal(agreement.exchange_rate) == Decimal(str(settings.MOCK_EXCHANGE_RATE_USD_PEN))
    assert agreement.exchange_rate_source == "mock"
    assert agreement.exchange_rate_timestamp is not None


async def test_credit_creates_reservation(client: httpx.AsyncClient, db):
    from app.modules.credits.domain.models import Reservation, ReservationStatus
    from app.modules.inventory.domain.models import InventoryMovement, MovementType

    async with db.begin():
        product = await _mk_product(db, "Reserva crédito")
        await _add_stock(db, product.id, "5")
        customer = await _mk_customer(db, limit="20000", frequent=True)

    agreement = await _make_credit(db, customer=customer, product=product, total="1000", initial="200", n=2)
    async with db.begin():
        reservation = (
            await db.execute(select(Reservation).where(Reservation.credit_agreement_id == agreement.id))
        ).scalar_one()
        assert reservation.status == ReservationStatus.ACTIVE
        assert reservation.sale_id == agreement.sale_id
        movements = (
            await db.execute(
                select(InventoryMovement).where(
                    InventoryMovement.reference_type == "credit",
                    InventoryMovement.reference_id == agreement.sale_id,
                    InventoryMovement.movement_type == MovementType.RESERVATION,
                )
            )
        ).scalars().all()
        assert len(movements) == 1
        assert Decimal(movements[0].quantity) == Decimal("-1")
        summary = (
            await db.execute(
                text("SELECT available FROM v_product_stock WHERE product_id = :pid").bindparams(pid=product.id)
            )
        ).first()
        assert Decimal(str(summary[0])) == Decimal("4")


async def test_credit_audit_log_has_all_terms(client: httpx.AsyncClient, db):
    from app.modules.audit.domain.models import AuditLog

    async with db.begin():
        product = await _mk_product(db, "Auditoría crédito")
        await _add_stock(db, product.id, "5")
        customer = await _mk_customer(db, limit="20000", frequent=True)

    agreement = await _make_credit(
        db, customer=customer, product=product, total="2500", initial="500", n=4, free=1, rate="0.03"
    )

    audit = (
        await db.execute(
            select(AuditLog).where(AuditLog.action == "CREATE_CREDIT", AuditLog.entity_id == agreement.id)
        )
    ).scalar_one_or_none()
    assert audit is not None
    nv = audit.new_values
    assert nv["financed_amount"] == "2000.00"
    assert nv["total_amount"] == "2500.00"
    assert nv["number_of_installments"] == 4
    assert nv["interest_free_months"] == 1
    assert nv["interest_rate"] == "0.03"
    assert nv["exchange_rate"]
    assert nv["first_due_date"]


# ---------------------------------------------------------------------------
# #F05-19 — Pago de cuotas
# ---------------------------------------------------------------------------


async def test_partial_payment_updates_installment(client: httpx.AsyncClient, db):
    async with db.begin():
        product = await _mk_product(db, "Pago parcial")
        await _add_stock(db, product.id, "5")
        customer = await _mk_customer(db, limit="20000", frequent=True)

    agreement = await _make_credit(db, customer=customer, product=product, total="1000", initial="0", n=2)
    inst = sorted(agreement.installments, key=lambda i: i.number)[0]

    await _login(client, OWNER)
    resp = await client.post(
        f"/api/v1/installments/{inst.id}/pay",
        json={"amount": "200", "method": "CASH"},
    )
    assert resp.status_code == 200, resp.text

    detail = (await client.get(f"/api/v1/installments/{inst.id}")).json()
    assert detail["status"] == "PARTIALLY_PAID"
    assert Decimal(detail["paid_amount"]) == Decimal("200")
    assert Decimal(detail["remaining_amount"]) == Decimal("300")
    assert Decimal(detail["total_due"]) == Decimal("300")


async def test_full_payment_marks_installment_paid(client: httpx.AsyncClient, db):
    async with db.begin():
        product = await _mk_product(db, "Pago total")
        await _add_stock(db, product.id, "5")
        customer = await _mk_customer(db, limit="20000", frequent=True)

    agreement = await _make_credit(db, customer=customer, product=product, total="1000", initial="0", n=2)
    inst = sorted(agreement.installments, key=lambda i: i.number)[0]

    await _login(client, OWNER)
    resp = await client.post(
        f"/api/v1/installments/{inst.id}/pay", json={"amount": "500", "method": "CASH"}
    )
    assert resp.status_code == 200, resp.text
    detail = (await client.get(f"/api/v1/installments/{inst.id}")).json()
    assert detail["status"] == "PAID"
    assert Decimal(detail["remaining_amount"]) == Decimal("0")


async def test_payment_idempotency(client: httpx.AsyncClient, db):
    from app.modules.cash.domain.models import CashMovement
    from app.modules.credits.domain.models import CreditPayment

    async with db.begin():
        product = await _mk_product(db, "Idempotencia")
        await _add_stock(db, product.id, "5")
        customer = await _mk_customer(db, limit="20000", frequent=True)
        owner = await _get_owner(db)
        cash_session = await _open_session(db, owner)

    agreement = await _make_credit(db, customer=customer, product=product, total="1000", initial="0", n=2)
    inst = sorted(agreement.installments, key=lambda i: i.number)[0]

    await _login(client, OWNER)
    payload = {
        "amount": "100",
        "method": "CASH",
        "idempotency_key": f"IDEM-{uuid_mod.uuid4().hex[:8]}",
        "cash_session_id": str(cash_session.id),
    }
    r1 = await client.post(f"/api/v1/installments/{inst.id}/pay", json=payload)
    r2 = await client.post(f"/api/v1/installments/{inst.id}/pay", json=payload)
    assert r1.status_code == 200 and r2.status_code == 200
    assert r1.json()["id"] == r2.json()["id"], "misma clave debe retornar mismo pago"

    count_payments = (
        await db.execute(select(func.count(CreditPayment.id)).where(CreditPayment.installment_id == inst.id))
    ).scalar()
    assert count_payments == 1
    count_cash = (
        await db.execute(select(func.count(CashMovement.id)).where(CashMovement.idempotency_key == f"{payload['idempotency_key']}-CASH"))
    ).scalar()
    assert count_cash == 1


async def test_last_installment_completes_credit(client: httpx.AsyncClient, db):
    from app.modules.credits.domain.models import AgreementStatus, CreditAgreement, CreditInstallment
    from app.modules.inventory.domain.models import InventoryMovement, MovementType
    from app.modules.sales.domain.models import Sale

    async with db.begin():
        product = await _mk_product(db, "Última cuota")
        await _add_stock(db, product.id, "5")
        customer = await _mk_customer(db, limit="20000", frequent=True)

    agreement = await _make_credit(db, customer=customer, product=product, total="1000", initial="0", n=2)
    sale_id = agreement.sale_id

    await _login(client, OWNER)
    insts = (await client.get(f"/api/v1/credits/{agreement.id}/installments")).json()["items"]

    for inst in insts:
        resp = await client.post(
            f"/api/v1/installments/{inst['id']}/pay",
            json={"amount": str(inst["total_due"]), "method": "YAPE"},
        )
        assert resp.status_code == 200, resp.text

    # los pagos ocurrieron en otras sesiones → invalidar caché de identidad
    ag_id = agreement.id
    db.expire_all()
    agreement_row = await db.get(CreditAgreement, ag_id)
    assert agreement_row.status == AgreementStatus.PAID
    sale_row = await db.get(Sale, sale_id)
    assert sale_row.status == "COMPLETED"
    completed_moves = (
        await db.execute(
            select(InventoryMovement).where(
                InventoryMovement.reference_id == ag_id,
                InventoryMovement.movement_type == MovementType.SALE_COMPLETED,
            )
        )
    ).scalars().all()
    assert len(completed_moves) >= 1
    unpaid = (
        await db.execute(select(CreditInstallment).where(CreditInstallment.agreement_id == agreement.id, CreditInstallment.status != "PAID"))
    ).scalars().all()
    assert not unpaid


async def test_advance_payment_multiple_installments(client: httpx.AsyncClient, db):
    from app.modules.credits.domain.models import CreditInstallment, CreditPayment, InstallmentStatus

    async with db.begin():
        product = await _mk_product(db, "Pago adelantado")
        await _add_stock(db, product.id, "5")
        customer = await _mk_customer(db, limit="20000", frequent=True)

    agreement = await _make_credit(db, customer=customer, product=product, total="1500", initial="0", n=3)
    insts = sorted(agreement.installments, key=lambda i: i.number)
    ag_id = agreement.id
    ids = [i.id for i in insts]

    await _login(client, OWNER)
    amount = "750"  # cubre cuota 1 (500) completa + cuota 2 parcial (250)
    resp = await client.post(
        f"/api/v1/credits/{ag_id}/pay-multiple",
        json={"installment_ids": [str(i) for i in ids], "amount": amount, "method": "BANK_TRANSFER"},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert Decimal(body["applied_total"]) == Decimal("750")

    db.expire_all()  # los pagos ocurrieron en otra sesión
    rows = (
        await db.execute(
            select(CreditInstallment).where(CreditInstallment.agreement_id == ag_id).order_by(CreditInstallment.number)
        )
    ).scalars().all()
    assert rows[0].status == InstallmentStatus.PAID
    assert rows[1].status == InstallmentStatus.PARTIALLY_PAID
    assert Decimal(rows[1].paid_amount) == Decimal("250")
    assert rows[2].status == InstallmentStatus.PENDING

    payments = (
        await db.execute(select(CreditPayment).where(CreditPayment.agreement_id == ag_id))
    ).scalars().all()
    assert len(payments) == 2, "un CreditPayment por cuota afectada"


async def test_payment_includes_mora_amount(client: httpx.AsyncClient, db):
    async with db.begin():
        product = await _mk_product(db, "Con mora")
        await _add_stock(db, product.id, "5")
        customer = await _mk_customer(db, limit="20000", frequent=True)

    agreement = await _make_credit(db, customer=customer, product=product, total="1000", initial="0", n=2)
    inst = sorted(agreement.installments, key=lambda i: i.number)[0]
    async with db.begin():
        inst = await db.get(type(inst), inst.id)
        inst.mora_amount = Decimal("15.00")  # mora simulada ya aplicada
        inst.due_date = date.today() - timedelta(days=40)

    await _login(client, OWNER)
    detail_before = (await client.get(f"/api/v1/installments/{inst.id}")).json()
    assert Decimal(detail_before["total_due"]) == Decimal("515")

    # pago menor a deuda total (capital+mora): capital primero → remaining=0 pero no PAID
    r = await client.post(f"/api/v1/installments/{inst.id}/pay", json={"amount": "505", "method": "CASH"})
    assert r.status_code == 200
    mid = (await client.get(f"/api/v1/installments/{inst.id}")).json()
    assert mid["status"] == "PARTIALLY_PAID"
    assert Decimal(mid["remaining_amount"]) == Decimal("0")

    # completar mora restante → PAID
    r2 = await client.post(f"/api/v1/installments/{inst.id}/pay", json={"amount": "10", "method": "CASH"})
    assert r2.status_code == 200
    final = (await client.get(f"/api/v1/installments/{inst.id}")).json()
    assert final["status"] == "PAID"


# ---------------------------------------------------------------------------
# #F05-08/#F05-20 — Mora mensual
# ---------------------------------------------------------------------------


async def _overdue_setup(db, *, principal="100.00"):
    """Acuerdo con una cuota vencida el mes pasado (sin mora aún)."""
    from app.modules.credits.domain.models import (
        AgreementStatus,
        CreditAgreement,
        CreditInstallment,
        InstallmentStatus,
    )
    from app.modules.sales.domain.models import Sale

    owner = await _get_owner(db)
    customer = await _mk_customer(db, limit="20000")
    sale = Sale(
        code=f"VTA-TEST-{uuid_mod.uuid4().hex[:8].upper()}",
        customer_id=customer.id,
        sale_type="CREDIT",
        status="PARTIALLY_PAID",
        subtotal=Decimal(principal),
        discount_amount=Decimal("0"),
        total=Decimal(principal),
        currency="PEN",
        exchange_rate=Decimal("1"),
        created_by=owner.id,
    )
    db.add(sale)
    await db.flush()
    agreement = CreditAgreement(
        code=f"CRD-TEST-{uuid_mod.uuid4().hex[:8].upper()}",
        customer_id=customer.id,
        sale_id=sale.id,
        status=AgreementStatus.ACTIVE,
        total_amount=Decimal(principal),
        initial_payment=Decimal("0"),
        financed_amount=Decimal(principal),
        number_of_installments=1,
        installment_amount=Decimal(principal),
        interest_rate=Decimal("0"),
        interest_free_months=0,
        currency="PEN",
        exchange_rate=Decimal("1"),
        first_due_date=date.today() - timedelta(days=35),
        authorized_by=owner.id,
        created_by=owner.id,
    )
    db.add(agreement)
    await db.flush()
    inst = CreditInstallment(
        agreement_id=agreement.id,
        number=1,
        amount=Decimal(principal),
        due_date=date.today() - timedelta(days=35),
        paid_amount=Decimal("0"),
        remaining_amount=Decimal(principal),
        mora_amount=Decimal("0"),
        status=InstallmentStatus.PENDING,
    )
    db.add(inst)
    await db.flush()  # asigna la PK UUID antes de exponer la instancia
    return agreement, inst


def _period_offset(offset: int) -> str:
    today = date.today()
    total = today.month - 1 + offset
    year = today.year + total // 12
    month = total % 12 + 1
    return f"{year:04d}-{month:02d}"


async def test_mora_applied_to_overdue_installment(client: httpx.AsyncClient, db):
    from app.database.session import AsyncSessionLocal
    from app.modules.credits.application.service import apply_mora_for_period
    from app.modules.credits.domain.models import (
        AgreementStatus,
        CreditInstallment,
        CreditMora,
        InstallmentStatus,
    )

    async with AsyncSessionLocal() as session:
        async with session.begin():
            agreement, inst = await _overdue_setup(session, principal="100.00")
            inst_id, ag_id = inst.id, agreement.id

    async with AsyncSessionLocal() as session:
        result = await apply_mora_for_period(session, period=_period_offset(0))

    # otros tests pueden dejar cuotas vencidas propias → el agregado global
    # no es determinista; las verificaciones finas son por-cuota
    assert result["processed_installments"] >= 1

    # la instancia quedó en otra sesión cerrada → recargar desde db
    inst = await db.get(CreditInstallment, inst_id)
    assert Decimal(inst.mora_amount) == Decimal("3.00")
    assert inst.status == InstallmentStatus.OVERDUE

    mora_row = (
        await db.execute(select(CreditMora).where(CreditMora.installment_id == inst.id))
    ).scalar_one()
    assert Decimal(mora_row.principal_vencido) == Decimal("100.00")
    assert Decimal(mora_row.rate) == Decimal("0.03")
    assert mora_row.period == _period_offset(0)

    agreement_row = await db.get(type(agreement), ag_id)
    assert agreement_row.status in (AgreementStatus.OVERDUE, AgreementStatus.ACTIVE)


async def test_mora_not_capitalized(client: httpx.AsyncClient, db):
    """Mes 2 se calcula sobre capital 100, no sobre 103 (#F05-20 crítico)."""
    from app.database.session import AsyncSessionLocal
    from app.modules.credits.application.service import apply_mora_for_period
    from app.modules.credits.domain.models import CreditInstallment, CreditMora

    async with AsyncSessionLocal() as session:
        async with session.begin():
            _, inst = await _overdue_setup(session, principal="100.00")
            # vencida ANTES del inicio del período anterior para que ambos
            # períodos (-1 y 0) le apliquen mora
            inst.due_date = date.today() - timedelta(days=70)
            inst_id = inst.id
    async with AsyncSessionLocal() as session:
        r1 = await apply_mora_for_period(session, period=_period_offset(-1))
    async with AsyncSessionLocal() as session:
        r2 = await apply_mora_for_period(session, period=_period_offset(0))

    _ = r1, r2
    inst = await db.get(CreditInstallment, inst_id)
    assert Decimal(inst.mora_amount) == Decimal("6.00"), "3% sobre 100 dos veces, nunca sobre 103"

    moras = (
        await db.execute(select(CreditMora).where(CreditMora.installment_id == inst.id).order_by(CreditMora.period))
    ).scalars().all()
    assert len(moras) == 2
    assert Decimal(moras[1].principal_vencido) == Decimal("100.00"), "la base nunca incluye mora anterior"


async def test_mora_idempotent(client: httpx.AsyncClient, db):
    from app.database.session import AsyncSessionLocal
    from app.modules.credits.application.service import apply_mora_for_period
    from app.modules.credits.domain.models import CreditMora

    async with AsyncSessionLocal() as session:
        async with session.begin():
            _, inst = await _overdue_setup(session)

    period = _period_offset(0)
    async with AsyncSessionLocal() as session:
        r1 = await apply_mora_for_period(session, period=period)
    async with AsyncSessionLocal() as session:
        r2 = await apply_mora_for_period(session, period=period)

    assert r1["processed_installments"] == 1
    assert r2["processed_installments"] == 0, "segunda ejecución no duplica"

    count = (
        await db.execute(select(func.count(CreditMora.id)).where(CreditMora.installment_id == inst.id))
    ).scalar()
    assert count == 1


async def test_mora_rate_from_settings(client: httpx.AsyncClient, db, monkeypatch):
    from app.core.config import settings
    from app.database.session import AsyncSessionLocal
    from app.modules.credits.application.service import apply_mora_for_period
    from app.modules.credits.domain.models import CreditMora

    monkeypatch.setattr(settings, "MORA_RATE", 0.05)

    async with AsyncSessionLocal() as session:
        async with session.begin():
            _, inst = await _overdue_setup(session, principal="100.00")

    async with AsyncSessionLocal() as session:
        await apply_mora_for_period(session, period=_period_offset(0))

    mora_row = (
        await db.execute(select(CreditMora).where(CreditMora.installment_id == inst.id))
    ).scalar_one()
    assert Decimal(mora_row.rate) == Decimal("0.05")
    assert Decimal(mora_row.mora_amount) == Decimal("5.00")


async def test_mora_uses_decimal_not_float(client: httpx.AsyncClient, db):
    """Resultado exacto Decimal: 100 * 0.03 = 3.00 sin error de punto flotante."""
    from decimal import ROUND_HALF_UP

    from app.modules.credits.application.service import money

    computed = Decimal("100") * Decimal(str(0.03)) * Decimal("28")
    result = money(computed)
    assert isinstance(result, Decimal)
    assert result == (computed.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
    assert result == Decimal("84.00")


async def test_mora_does_not_apply_to_current_period(client: httpx.AsyncClient, db):
    """Cuota que vence DENTRO del período actual no recibe mora."""
    from app.database.session import AsyncSessionLocal
    from app.modules.credits.application.service import apply_mora_for_period
    from app.modules.credits.domain.models import CreditInstallment, InstallmentStatus

    async with AsyncSessionLocal() as session:
        async with session.begin():
            _, future_inst = await _overdue_setup(session, principal="200.00")
            future_inst.due_date = date.today() + timedelta(days=5)  # dentro del período actual
            inst_id = future_inst.id

    async with AsyncSessionLocal() as session:
        result = await apply_mora_for_period(session, period=_period_offset(0))

    assert result["processed_installments"] == 0
    future_inst = await db.get(CreditInstallment, inst_id)
    assert Decimal(future_inst.mora_amount) == Decimal("0")
    assert future_inst.status == InstallmentStatus.PENDING


# ---------------------------------------------------------------------------
# #F05-10/#F05-21 — Reprogramación (solo OWNER)
# ---------------------------------------------------------------------------


async def test_owner_can_restructure_installment(client: httpx.AsyncClient, db):
    async with db.begin():
        product = await _mk_product(db, "Reprogramar")
        await _add_stock(db, product.id, "5")
        customer = await _mk_customer(db, limit="20000", frequent=True)

    agreement = await _make_credit(db, customer=customer, product=product, total="1000", initial="0", n=2)
    inst = sorted(agreement.installments, key=lambda i: i.number)[0]
    old_due = inst.due_date

    await _login(client, OWNER)
    new_due = date.today() + timedelta(days=60)
    resp = await client.put(
        f"/api/v1/installments/{inst.id}/restructure",
        json={"new_due_date": str(new_due), "reason": "Cliente pidió postergar por emergencia"},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["due_date"] == str(new_due)
    assert body["original_due_date"] == str(old_due)


async def test_sales_cannot_restructure(client: httpx.AsyncClient, db):
    async with db.begin():
        product = await _mk_product(db, "Reprog sales")
        await _add_stock(db, product.id, "5")
        customer = await _mk_customer(db, limit="20000", frequent=True)

    agreement = await _make_credit(db, customer=customer, product=product, total="1000", initial="0", n=2)
    inst = sorted(agreement.installments, key=lambda i: i.number)[0]

    await _login(client, SALES)
    resp = await client.put(
        f"/api/v1/installments/{inst.id}/restructure",
        json={"new_due_date": str(date.today() + timedelta(days=60)), "reason": "Intento sin permiso"},
    )
    assert resp.status_code == 403


async def test_restructure_saves_original_due_date(client: httpx.AsyncClient, db):
    async with db.begin():
        product = await _mk_product(db, "Original due")
        await _add_stock(db, product.id, "5")
        customer = await _mk_customer(db, limit="20000", frequent=True)

    agreement = await _make_credit(db, customer=customer, product=product, total="1000", initial="0", n=2)
    inst = sorted(agreement.installments, key=lambda i: i.number)[0]
    original = inst.due_date

    await _login(client, OWNER)
    d1 = date.today() + timedelta(days=45)
    d2 = date.today() + timedelta(days=75)
    await client.put(
        f"/api/v1/installments/{inst.id}/restructure",
        json={"new_due_date": str(d1), "reason": "Primera reprogramación"},
    )
    await client.put(
        f"/api/v1/installments/{inst.id}/restructure",
        json={"new_due_date": str(d2), "reason": "Segunda reprogramación"},
    )

    detail = (await client.get(f"/api/v1/installments/{inst.id}")).json()
    assert detail["due_date"] == str(d2)
    assert detail["original_due_date"] == str(original), "original nunca se sobrescribe"


async def test_restructure_creates_audit_log_with_reason(client: httpx.AsyncClient, db):
    from app.modules.audit.domain.models import AuditLog

    async with db.begin():
        product = await _mk_product(db, "Audit reprog")
        await _add_stock(db, product.id, "5")
        customer = await _mk_customer(db, limit="20000", frequent=True)

    agreement = await _make_credit(db, customer=customer, product=product, total="1000", initial="0", n=2)
    inst = sorted(agreement.installments, key=lambda i: i.number)[0]
    old_due = inst.due_date

    await _login(client, OWNER)
    new_due = date.today() + timedelta(days=90)
    reason = "Postergación autorizada por gerencia"
    resp = await client.put(
        f"/api/v1/installments/{inst.id}/restructure",
        json={"new_due_date": str(new_due), "reason": reason},
    )
    assert resp.status_code == 200

    audit = (
        await db.execute(
            select(AuditLog).where(
                AuditLog.action == "RESTRUCTURE_CREDIT", AuditLog.entity_id == agreement.id
            )
        )
    ).scalars().all()
    match = [a for a in audit if a.new_values.get("installment_id") == str(inst.id)]
    assert match, "debe existir auditoría de la cuota"
    nv = match[-1].new_values
    assert nv["old_due_date"] == str(old_due)
    assert nv["new_due_date"] == str(new_due)
    assert nv["reason"] == reason


# ---------------------------------------------------------------------------
# #F05-11/#F05-22 — Entrega anticipada DELIVERED_ON_CREDIT
# ---------------------------------------------------------------------------


async def test_deliver_on_credit_changes_inventory_status(client: httpx.AsyncClient, db):
    from app.modules.inventory.domain.models import InventoryMovement, MovementType

    async with db.begin():
        product = await _mk_product(db, "Entrega anticipada")
        await _add_stock(db, product.id, "5")
        customer = await _mk_customer(db, limit="20000", frequent=True)

    agreement = await _make_credit(db, customer=customer, product=product, total="1200", initial="300", n=3)
    ag_id = agreement.id
    sale_id = agreement.sale_id

    await _login(client, OWNER)
    resp = await client.post(f"/api/v1/credits/{ag_id}/deliver")
    assert resp.status_code == 200, resp.text

    movements = (
        await db.execute(
            select(InventoryMovement).where(
                InventoryMovement.reference_type == "credit", InventoryMovement.reference_id == ag_id
            )
        )
    ).scalars().all()
    types = {m.movement_type for m in movements}
    assert MovementType.CREDIT_DELIVERY in types

    releases = (
        await db.execute(
            select(InventoryMovement).where(
                InventoryMovement.reference_id == sale_id,
                InventoryMovement.movement_type == MovementType.RELEASE_RESERVATION,
            )
        )
    ).scalars().all()
    assert len(releases) >= 1


async def test_deliver_on_credit_serial_unit_status_updated(client: httpx.AsyncClient, db):
    from app.modules.products.domain.models import SerializedUnit
    from sqlalchemy import select as sel

    async with db.begin():
        product = await _mk_product(db, "Serial entrega", serialized=True)
        unit = (
            await db.execute(sel(SerializedUnit).where(SerializedUnit.product_id == product.id))
        ).scalar_one()
        await _add_stock(db, product.id, "1")
        customer = await _mk_customer(db, limit="20000", frequent=True)

    agreement = await _make_credit(
        db, customer=customer, product=product, total="1500", initial="500", n=4,
        serialized_unit_id=unit.id,
    )
    ag_id = agreement.id

    await db.refresh(unit)
    assert unit.status == "RESERVED"

    await _login(client, OWNER)
    resp = await client.post(f"/api/v1/credits/{ag_id}/deliver")
    assert resp.status_code == 200, resp.text

    await db.refresh(unit)
    assert unit.status == "DELIVERED_ON_CREDIT"


async def test_complete_all_installments_marks_unit_sold(client: httpx.AsyncClient, db):
    from app.modules.credits.domain.models import AgreementStatus, CreditAgreement
    from app.modules.products.domain.models import SerializedUnit
    from app.modules.sales.domain.models import Sale
    from sqlalchemy import select as sel

    async with db.begin():
        product = await _mk_product(db, "Serial sold", serialized=True)
        unit = (
            await db.execute(sel(SerializedUnit).where(SerializedUnit.product_id == product.id))
        ).scalar_one()
        await _add_stock(db, product.id, "1")
        customer = await _mk_customer(db, limit="20000", frequent=True)

    agreement = await _make_credit(
        db, customer=customer, product=product, total="800", initial="200", n=3,
        serialized_unit_id=unit.id,
    )
    ag_id = agreement.id
    sale_id = agreement.sale_id

    await _login(client, OWNER)
    insts = (await client.get(f"/api/v1/credits/{ag_id}/installments")).json()["items"]
    for inst in insts:
        r = await client.post(
            f"/api/v1/installments/{inst['id']}/pay", json={"amount": str(inst["total_due"]), "method": "CASH"}
        )
        assert r.status_code == 200, r.text

    # los pagos ocurrieron en otras sesiones → invalidar caché de identidad
    db.expire_all()
    agreement_row = await db.get(CreditAgreement, ag_id)
    sale_row = await db.get(Sale, sale_id)
    await db.refresh(unit)
    assert agreement_row.status == AgreementStatus.PAID
    assert sale_row.status == "COMPLETED"
    assert unit.status == "SOLD"


async def test_delivered_on_credit_not_available_for_sale(client: httpx.AsyncClient, db):
    """Unidad entregada a crédito ya NO está disponible para otra venta."""
    from app.database.session import AsyncSessionLocal
    from app.modules.credits.application.service import deliver_on_credit
    from app.modules.products.domain.models import SerializedUnit
    from sqlalchemy import select as sel

    async with db.begin():
        product = await _mk_product(db, "No disponible", serialized=True)
        unit = (
            await db.execute(sel(SerializedUnit).where(SerializedUnit.product_id == product.id))
        ).scalar_one()
        await _add_stock(db, product.id, "1")
        customer = await _mk_customer(db, limit="20000", frequent=True)

    agreement = await _make_credit(
        db, customer=customer, product=product, total="900", initial="300", n=2,
        serialized_unit_id=unit.id,
    )

    # los servicios del módulo gestionan su propio commit (sin begin() externo)
    async with AsyncSessionLocal() as session:
        owner = await _get_owner(session)
        await deliver_on_credit(session, agreement_id=agreement.id, user=owner)

    await db.refresh(unit)
    assert unit.status != "AVAILABLE"


# ---------------------------------------------------------------------------
# Smoke de permisos/auth
# ---------------------------------------------------------------------------


async def test_credits_endpoints_require_auth(client: httpx.AsyncClient):
    assert (await client.get("/api/v1/credits")).status_code in (401, 403)
    resp = await client.post(f"/api/v1/installments/{uuid_mod.uuid4()}/pay", json={"amount": "10"})
    assert resp.status_code in (401, 403)


async def test_sales_can_view_but_not_manage(client: httpx.AsyncClient, db):
    await _login(client, SALES)
    assert (await client.get("/api/v1/credits")).status_code == 200

    async with db.begin():
        product = await _mk_product(db, "Permisos mixtos")
        await _add_stock(db, product.id, "5")
        customer = await _mk_customer(db, limit="20000", frequent=True)

    agreement = await _make_credit(db, customer=customer, product=product, total="1000", initial="0", n=2)
    inst = sorted(agreement.installments, key=lambda i: i.number)[0]

    # SALES no tiene cuotas.gestionar → 403 al pagar
    resp = await client.post(f"/api/v1/installments/{inst.id}/pay", json={"amount": "50", "method": "CASH"})
    assert resp.status_code == 403
