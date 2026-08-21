"""Servicio de créditos, cuotas y mora (#F05-04..#F05-11).

Invariantes financieros:
- `remaining_amount` es SOLO capital pendiente; la mora vive en `mora_amount`.
- Deuda total de cuota = remaining_amount + mora_amount.
- Mora se calcula SIEMPRE sobre capital pendiente → nunca se capitaliza (#F05-08).
- Todos los montos usan Decimal con redondeo HALF_UP a 2 decimales.

Nota sobre notificaciones: el módulo notifications llega en FASE 12; por ahora
los eventos (DEFAULTED, fallo de tarea de mora) se registran en AuditLog + logs.
"""

from __future__ import annotations

import calendar
import logging
import uuid
from typing import Any
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal

from app.core.config import settings
from app.core.exceptions import BusinessRuleError, NotFoundError, ValidationError
from app.modules.cash.domain.models import CashMovement, CashSession
from app.modules.credits.domain.models import (
    AgreementStatus,
    AuthorizationType,
    CreditAgreement,
    CreditAuthorization,
    CreditInstallment,
    CreditMora,
    CreditPayment,
    InstallmentStatus,
    Reservation,
    ReservationStatus,
)
from app.modules.credits.infrastructure import repository
from app.modules.customers.domain.models import Customer
from app.modules.inventory.application.service import release_reservation, reserve_stock
from app.modules.inventory.domain.models import MovementType
from app.modules.inventory.infrastructure.repository import add_movement, get_stock_summary
from app.modules.products.domain.models import Product, SerializedUnit
from app.modules.sales.domain.models import Sale, SaleItem, SalePayment
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger("hasbun.credits")

TWO_PLACES = Decimal("0.01")


def money(value: Decimal) -> Decimal:
    """Redondeo financiero determinista."""
    return Decimal(value).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


