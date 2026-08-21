"""Seeds de créditos ficticios (#F05-16/#F05-29).

Crea 6 acuerdos que cubren todos los estados:
- 3 ACTIVE con cuotas PENDING
- 1 OVERDUE con mora calculada del período anterior
- 1 PAID (todas las cuotas pagadas)
- 1 DEFAULTED (cliente moroso, varias cuotas vencidas)

Idempotente: si ya existen acuerdos seed, completa hasta TARGET_CREDITS.
Todo inventario usa InventoryMovement(RESERVATION) y filas Reservation.
"""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.modules.cash.domain.models import CashSession
from app.modules.credits.application.service import _build_installments, add_months, current_period
from app.modules.credits.domain.models import (
    AgreementStatus,
    CreditAgreement,
    CreditInstallment,
    CreditMora,
    CreditPayment,
    InstallmentStatus,
    Reservation,
    ReservationStatus,
)
from app.modules.customers.domain.models import Customer
from app.modules.inventory.infrastructure.repository import get_stock_summary
from app.modules.products.domain.models import Product
from app.modules.sales.domain.models import Sale, SaleItem, SalePayment
from app.modules.sales.infrastructure.code import next_document_code
from app.modules.users.domain.models import User

logger = logging.getLogger("hasbun.seeds.credits")

TARGET_CREDITS = 6


def _prev_period(period: str) -> str:
    year, month = int(period[:4]), int(period[5:])
    if month == 1:
        return f"{year - 1:04d}-12"
    return f"{year:04d}-{month - 1:02d}"


async def _pick_products(db: AsyncSession, needed: int, total: Decimal) -> list[tuple[Product, Decimal]]:
    """Selecciona productos no serializados con stock para cubrir `needed` ítems."""
    products = (
        (
            await db.execute(
                select(Product).where(Product.active.is_(True), Product.is_serialized.is_(False))
            )
        )
        .scalars()
        .all()
    )
    chosen: list[tuple[Product, Decimal]] = []
    remaining = total
    for p in products:
        summary = await get_stock_summary(db, p.id)
        if summary.available < 1:
            continue
        price = min(Decimal(p.sale_price), remaining)
        if price <= 0:
            continue
        qty = Decimal("1")
        sub = money(price * qty)
        chosen.append((p, qty))
        remaining -= sub
        if len(chosen) >= needed or remaining <= 0:
            break
    return chosen


def money(v) -> Decimal:
    return Decimal(v).quantize(Decimal("0.01"))


async def _open_session(db: AsyncSession, user: User) -> CashSession | None:
    return (
        await db.execute(select(CashSession).where(CashSession.user_id == user.id, CashSession.status == "OPEN"))
    ).scalars().first()


async def _installments_of(db: AsyncSession, agreement_id: uuid.UUID) -> list[CreditInstallment]:
    """Cuotas del acuerdo ordenadas por número (consulta explícita, sin lazy-load)."""
    rows = await db.execute(
        select(CreditInstallment)
        .where(CreditInstallment.agreement_id == agreement_id)
        .order_by(CreditInstallment.number)
    )
    return list(rows.scalars().all())


