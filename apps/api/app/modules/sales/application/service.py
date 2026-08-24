"""Servicio ventas atómico (#F04-08)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal

from app.core.config import settings
from app.core.exceptions import BusinessRuleError, NotFoundError, ValidationError
from app.modules.audit.application.service import log
from app.modules.cash.infrastructure.repository import get_session as get_cash_session
from app.modules.inventory.application.service import confirm_sale
from app.modules.products.domain.models import Product, SerializedUnit
from app.modules.sales.domain.models import DiscountAuthorization, Sale, SaleItem, SalePayment
from app.modules.sales.infrastructure.code import next_sale_code
from app.modules.sales.infrastructure.repository import get_by_idempotency
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


async def request_discount(db: AsyncSession, *, data, requested_by):
    if data.type == "PERCENTAGE" and (data.percentage is None or data.percentage <= 0 or data.percentage > 1):
        raise ValidationError("Porcentaje inválido")
    if data.type == "FIXED_AMOUNT" and (data.fixed_amount is None or data.fixed_amount < 0):
        raise ValidationError("Monto inválido")
    auth = DiscountAuthorization(
        sale_id=data.sale_id, type=data.type, percentage=data.percentage, fixed_amount=data.fixed_amount,
        reason=data.reason, requested_by=requested_by.id, status="PENDING", requested_at=datetime.now(UTC)
    )
    db.add(auth)
    await db.commit()
    await db.refresh(auth)
    await log(action="REQUEST_DISCOUNT", module="sales", user_id=requested_by.id, entity_type="DiscountAuthorization", entity_id=auth.id, new_values={"type": auth.type})
    try:
        from app.modules.notifications.application.service import notify_roles

        await notify_roles(
            db,
            role_codes=["OWNER"],
            type_="discount_request",
            title="Solicitud de descuento",
            message=f"{requested_by.email} solicita descuento {auth.type} para venta {data.sale_id}",
            priority="HIGH", related_type="DiscountAuthorization", related_id=auth.id,
        )
        await db.commit()
    except Exception:  # noqa: BLE001 — la notificación nunca rompe el flujo
        await db.rollback()
    return auth


async def approve_discount(db: AsyncSession, *, auth_id: uuid.UUID, approved_by):
    auth = await db.get(DiscountAuthorization, auth_id)
    if not auth or auth.status != "PENDING":
        raise NotFoundError("Solicitud no encontrada")
    auth.status = "APPROVED"
    auth.approved_by = approved_by.id
    auth.reviewed_at = datetime.now(UTC)
    await db.commit()
    await log(action="APPROVE_DISCOUNT", module="sales", user_id=approved_by.id, entity_type="DiscountAuthorization", entity_id=auth.id, new_values={"approved_by": str(approved_by.id)})
    try:
        from app.modules.notifications.application.service import create_notification

        await create_notification(
            db, user_id=auth.requested_by, type_="discount_approved",
            title="Descuento aprobado",
            message=f"Tu solicitud de descuento fue APROBADA por {approved_by.email}",
            priority="MEDIUM", related_type="DiscountAuthorization", related_id=auth.id,
        )
        await db.commit()
    except Exception:  # noqa: BLE001 — la notificación nunca rompe el flujo
        await db.rollback()
    return auth


async def reject_discount(db: AsyncSession, *, auth_id: uuid.UUID, rejected_by):
    auth = await db.get(DiscountAuthorization, auth_id)
    if not auth or auth.status != "PENDING":
        raise NotFoundError("Solicitud no encontrada")
    auth.status = "REJECTED"
    auth.approved_by = rejected_by.id
    auth.reviewed_at = datetime.now(UTC)
    await db.commit()
    await log(action="REJECT_DISCOUNT", module="sales", user_id=rejected_by.id, entity_type="DiscountAuthorization", entity_id=auth.id, new_values={})
    try:
        from app.modules.notifications.application.service import create_notification

        await create_notification(
            db, user_id=auth.requested_by, type_="discount_rejected",
            title="Descuento rechazado",
            message=f"Tu solicitud de descuento fue RECHAZADA por {rejected_by.email}",
            priority="MEDIUM", related_type="DiscountAuthorization", related_id=auth.id,
        )
        await db.commit()
    except Exception:  # noqa: BLE001 — la notificación nunca rompe el flujo
        await db.rollback()
    return auth


async def create_cash_sale(db: AsyncSession, *, data, user, commit: bool = True):
    # idempotencia
    if data.idempotency_key:
        existing = await get_by_idempotency(db, data.idempotency_key)
        if existing:
            return existing

    # sesión caja
    if not data.cash_session_id:
        raise ValidationError("Se requiere sesión de caja")
    cash_session = await get_cash_session(db, data.cash_session_id)
    if not cash_session or cash_session.status != "OPEN":
        raise BusinessRuleError("Sesión de caja no abierta")

    # descuento auth
    discount_amount = Decimal("0")
    if data.discount_authorization_id:
        auth = await db.get(DiscountAuthorization, data.discount_authorization_id)
        if not auth or auth.status != "APPROVED":
            raise BusinessRuleError("Descuento no aprobado")

    # congela tipo cambio
    exchange_rate = Decimal(str(settings.MOCK_EXCHANGE_RATE_USD_PEN))
    exchange_source = "mock"

    sale = Sale(
        code=await next_sale_code(db),
        customer_id=data.customer_id,
        sale_type="CASH",
        status="DRAFT",
        currency=data.currency,
        exchange_rate=exchange_rate,
        exchange_rate_source=exchange_source,
        exchange_rate_timestamp=datetime.now(UTC),
        discount_authorization_id=data.discount_authorization_id,
        cash_session_id=data.cash_session_id,
        idempotency_key=data.idempotency_key,
        notes=data.notes,
        created_by=user.id,
        subtotal=Decimal("0"),
        discount_amount=discount_amount,
        total=Decimal("0"),
    )
    db.add(sale)
    await db.flush()

    subtotal = Decimal("0")
    for item in data.items:
        product = (await db.execute(select(Product).where(Product.id == item.product_id).with_for_update())).scalar_one_or_none()
        if not product:
            raise NotFoundError("Producto no encontrado")
        # stock check
        from app.modules.inventory.infrastructure.repository import get_stock_summary
        summary = await get_stock_summary(db, product.id)
        if summary.available < item.quantity:
            raise BusinessRuleError(f"Stock insuficiente {product.sku}: disponible {summary.available}")
        # serializado
        if product.is_serialized:
            if not item.serialized_unit_id:
                raise ValidationError(f"Producto {product.sku} requiere serial")
            unit = (await db.execute(select(SerializedUnit).where(SerializedUnit.id == item.serialized_unit_id).with_for_update())).scalar_one_or_none()
            if not unit or unit.status != "AVAILABLE" or unit.product_id != product.id:
                raise BusinessRuleError("Serial no disponible")
            unit.status = "SOLD"
        # precio: override congelado (conversión de cotización) o precio vigente
        unit_price_override = getattr(item, "unit_price", None)
        if unit_price_override is not None:
            unit_price = Decimal(str(unit_price_override))
        else:
            # precio vigente (get_current_price simplificado: sale_price)
            unit_price = product.sale_price
            # oferta activa?
            now = datetime.now(UTC)
            for o in product.offers:
                if o.active and o.start_at <= now <= o.end_at:
                    unit_price = o.offer_price
                    break
        item_sub = (unit_price * item.quantity - item.discount_amount).quantize(Decimal("0.01"))
        subtotal += item_sub
        sale_item = SaleItem(
            sale_id=sale.id, product_id=product.id, serialized_unit_id=item.serialized_unit_id,
            quantity=item.quantity, unit_price=unit_price, unit_cost=product.cost_price,
            discount_amount=item.discount_amount, subtotal=item_sub
        )
        db.add(sale_item)
        # inventory movement
        await confirm_sale(db, product_id=product.id, qty=item.quantity, reference_id=sale.id, created_by=user.id, unit_cost=product.cost_price)

    # descuento global
    if data.discount_authorization_id:
        auth = await db.get(DiscountAuthorization, data.discount_authorization_id)
        if auth is not None:
            if auth.type == "PERCENTAGE":
                discount_amount = (subtotal * (auth.percentage or Decimal("0"))).quantize(Decimal("0.01"))
            else:
                discount_amount = auth.fixed_amount or Decimal("0")
            if discount_amount > subtotal:
                raise ValidationError("Descuento mayor al subtotal")

    sale.subtotal = subtotal.quantize(Decimal("0.01"))
    sale.discount_amount = discount_amount.quantize(Decimal("0.01"))
    sale.total = (subtotal - discount_amount).quantize(Decimal("0.01"))

    # pago
    pay_total = Decimal("0")
    for p in data.payments or []:
        amt = Decimal(str(p.get("amount", 0)))
        pay_total += amt
        sp = SalePayment(sale_id=sale.id, method=p.get("method", "CASH"), amount=amt, reference=p.get("reference"), registered_by=user.id, idempotency_key=p.get("idempotency_key"), paid_at=datetime.now(UTC))
        db.add(sp)
    if pay_total < sale.total:
        # permite pagos parciales? para CASH exige total
        if sale.sale_type == "CASH" and pay_total < sale.total:
            raise BusinessRuleError(f"Pago insuficiente: {pay_total} < {sale.total}")

    sale.status = "PAID"

    # movimiento caja
    from app.modules.cash.domain.models import CashMovement
    db.add(CashMovement(session_id=cash_session.id, type="SALE_INCOME", amount=sale.total, direction="IN", reference_type="sale", reference_id=sale.id, created_by=user.id, idempotency_key=data.idempotency_key))

    if not commit:
        # conversión de cotización: el llamador hace el commit único (#F06-03)
        return sale

    await db.commit()
    fresh_sale = await db.get(Sale, sale.id)
    sale = fresh_sale if fresh_sale is not None else sale
    await log(action="CREATE_SALE", module="sales", user_id=user.id, entity_type="Sale", entity_id=sale.id, new_values={"code": sale.code, "total": str(sale.total)})
    # Tras el commit: WhatsApp NEW_SALE + notificaciones internas (#F06-10).
    # Nunca bloquea el flujo: los fallos solo se loguean.
    try:
        await notify_new_sale(sale.id)
    except Exception:  # noqa: BLE001
        import logging

        logging.getLogger("hasbun.sales").exception("Fallo notificación NEW_SALE venta %s", sale.code)
    return sale


async def notify_new_sale(sale_id: uuid.UUID) -> None:
    """Encola WhatsApp NEW_SALE al cliente + notificación interna OWNER/SALES.

    Se ejecuta SIEMPRE después del commit de la venta (REQUIREMENTS §23.4).
    Usa sesiones propias para no tocar la transacción original.
    """
    from app.database.session import AsyncSessionLocal
    from app.modules.customers.domain.models import Customer
    from app.modules.notifications.application.service import notify_roles
    from app.modules.sales.domain.models import SaleItem
    from app.modules.whatsapp.application.service import send_event
    from sqlalchemy.orm import selectinload

    async with AsyncSessionLocal() as db:
        sale = (
            await db.execute(
                select(Sale)
                .where(Sale.id == sale_id)
                .options(selectinload(Sale.items).selectinload(SaleItem.product))
            )
        ).scalar_one_or_none()
        if sale is None:
            return
        customer = await db.get(Customer, sale.customer_id)
        recipient = (customer.phone_whatsapp or customer.phone) if customer else None
        name = (
            customer.razon_social
            or " ".join(filter(None, [customer.first_name or "", customer.last_name or ""]))
            or None
        ) if customer else None
        product_list = ", ".join(
            (item.product.name if item.product else "producto") for item in sale.items
        )
        await send_event(
            db,
            event_type="NEW_SALE",
            recipient=recipient,
            variables={
                "customer_name": name,
                "sale_code": sale.code,
                "total": str(sale.total),
                "product_list": product_list,
            },
            idempotency_key=f"new-sale:{sale.id}",
        )
        await db.commit()

    async with AsyncSessionLocal() as ndb:
        sale2 = await ndb.get(Sale, sale_id)
        if sale2 is None:
            return
        await notify_roles(
            ndb,
            role_codes=["OWNER", "SALES"],
            type_="new_sale",
            title="Nueva venta",
            message=f"Venta {sale2.code} registrada por {sale2.currency} {sale2.total}",
            priority="LOW",
            related_type="sale",
            related_id=sale2.id,
        )
        await ndb.commit()


async def cancel_sale(db: AsyncSession, *, sale_id: uuid.UUID, reason: str, user):
    sale = await db.get(Sale, sale_id)
    if not sale or sale.status not in ("DRAFT", "PAID", "PENDING_PAYMENT"):
        raise BusinessRuleError("No se puede cancelar")
    sale.status = "CANCELLED"
    await db.commit()
    await log(action="CANCEL_SALE", module="sales", user_id=user.id, entity_type="Sale", entity_id=sale.id, new_values={"reason": reason})
    return sale