def add_months(d: date, months: int) -> date:
    """Suma meses recortando al último día del mes destino (31 ene + 1 → 28/29 feb)."""
    total = d.month - 1 + months
    year = d.year + total // 12
    month = total % 12 + 1
    day = min(d.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def current_period(today: date | None = None) -> str:
    t = today or date.today()
    return f"{t.year:04d}-{t.month:02d}"


def period_start(period: str) -> date:
    year, month = period.split("-")
    return date(int(year), int(month), 1)


@dataclass
class Blocker:
    type: str
    authorization: str
    message: str

    def as_dict(self) -> dict[str, str]:
        return {"type": self.type, "authorization": self.authorization, "message": self.message}


# ---------------------------------------------------------------------------
# #F05-04 — Validación pre-crédito
# ---------------------------------------------------------------------------


async def _approved_authorization_types(
    db: AsyncSession, customer_id: uuid.UUID, authorization_ids: list[uuid.UUID]
) -> set[str]:
    if not authorization_ids:
        return set()
    rows = (
        await db.execute(
            select(CreditAuthorization).where(
                CreditAuthorization.customer_id == customer_id,
                CreditAuthorization.status == "APPROVED",
                CreditAuthorization.id.in_(authorization_ids),
            )
        )
    ).scalars().all()
    return {a.type for a in rows}


async def validate_customer_for_credit(
    db: AsyncSession,
    *,
    customer_id: uuid.UUID,
    total_amount: Decimal,
    initial_payment: Decimal,
    number_of_installments: int,
    authorization_ids: list[uuid.UUID] | None = None,
) -> dict[str, Any]:
    """Verificaciones en orden; acumula bloqueos con la autorización requerida.

    Retorna {"approved": bool, "blockers": [...], "warnings": [...]} para que el
    frontend muestre qué autorización OWNER hace falta en cada caso (#F05-12).
    """
    customer = await db.get(Customer, customer_id)
    if customer is None:
        raise NotFoundError("Cliente no encontrado")

    total = money(total_amount)
    initial = money(initial_payment)
    financed = money(total - initial)
    if number_of_installments < 1:
        raise ValidationError("Número de cuotas inválido")
    if initial >= total:
        raise ValidationError("El inicial debe ser menor al total")
    if initial < 0:
        raise ValidationError("El inicial no puede ser negativo")

    auths = await _approved_authorization_types(db, customer_id, list(authorization_ids or []))
    blockers: list[Blocker] = []
    warnings: list[Blocker] = []

    # 1. MOROSIDAD ACTIVA
    if await repository.has_overdue_for_customer(db, customer_id):
        if AuthorizationType.OVERRIDE_DELINQUENCY not in auths:
            blockers.append(
                Blocker(
                    "CUSTOMER_DELINQUENT",
                    AuthorizationType.OVERRIDE_DELINQUENCY,
                    "El cliente tiene cuotas vencidas. Requiere autorización OWNER.",
                )
            )

    # 2. LÍMITE DE CRÉDITO
    pending = await repository.active_pending_total(db, customer_id)
    if pending + financed > customer.credit_limit and AuthorizationType.OVERRIDE_LIMIT not in auths:
        blockers.append(
            Blocker(
                "CREDIT_LIMIT_EXCEEDED",
                AuthorizationType.OVERRIDE_LIMIT,
                f"Excede límite: pendiente S/ {pending} + nuevo S/ {financed} > límite S/ {customer.credit_limit}",
            )
        )

    # 3. MÚLTIPLES CRÉDITOS ACTIVOS
    if await repository.has_active_agreements(db, customer_id):
        if AuthorizationType.MULTIPLE_CREDITS not in auths:
            blockers.append(
                Blocker(
                    "MULTIPLE_ACTIVE_CREDITS",
                    AuthorizationType.MULTIPLE_CREDITS,
                    "El cliente ya tiene créditos activos. Requiere autorización OWNER.",
                )
            )

    # 4. INICIAL
    if initial == 0 and not customer.is_frequent and AuthorizationType.WAIVE_INITIAL not in auths:
        blockers.append(
            Blocker(
                "INITIAL_REQUIRED",
                AuthorizationType.WAIVE_INITIAL,
                "Cliente no frecuente sin inicial. Requiere autorización OWNER.",
            )
        )
    min_initial = money(total * Decimal(str(settings.CREDIT_MIN_INITIAL_PERCENT)))
    if initial > 0 and initial < min_initial:
        warnings.append(
            Blocker(
                "LOW_INITIAL",
                "",
                f"Inicial sugerido mínimo S/ {min_initial} ({settings.CREDIT_MIN_INITIAL_PERCENT:.0%} del total)",
            )
        )

    return {
        "approved": not blockers,
        "blockers": [b.as_dict() for b in blockers],
        "warnings": [w.as_dict() for w in warnings],
    }


# ---------------------------------------------------------------------------
# #F05-05 — Creación atómica del crédito
# ---------------------------------------------------------------------------


def _build_installments(
    *, agreement_id: uuid.UUID, financed: Decimal, count: int, first_due: date,
    free_months: int, rate: Decimal,
) -> list[CreditInstallment]:
    """Genera N cuotas. Base = financed/N (última absorbe redondeo); las cuotas
    posteriores a los meses sin interés suman interés flat sobre el saldo
    financiado (#F05-18): amount + financed * rate."""
    base = money(financed / count)
    installments: list[CreditInstallment] = []
    accumulated = Decimal("0.00")
    for i in range(1, count + 1):
        due = add_months(first_due, i - 1)
        amt = base
        if i == count:
            amt = money(financed - accumulated)
        else:
            accumulated += base
        if i > free_months and rate > 0:
            amt = money(amt + financed * rate)
        installments.append(
            CreditInstallment(
                agreement_id=agreement_id,
                number=i,
                amount=amt,
                due_date=due,
                paid_amount=Decimal("0.00"),
                remaining_amount=amt,
                mora_amount=Decimal("0.00"),
                status=InstallmentStatus.PENDING,
            )
        )
    return installments


async def _vigent_price(product: Product) -> Decimal:
    now = datetime.now(UTC)
    price = Decimal(product.sale_price)
    for offer in product.offers:
        if offer.active and offer.start_at <= now <= offer.end_at:
            price = Decimal(offer.offer_price)
            break
    return price


async def create_credit_sale(db: AsyncSession, *, data, user) -> CreditAgreement:
    """Operación ATÓMICA: venta a crédito + cuotas + reservas + caja (#F05-05).

    Cualquier fallo lanza excepción y el llamador (get_db / test) hace rollback.
    """
    validation = await validate_customer_for_credit(
        db,
        customer_id=data.customer_id,
        total_amount=data.total_amount,
        initial_payment=data.initial_payment,
        number_of_installments=data.number_of_installments,
        authorization_ids=data.authorization_ids,
    )
    if not validation["approved"]:
        raise BusinessRuleError(
            "Crédito bloqueado por reglas de negocio",
            details={"blockers": validation["blockers"]},
        )

    initial = money(data.initial_payment)
    cash_session: CashSession | None = None
    if initial > 0 and data.cash_session_id:
        cash_session = await db.get(CashSession, data.cash_session_id)
        if cash_session is None or cash_session.status != "OPEN":
            raise BusinessRuleError("Sesión de caja no abierta")

    # --- Venta ---
    from app.modules.sales.infrastructure.code import next_document_code

    year = datetime.now(UTC).year
    exchange_rate = Decimal(str(settings.MOCK_EXCHANGE_RATE_USD_PEN))

    sale = Sale(
        code=await next_document_code(db, "VTA", year),
        customer_id=data.customer_id,
        sale_type="CREDIT",
        status="PARTIALLY_PAID",
        subtotal=Decimal("0.00"),
        discount_amount=Decimal("0.00"),
        total=Decimal("0.00"),
        currency=data.currency,
        exchange_rate=exchange_rate,
        exchange_rate_source="mock",
        exchange_rate_timestamp=datetime.now(UTC),
        cash_session_id=cash_session.id if cash_session else None,
        notes=data.notes,
        created_by=user.id,
    )
    db.add(sale)
    await db.flush()

    total = Decimal("0.00")
    product_rows: list[tuple[Product, Decimal]] = []
    for item in data.items:
        product = (
            await db.execute(select(Product).where(Product.id == item.product_id).with_for_update())
        ).scalar_one_or_none()
        if product is None:
            raise NotFoundError("Producto no encontrado")
        summary = await get_stock_summary(db, product.id)
        if summary.available < item.quantity:
            raise BusinessRuleError(f"Stock insuficiente {product.sku}: disponible {summary.available}")
        unit_price = await _vigent_price(product)
        sub = money(unit_price * item.quantity)
        total += sub
        db.add(
            SaleItem(
                sale_id=sale.id,
                product_id=product.id,
                serialized_unit_id=item.serialized_unit_id,
                quantity=item.quantity,
                unit_price=unit_price,
                unit_cost=product.cost_price,
                discount_amount=Decimal("0.00"),
                subtotal=sub,
            )
        )
        product_rows.append((product, item.quantity))

        # Reserva de stock (InventoryMovement RESERVATION −qty) (#F03/#F05-03)
        await reserve_stock(
            db,
            product_id=product.id,
            qty=item.quantity,
            reference_type="credit",
            reference_id=sale.id,
            created_by=user.id,
        )
        if item.serialized_unit_id:
            unit = (
                await db.execute(
                    select(SerializedUnit).where(SerializedUnit.id == item.serialized_unit_id).with_for_update()
                )
            ).scalar_one_or_none()
            if unit is None or unit.status != "AVAILABLE" or unit.product_id != product.id:
                raise BusinessRuleError("Serial no disponible")
            unit.status = "RESERVED"

    total = money(total)

    agreement = CreditAgreement(
        code=await next_document_code(db, "CRD", year),
        customer_id=data.customer_id,
        sale_id=sale.id,
        status=AgreementStatus.ACTIVE,
        total_amount=total,
        initial_payment=initial,
        financed_amount=money(total - initial),
        number_of_installments=data.number_of_installments,
        installment_amount=money(money(total - initial) / data.number_of_installments),
        interest_rate=data.interest_rate,
        interest_free_months=data.interest_free_months,
        currency=data.currency,
        exchange_rate=exchange_rate,
        exchange_rate_source="mock",
        exchange_rate_timestamp=datetime.now(UTC),
        first_due_date=data.first_due_date,
        authorized_by=user.id,
        created_by=user.id,
    )
    db.add(agreement)
    await db.flush()

    expires_at = datetime.now(UTC) + timedelta(days=settings.RESERVATION_EXPIRY_DAYS)
    for product, _qty in product_rows:
        db.add(
            Reservation(
                product_id=product.id,
                customer_id=data.customer_id,
                sale_id=sale.id,
                credit_agreement_id=agreement.id,
                status=ReservationStatus.ACTIVE,
                initial_amount=initial,
                expires_at=expires_at,
                created_by=user.id,
            )
        )

    # add() directo: la relación quedaría sin cargar tras el flush y
    # acceder a ella en async dispararía un lazy-load prohibido.
    for inst_row in _build_installments(
        agreement_id=agreement.id,
        financed=money(total - initial),
        count=data.number_of_installments,
        first_due=data.first_due_date,
        free_months=data.interest_free_months,
        rate=Decimal(data.interest_rate),
    ):
        db.add(inst_row)

    sale.subtotal = total
    sale.total = total

    # Pago inicial + caja
    if initial > 0:
        idem_base = f"{agreement.code}-INITIAL"
        existing_pay = (
            await db.execute(select(SalePayment).where(SalePayment.idempotency_key == idem_base))
        ).scalar_one_or_none()
        if existing_pay is None:
            db.add(
                SalePayment(
                    sale_id=sale.id,
                    method=data.initial_method,
                    amount=initial,
                    registered_by=user.id,
                    idempotency_key=idem_base,
                    paid_at=datetime.now(UTC),
                )
            )
            if cash_session is not None:
                db.add(
                    CashMovement(
                        session_id=cash_session.id,
                        type="CREDIT_PAYMENT",
                        amount=initial,
                        direction="IN",
                        reference_type="credit_agreement",
                        reference_id=agreement.id,
                        created_by=user.id,
                        idempotency_key=idem_base,
                    )
                )

    await db.commit()
    await _audit(
        action="CREATE_CREDIT",
        user_id=user.id,
        entity=agreement,
        new_values={
            "code": agreement.code,
            "customer_id": str(agreement.customer_id),
            "sale_id": str(sale.id),
            "total_amount": str(agreement.total_amount),
            "initial_payment": str(agreement.initial_payment),
            "financed_amount": str(agreement.financed_amount),
            "number_of_installments": agreement.number_of_installments,
            "installment_amount": str(agreement.installment_amount),
            "interest_rate": str(agreement.interest_rate),
            "interest_free_months": agreement.interest_free_months,
            "currency": agreement.currency,
            "exchange_rate": str(agreement.exchange_rate),
            "first_due_date": agreement.first_due_date.isoformat(),
        },
    )
    return await repository.get_agreement(db, agreement.id)  # type: ignore[return-value]


# ---------------------------------------------------------------------------
# #F05-06 — Pago de cuotas
# ---------------------------------------------------------------------------


async def _apply_to_installment(installment: CreditInstallment, amount: Decimal) -> None:
    """Aplica un monto a la deuda combinada (capital primero para remaining).

    PAID cuando paid_amount >= amount + mora_amount (#F05-06).
    """
    new_paid = money(installment.paid_amount + amount)
    total_due = money(installment.amount + installment.mora_amount)
    if money(total_due - installment.paid_amount) <= 0:
        raise BusinessRuleError(f"Cuota {installment.number} ya está pagada")
    if amount > money(total_due - installment.paid_amount):
        raise ValidationError(
            f"Pago excede deuda de cuota {installment.number}: adeudado {money(total_due - installment.paid_amount)}"
        )
    installment.paid_amount = new_paid
    installment.remaining_amount = money(max(Decimal("0.00"), installment.amount - new_paid))
    if new_paid >= total_due:
        installment.status = InstallmentStatus.PAID
    else:
        installment.status = InstallmentStatus.PARTIALLY_PAID


async def _cash_movement_for_payment(
    db: AsyncSession, *, session_id: uuid.UUID | None, amount: Decimal, agreement: CreditAgreement,
    key: str | None, user_id: uuid.UUID,
) -> None:
    if session_id is None or amount <= 0:
        return
    session = await db.get(CashSession, session_id)
    if session is None or session.status != "OPEN":
        raise BusinessRuleError("Sesión de caja no abierta")
    db.add(
        CashMovement(
            session_id=session_id,
            type="CREDIT_PAYMENT",
            amount=amount,
            direction="IN",
            reference_type="credit_agreement",
            reference_id=agreement.id,
            created_by=user_id,
            idempotency_key=key,
        )
    )


async def pay_installment(db: AsyncSession, *, installment_id: uuid.UUID, data, user) -> CreditPayment:
    """Pago total o parcial de una cuota, transacción atómica (#F05-06)."""
    if data.idempotency_key:
        existing = (
            await db.execute(select(CreditPayment).where(CreditPayment.idempotency_key == data.idempotency_key))
        ).scalar_one_or_none()
        if existing is not None:
            return existing

    installment = (
        await db.execute(
            select(CreditInstallment).where(CreditInstallment.id == installment_id).with_for_update()
        )
    ).scalar_one_or_none()
    if installment is None:
        raise NotFoundError("Cuota no encontrada")
    agreement = (
        await db.execute(select(CreditAgreement).where(CreditAgreement.id == installment.agreement_id).with_for_update())
    ).scalar_one()
    if agreement.status in (AgreementStatus.PAID, AgreementStatus.CANCELLED):
        raise BusinessRuleError("El crédito no admite pagos en su estado actual")

    amount = money(data.amount)
    await _apply_to_installment(installment, amount)

    payment = CreditPayment(
        installment_id=installment.id,
        agreement_id=agreement.id,
        amount=amount,
        method=data.method,
        method_detail=data.method_detail,
        reference=data.reference,
        cash_session_id=data.cash_session_id,
        idempotency_key=data.idempotency_key,
        paid_at=datetime.now(UTC),
        registered_by=user.id,
    )
    db.add(payment)

    await _cash_movement_for_payment(
        db,
        session_id=data.cash_session_id,
        amount=amount,
        agreement=agreement,
        key=f"{data.idempotency_key}-CASH" if data.idempotency_key else None,
        user_id=user.id,
    )

    completed = await _finalize_if_completed(db, agreement=agreement, user_id=user.id)
    await db.commit()

    await _audit(
        action="CREDIT_PAYMENT",
        user_id=user.id,
        entity=agreement,
        new_values={
            "code": agreement.code,
            "installment_id": str(installment.id),
            "number": installment.number,
            "amount": str(amount),
            "method": data.method,
            "credit_completed": completed,
        },
    )
    if completed:
        await _audit(action="CREDIT_COMPLETED", user_id=user.id, entity=agreement, new_values={"code": agreement.code})
    return payment


async def _finalize_if_completed(db: AsyncSession, *, agreement: CreditAgreement, user_id: uuid.UUID) -> bool:
    """Si todas las cuotas están PAID: acuerdo PAID, venta COMPLETED, inventario SOLD (#F05-06 paso 9)."""
    unpaid = [i for i in agreement.installments if i.status != InstallmentStatus.PAID]
    if unpaid:
        # refrescar estado del acuerdo según cuotas
        if any(i.status == InstallmentStatus.OVERDUE for i in agreement.installments):
            if agreement.status == AgreementStatus.ACTIVE:
                agreement.status = AgreementStatus.OVERDUE
        return False

    agreement.status = AgreementStatus.PAID
    sale = await db.get(Sale, agreement.sale_id)
    if sale is not None:
        sale.status = "COMPLETED"
        for item in sale.items:
            await add_movement(
                db,
                product_id=item.product_id,
                quantity=-item.quantity,
                movement_type=MovementType.SALE_COMPLETED,
                reference_type="credit",
                reference_id=agreement.id,
                created_by=user_id,
                notes=f"Crédito {agreement.code} completado",
            )
            if item.serialized_unit_id:
                unit = (
                    await db.execute(
                        select(SerializedUnit).where(SerializedUnit.id == item.serialized_unit_id).with_for_update()
                    )
                ).scalar_one_or_none()
                if unit is not None:
                    unit.status = "SOLD"
        reservations = (
            await db.execute(
                select(Reservation).where(Reservation.sale_id == sale.id, Reservation.status == ReservationStatus.ACTIVE)
            )
        ).scalars().all()
        for r in reservations:
            r.status = ReservationStatus.CONVERTED_TO_SALE
    return True


# ---------------------------------------------------------------------------
# #F05-07 — Pago adelantado de múltiples cuotas
# ---------------------------------------------------------------------------


async def pay_multiple_installments(db: AsyncSession, *, agreement_id: uuid.UUID, data, user) -> dict[str, Any]:
    """Distribuye `amount` entre las cuotas seleccionadas en orden cronológico.

    Un CreditPayment por cuota afectada (trazabilidad completa); nunca altera
    pagos anteriores (#F05-07).
    """
    if data.idempotency_key:
        existing = (
            await db.execute(select(CreditPayment).where(CreditPayment.idempotency_key == f"{data.idempotency_key}-1"))
        ).scalar_one_or_none()
        if existing is not None:
            return {"payments": [existing], "applied_total": existing.amount}

    agreement = (
        await db.execute(select(CreditAgreement).where(CreditAgreement.id == agreement_id).with_for_update())
    ).scalar_one_or_none()
    if agreement is None:
        raise NotFoundError("Crédito no encontrado")
    if agreement.status in (AgreementStatus.PAID, AgreementStatus.CANCELLED):
        raise BusinessRuleError("El crédito no admite pagos en su estado actual")

    requested = (
        await db.execute(
            select(CreditInstallment)
            .where(CreditInstallment.id.in_([str(i) for i in data.installment_ids]))
            .with_for_update()
        )
    ).scalars().all()
    by_id = {str(i.id): i for i in requested}
    missing = [str(i) for i in data.installment_ids if str(i) not in by_id]
    if missing:
        raise NotFoundError("Cuota no encontrada")

    ordered = sorted(requested, key=lambda i: (i.due_date, i.number))
    left = money(data.amount)
    applied_total = Decimal("0.00")
    payments: list[CreditPayment] = []

    for inst in ordered:
        if left <= 0:
            break
        owed = money(inst.amount + inst.mora_amount - inst.paid_amount)
        if owed <= 0:
            continue
        to_pay = min(left, owed)
        await _apply_to_installment(inst, to_pay)
        payment = CreditPayment(
            installment_id=inst.id,
            agreement_id=agreement.id,
            amount=to_pay,
            method=data.method,
            reference=data.reference,
            cash_session_id=data.cash_session_id,
            idempotency_key=f"{data.idempotency_key}-{inst.number}" if data.idempotency_key else None,
            paid_at=datetime.now(UTC),
            registered_by=user.id,
        )
        db.add(payment)
        payments.append(payment)
        left -= to_pay
        applied_total += to_pay

    if not payments:
        raise ValidationError("Ninguna cuota seleccionada tiene deuda pendiente")

    await _cash_movement_for_payment(
        db,
        session_id=data.cash_session_id,
        amount=applied_total,
        agreement=agreement,
        key=f"{data.idempotency_key}-CASH" if data.idempotency_key else None,
        user_id=user.id,
    )

    completed = await _finalize_if_completed(db, agreement=agreement, user_id=user.id)
    await db.commit()
    await _audit(
        action="CREDIT_PAYMENT_MULTIPLE",
        user_id=user.id,
        entity=agreement,
        new_values={
            "code": agreement.code,
            "installments": [p.installment_id.__str__() for p in payments],
            "applied_total": str(applied_total),
            "credit_completed": completed,
        },
    )
    return {"payments": payments, "applied_total": applied_total}


# ---------------------------------------------------------------------------
# #F05-08 — Mora mensual
# ---------------------------------------------------------------------------


async def apply_mora_for_period(
    db: AsyncSession, *, period: str | None = None, generated_by: str = "system"
) -> dict[str, Any]:
    """Aplica mora del período a cuotas vencidas. IDEMPOTENTE (#F05-08).

    - Solo cuotas PENDING/PARTIALLY_PAID/OVERDUE con due_date < inicio del período.
    - UNIQUE (installment_id, period) evita doble mora.
    - Base = remaining_amount (capital puro) → nunca capitaliza mora.
    - Tasa desde settings (default 3%).
    """
    period = period or current_period()
    start = period_start(period)
    rate = Decimal(str(settings.MORA_RATE)).quantize(Decimal("0.0001"))
    now = datetime.now(UTC)

    already = set(
        (
            await db.execute(select(CreditMora.installment_id).where(CreditMora.period == period))
        ).scalars().all()
    )

    overdue_rows = (
        await db.execute(
            select(CreditInstallment).where(
                CreditInstallment.status.in_([InstallmentStatus.PENDING, InstallmentStatus.PARTIALLY_PAID, InstallmentStatus.OVERDUE]),
                CreditInstallment.due_date < start,
            )
        )
    ).scalars().all()

    processed = 0
    total_mora = Decimal("0.00")
    affected_agreements: set[uuid.UUID] = set()

    for inst in overdue_rows:
        affected_agreements.add(inst.agreement_id)
        if inst.id in already:
            continue
        principal = money(inst.remaining_amount)
        if principal <= 0:
            continue  # capital cancelado: no genera nueva mora
        mora = money(principal * rate)
        db.add(
            CreditMora(
                installment_id=inst.id,
                agreement_id=inst.agreement_id,
                principal_vencido=principal,
                rate=rate,
                mora_amount=mora,
                period=period,
                applied_at=now,
                generated_by=generated_by,
            )
        )
        inst.mora_amount = money(inst.mora_amount + mora)
        if inst.status != InstallmentStatus.OVERDUE:
            inst.status = InstallmentStatus.OVERDUE
        processed += 1
        total_mora += mora

    await db.flush()

    # Estados de acuerdo + umbral DEFAULTED
    defaulted = 0
    for agreement_id in affected_agreements:
        agreement = await repository.get_agreement(db, agreement_id)
        if agreement is None or agreement.status in (AgreementStatus.PAID, AgreementStatus.CANCELLED):
            continue
        overdue_count = sum(1 for i in agreement.installments if i.status == InstallmentStatus.OVERDUE)
        if overdue_count == 0:
            if agreement.status == AgreementStatus.OVERDUE:
                agreement.status = AgreementStatus.ACTIVE
        elif overdue_count >= settings.CREDIT_DEFAULTED_MIN_OVERDUE and agreement.status != AgreementStatus.DEFAULTED:
            agreement.status = AgreementStatus.DEFAULTED
            defaulted += 1
            await _audit(
                action="CREDIT_DEFAULTED_NOTIFY_OWNER",
                user_id=None,
                entity=agreement,
                new_values={
                    "code": agreement.code,
                    "overdue_installments": overdue_count,
                    "note": "Notificación formal a OWNER llega con módulo notifications (FASE 12)",
                },
            )
        elif agreement.status == AgreementStatus.ACTIVE:
            agreement.status = AgreementStatus.OVERDUE

    await db.commit()
    result = {
        "period": period,
        "processed_installments": processed,
        "mora_total": str(money(total_mora)),
        "defaulted_agreements": defaulted,
    }
    logger.info("Mora aplicada: %s", result)
    return result


# ---------------------------------------------------------------------------
# #F05-10 — Reprogramación de cuotas
# ---------------------------------------------------------------------------


async def restructure_installment(
    db: AsyncSession, *, installment_id: uuid.UUID, new_due_date: date, reason: str, owner_user
) -> CreditInstallment:
    """Reprogramación SOLO OWNER (router garantiza permiso cuotas.gestionar).

    Guarda original_due_date una única vez y registra motivo/usuario/timestamp.
    Si pasa de OVERDUE a fecha futura vuelve a PENDING (la mora ya generada NO se borra).
    """
    installment = (
        await db.execute(select(CreditInstallment).where(CreditInstallment.id == installment_id).with_for_update())
    ).scalar_one_or_none()
    if installment is None:
        raise NotFoundError("Cuota no encontrada")
    if installment.status == InstallmentStatus.PAID:
        raise BusinessRuleError("No se puede reprogramar una cuota pagada")
    old_due = installment.due_date

    if installment.original_due_date is None:
        installment.original_due_date = old_due  # nunca se sobrescribe
    installment.due_date = new_due_date
    installment.restructured_at = datetime.now(UTC)
    installment.restructured_by = owner_user.id
    installment.restructure_reason = reason

    today = date.today()
    if installment.status == InstallmentStatus.OVERDUE and new_due_date >= today:
        installment.status = InstallmentStatus.PENDING

    agreement = await repository.get_agreement(db, installment.agreement_id)
    if agreement is not None and agreement.status == AgreementStatus.OVERDUE:
        if all(i.status != InstallmentStatus.OVERDUE for i in agreement.installments):
            agreement.status = AgreementStatus.ACTIVE

    await db.commit()
    await _audit(
        action="RESTRUCTURE_CREDIT",
        user_id=owner_user.id,
        entity=agreement,
        new_values={
            "code": agreement.code if agreement else None,
            "installment_id": str(installment.id),
            "old_due_date": old_due.isoformat(),
            "new_due_date": new_due_date.isoformat(),
            "reason": reason,
        },
    )
    return installment


# ---------------------------------------------------------------------------
# #F05-11 — Entrega anticipada DELIVERED_ON_CREDIT
# ---------------------------------------------------------------------------


async def deliver_on_credit(db: AsyncSession, *, agreement_id: uuid.UUID, user) -> CreditAgreement:
    """Entrega del bien antes de pagar todo (#F05-11).

    Por cada ítem: libera la reserva y registra CREDIT_DELIVERY (el stock pasa
    del bucket `reserved` al bucket `on_credit` sin cambiar disponibilidad).
    Serializados pasan a DELIVERED_ON_CREDIT y las reservas a CONVERTED_TO_CREDIT.
    """
    agreement = (
        await db.execute(select(CreditAgreement).where(CreditAgreement.id == agreement_id).with_for_update())
    ).scalar_one_or_none()
    if agreement is None:
        raise NotFoundError("Crédito no encontrado")
    if agreement.status not in (AgreementStatus.ACTIVE, AgreementStatus.APPROVED):
        raise BusinessRuleError(f"No se puede entregar en estado {agreement.status}")

    sale = await db.get(Sale, agreement.sale_id)
    if sale is None:
        raise NotFoundError("Venta del crédito no encontrada")

    delivered_any = False
    for item in sale.items:
        await release_reservation(
            db,
            product_id=item.product_id,
            qty=item.quantity,
            reference_id=sale.id,
            created_by=user.id,
        )
        await add_movement(
            db,
            product_id=item.product_id,
            quantity=-item.quantity,
            movement_type=MovementType.CREDIT_DELIVERY,
            reference_type="credit",
            reference_id=agreement.id,
            created_by=user.id,
            notes=f"Entrega anticipada crédito {agreement.code}",
        )
        if item.serialized_unit_id:
            unit = (
                await db.execute(
                    select(SerializedUnit).where(SerializedUnit.id == item.serialized_unit_id).with_for_update()
                )
            ).scalar_one_or_none()
            if unit is not None:
                unit.status = "DELIVERED_ON_CREDIT"
        reservation = (
            await db.execute(
                select(Reservation).where(
                    Reservation.sale_id == sale.id,
                    Reservation.product_id == item.product_id,
                    Reservation.status == ReservationStatus.ACTIVE,
                )
            )
        ).scalars().first()
        if reservation is not None:
            reservation.status = ReservationStatus.CONVERTED_TO_CREDIT
        delivered_any = True

    if not delivered_any:
        raise BusinessRuleError("La venta no tiene ítems para entregar")

    agreement.status = AgreementStatus.ACTIVE
    await db.commit()
    await _audit(
        action="DELIVER_ON_CREDIT",
        user_id=user.id,
        entity=agreement,
        new_values={"code": agreement.code, "delivered_items": len(sale.items)},
    )
    return await repository.get_agreement(db, agreement.id)  # type: ignore[return-value]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _audit(*, action: str, user_id: uuid.UUID | None, entity: CreditAgreement | None, new_values: dict) -> None:
    """Auditoría post-commit: nunca interrumpe el flujo."""
    from app.modules.audit.application.service import log

    await log(
        action=action,
        module="credits",
        user_id=user_id,
        entity_type="CreditAgreement" if entity is not None else None,
        entity_id=entity.id if entity is not None else None,
        new_values=new_values,
    )


async def customer_credits(db: AsyncSession, customer_id: uuid.UUID) -> list[CreditAgreement]:
    agreements, _ = await repository.list_agreements(db, customer_id=customer_id, per_page=100)
    return agreements