async def _build_credit(
    db: AsyncSession,
    *,
    customer: Customer,
    user: User,
    total: Decimal,
    initial: Decimal,
    n_installments: int,
    free_months: int = 0,
    rate: Decimal = Decimal("0"),
    first_due_offset_months: int = 1,
) -> tuple[Sale, CreditAgreement]:
    """Construye venta a crédito + acuerdo + cuotas + reservas (sin commit)."""
    year = datetime.now(UTC).year
    exchange_rate = Decimal(str(settings.MOCK_EXCHANGE_RATE_USD_PEN))
    items = await _pick_products(db, needed=1, total=total)
    sale = Sale(
        code=await next_document_code(db, "VTA", year),
        customer_id=customer.id,
        sale_type="CREDIT",
        status="PARTIALLY_PAID",
        subtotal=total,
        discount_amount=Decimal("0.00"),
        total=total,
        currency="PEN",
        exchange_rate=exchange_rate,
        exchange_rate_source="mock",
        exchange_rate_timestamp=datetime.now(UTC),
        notes="Seed F05",
        created_by=user.id,
    )
    db.add(sale)
    await db.flush()

    financed = money(total - initial)
    for p, qty in items:
        db.add(
            SaleItem(
                sale_id=sale.id,
                product_id=p.id,
                quantity=qty,
                unit_price=money(total / len(items)),
                unit_cost=p.cost_price,
                discount_amount=Decimal("0.00"),
                subtotal=money(total / len(items)),
            )
        )
        from app.modules.inventory.application.service import reserve_stock

        await reserve_stock(
            db, product_id=p.id, qty=qty, reference_type="credit", reference_id=sale.id, created_by=user.id
        )

    agreement = CreditAgreement(
        code=await next_document_code(db, "CRD", year),
        customer_id=customer.id,
        sale_id=sale.id,
        status=AgreementStatus.ACTIVE,
        total_amount=total,
        initial_payment=initial,
        financed_amount=financed,
        number_of_installments=n_installments,
        installment_amount=money(financed / n_installments),
        interest_rate=rate,
        interest_free_months=free_months,
        currency="PEN",
        exchange_rate=exchange_rate,
        exchange_rate_source="mock",
        exchange_rate_timestamp=datetime.now(UTC),
        first_due_date=add_months(datetime.now(UTC).date(), first_due_offset_months),
        authorized_by=user.id,
        created_by=user.id,
    )
    db.add(agreement)
    await db.flush()
    # inserts directos: la relación quedaría sin cargar tras el flush y
    # accederla en async dispararía un lazy-load prohibido
    for inst_row in _build_installments(
        agreement_id=agreement.id,
        financed=financed,
        count=n_installments,
        first_due=agreement.first_due_date,
        free_months=free_months,
        rate=rate,
    ):
        db.add(inst_row)
    db.add(
        Reservation(
            product_id=items[0][0].id,
            customer_id=customer.id,
            sale_id=sale.id,
            credit_agreement_id=agreement.id,
            status=ReservationStatus.ACTIVE,
            initial_amount=initial,
            expires_at=datetime.now(UTC) + timedelta(days=settings.RESERVATION_EXPIRY_DAYS),
            created_by=user.id,
        )
    )
    if initial > 0:
        db.add(
            SalePayment(
                sale_id=sale.id,
                method="CASH",
                amount=initial,
                registered_by=user.id,
                idempotency_key=f"{agreement.code}-INITIAL",
                paid_at=datetime.now(UTC),
            )
        )
    await db.flush()
    return sale, agreement


async def _pay_installment_seed(
    db: AsyncSession, inst: CreditInstallment, agreement: CreditAgreement, amount: Decimal, user: User, key: str
) -> None:
    """Pago directo de seed: actualiza cuota y crea CreditPayment."""
    inst.paid_amount = money(inst.paid_amount + amount)
    inst.remaining_amount = money(max(Decimal("0"), inst.amount - inst.paid_amount))
    total_due = money(inst.amount + inst.mora_amount)
    inst.status = InstallmentStatus.PAID if inst.paid_amount >= total_due else InstallmentStatus.PARTIALLY_PAID
    db.add(
        CreditPayment(
            installment_id=inst.id,
            agreement_id=agreement.id,
            amount=amount,
            method="CASH",
            idempotency_key=key,
            paid_at=datetime.now(UTC),
            registered_by=user.id,
        )
    )


async def seed_credits(db: AsyncSession) -> dict[str, int]:
    total_existing = (await db.execute(select(func.count(CreditAgreement.id)))).scalar() or 0
    if total_existing >= TARGET_CREDITS:
        return {"credits_created": 0, "credits_total": int(total_existing)}

    owner = (await db.execute(select(User).where(User.email == "owner@hasbun.dev"))).scalars().first()
    if owner is None:
        return {"credits_created": 0, "error": 1}

    customers = {
        c.first_name or (c.razon_social or ""): c
        for c in (await db.execute(select(Customer))).scalars().all()
    }
    juan = customers.get("Juan")
    maria = customers.get("María") or customers.get("Maria")
    carlos = customers.get("Carlos")
    textiles = customers.get("Textiles Andinos S.A.C.")
    norte = customers.get("Distribuidora Norte E.I.R.L.")
    targets = [c for c in [juan, carlos, maria, textiles, norte] if c]
    if len(targets) < 3:
        return {"credits_created": 0, "no_customers": 1}

    created = 0
    today = datetime.now(UTC).date()

    # --- 3 ACTIVE ---
    scenarios_active: list[dict[str, Any]] = [
        dict(customer=juan or targets[0], total=Decimal("1200.00"), initial=Decimal("240.00"),
             n_installments=4, free_months=0, rate=Decimal("0")),
        dict(customer=carlos or targets[-1], total=Decimal("1800.00"), initial=Decimal("360.00"),
             n_installments=6, free_months=2, rate=Decimal("0.03")),
        dict(customer=textiles or targets[-1], total=Decimal("2500.00"), initial=Decimal("500.00"),
             n_installments=5, free_months=1, rate=Decimal("0.03")),
    ]
    built_active: list[tuple[Sale, CreditAgreement]] = []
    for sc in scenarios_active:
        cust = sc["customer"]
        if cust is None:
            continue
        built_active.append(
            await _build_credit(
                db, customer=cust, user=owner,
                total=sc["total"], initial=sc["initial"],
                n_installments=sc["n_installments"], free_months=sc["free_months"], rate=sc["rate"],
            )
        )

    # --- OVERDUE: 1 cuota vencida el mes pasado + mora ya calculada ---
    _, ag_overdue = await _build_credit(
        db, customer=maria or targets[0], user=owner,
        total=Decimal("900.00"), initial=Decimal("150.00"), n_installments=3,
        first_due_offset_months=-1,
    )
    overdue_insts = await _installments_of(db, ag_overdue.id)
    inst_overdue = overdue_insts[0]
    prev_p = _prev_period(current_period(today))
    principal = money(inst_overdue.remaining_amount)
    rate_mora = Decimal(str(settings.MORA_RATE)).quantize(Decimal("0.0001"))
    mora_amount = money(principal * rate_mora)
    db.add(
        CreditMora(
            installment_id=inst_overdue.id,
            agreement_id=ag_overdue.id,
            principal_vencido=principal,
            rate=rate_mora,
            mora_amount=mora_amount,
            period=prev_p,
            applied_at=datetime.now(UTC),
            generated_by="seed",
        )
    )
    inst_overdue.mora_amount = mora_amount
    inst_overdue.status = InstallmentStatus.OVERDUE
    ag_overdue.status = AgreementStatus.OVERDUE

    # --- PAID: todas las cuotas pagadas, venta COMPLETED ---
    sale_paid, ag_paid = await _build_credit(
        db, customer=norte or targets[-1], user=owner,
        total=Decimal("1600.00"), initial=Decimal("400.00"), n_installments=4,
        first_due_offset_months=-4,
    )
    for i, inst in enumerate(await _installments_of(db, ag_paid.id)):
        await _pay_installment_seed(db, inst, ag_paid, inst.amount, owner, key=f"{ag_paid.code}-{i}-FULL")
    ag_paid.status = AgreementStatus.PAID
    sale_paid.status = "COMPLETED"

    # --- DEFAULTED: 2 cuotas vencidas con mora en 2 períodos ---
    _, ag_defaulted = await _build_credit(
        db, customer=norte or targets[-1], user=owner,
        total=Decimal("4200.00"), initial=Decimal("800.00"), n_installments=8,
        first_due_offset_months=-2,
    )
    for inst in (await _installments_of(db, ag_defaulted.id))[:2]:
        principal_i = money(inst.remaining_amount)
        mora_i = money(principal_i * rate_mora)
        db.add(
            CreditMora(
                installment_id=inst.id,
                agreement_id=ag_defaulted.id,
                principal_vencido=principal_i,
                rate=rate_mora,
                mora_amount=mora_i,
                period=_prev_period(prev_p),
                applied_at=datetime.now(UTC),
                generated_by="seed",
            )
        )
        inst.mora_amount = mora_i
        inst.status = InstallmentStatus.OVERDUE
    ag_defaulted.status = AgreementStatus.DEFAULTED

    await db.commit()
    created = len(built_active) + 3

    final_total = (await db.execute(select(func.count(CreditAgreement.id)))).scalar() or 0
    logger.info("Seeds de créditos creados: %s (total %s)", created, final_total)
    return {"credits_created": int(created), "credits_total": int(final_total)}
