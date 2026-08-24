"""Servicio de cotizaciones (#F06-02/#F06-03/#F06-04).

Flujo de estados: DRAFT → SENT → VIEWED → ACCEPTED/REJECTED → CONVERTED,
con EXPIRED automático por tarea Celery (#F06-04).

La conversión a venta (#F06-03) es ATÓMICA: reutiliza los servicios de
venta contado/crédito con `commit=False` y precios congelados de la
cotización; si cualquier paso falla hay rollback total y la cotización
NO queda marcada CONVERTED.
"""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from types import SimpleNamespace
from typing import Any

from app.core.config import settings
from app.core.exceptions import BusinessRuleError, ConflictError, NotFoundError, ValidationError
from app.modules.audit.application.service import log as audit_log
from app.modules.customers.domain.models import Customer
from app.modules.products.domain.models import Product
from app.modules.quotes.domain.models import Quote, QuoteItem, QuoteStatus
from app.modules.quotes.infrastructure import repository
from app.modules.sales.domain.models import Sale
from app.modules.users.domain.models import User
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger("hasbun.quotes")


def _customer_name(customer: Customer | None) -> str | None:
    if customer is None:
        return None
    return (
        customer.razon_social
        or " ".join(filter(None, [customer.first_name, customer.last_name]))
        or None
    )


def _whatsapp_recipient(customer: Customer | None) -> str | None:
    if customer is None:
        return None
    return customer.phone_whatsapp or customer.phone or None


async def _audit(*, action: str, user_id: uuid.UUID | None, quote: Quote, extra: dict[str, Any] | None = None) -> None:
    values: dict[str, Any] = {"code": quote.code, "status": quote.status, "total": str(quote.total)}
    if extra:
        values.update(extra)
    await audit_log(
        action=action,
        module="quotes",
        user_id=user_id,
        entity_type="Quote",
        entity_id=quote.id,
        new_values=values,
    )


async def _vigent_price(product: Product) -> Decimal:
    """Precio vigente al crear la cotización (oferta activa > sale_price)."""
    now = datetime.now(UTC)
    price = Decimal(str(product.sale_price))
    for offer in product.offers:
        if offer.active and offer.start_at <= now <= offer.end_at:
            price = Decimal(str(offer.offer_price))
            break
    return price


# ---------------------------------------------------------------------------
# #F06-02 — CRUD y flujo de estados
# ---------------------------------------------------------------------------


async def create_quote(db: AsyncSession, *, data, user: User) -> Quote:
    """Crea Quote(DRAFT) con precios congelados (#F06-01/#F06-02)."""
    if data.valid_until < date.today():
        raise ValidationError("valid_until debe ser hoy o futuro")
    customer = await db.get(Customer, data.customer_id)
    if customer is None:
        raise NotFoundError("Cliente no encontrado")

    exchange_rate = Decimal(str(settings.MOCK_EXCHANGE_RATE_USD_PEN))
    quote = Quote(
        code=await repository.next_quote_code(db),
        customer_id=data.customer_id,
        status=QuoteStatus.DRAFT,
        subtotal=Decimal("0.00"),
        discount_amount=Decimal("0.00"),
        total=Decimal("0.00"),
        currency=data.currency,
        exchange_rate=exchange_rate,
        exchange_rate_source="mock",
        exchange_rate_timestamp=datetime.now(UTC),
        valid_until=data.valid_until,
        notes=data.notes,
        created_by=user.id,
    )
    db.add(quote)
    await db.flush()

    pairs: list[tuple[Decimal, Decimal, Decimal]] = []
    for item in data.items:
        product = await db.get(Product, item.product_id)
        if product is None:
            raise NotFoundError(f"Producto {item.product_id} no encontrado")
        unit_price = (
            Decimal(str(item.unit_price)) if item.unit_price is not None else await _vigent_price(product)
        )
        sub = ((unit_price * item.quantity) - item.discount_amount).quantize(Decimal("0.01"))
        db.add(
            QuoteItem(
                quote_id=quote.id,
                product_id=product.id,
                quantity=item.quantity,
                unit_price=unit_price,
                discount_amount=item.discount_amount,
                subtotal=sub,
                notes=item.notes,
            )
        )
        pairs.append((unit_price, item.quantity, item.discount_amount))

    subtotal, total = repository.compute_totals(pairs)
    quote.subtotal = subtotal
    quote.total = total
    quote.discount_amount = (subtotal - total).quantize(Decimal("0.01"))
    await db.commit()
    await _audit(action="CREATE_QUOTE", user_id=user.id, quote=quote)
    fresh = await repository.get_quote(db, quote.id)
    assert fresh is not None
    return fresh


async def update_quote(db: AsyncSession, *, quote_id: uuid.UUID, data, user: User) -> Quote:
    """Edita una cotización SOLO si está en DRAFT."""
    quote = await repository.get_quote(db, quote_id)
    if quote is None:
        raise NotFoundError("Cotización no encontrada")
    if quote.status != QuoteStatus.DRAFT:
        raise BusinessRuleError("Solo las cotizaciones DRAFT pueden editarse")
    if data.valid_until is not None:
        quote.valid_until = data.valid_until
    if data.notes is not None:
        quote.notes = data.notes
    if data.items is not None:
        for old in list(quote.items):
            await db.delete(old)
        await db.flush()
        pairs = []
        for item in data.items:
            product = await db.get(Product, item.product_id)
            if product is None:
                raise NotFoundError(f"Producto {item.product_id} no encontrado")
            unit_price = (
                Decimal(str(item.unit_price)) if item.unit_price is not None else await _vigent_price(product)
            )
            sub = ((unit_price * item.quantity) - item.discount_amount).quantize(Decimal("0.01"))
            db.add(
                QuoteItem(
                    quote_id=quote.id,
                    product_id=product.id,
                    quantity=item.quantity,
                    unit_price=unit_price,
                    discount_amount=item.discount_amount,
                    subtotal=sub,
                    notes=item.notes,
                )
            )
            pairs.append((unit_price, item.quantity, item.discount_amount))
        subtotal, total = repository.compute_totals(pairs)
        quote.subtotal = subtotal
        quote.total = total
        quote.discount_amount = (subtotal - total).quantize(Decimal("0.01"))
    await db.commit()
    await _audit(action="UPDATE_QUOTE", user_id=user.id, quote=quote)
    fresh = await repository.get_quote(db, quote_id)
    assert fresh is not None
    return fresh


async def send_quote(db: AsyncSession, *, quote_id: uuid.UUID, user: User) -> Quote:
    """DRAFT → SENT. Encola WhatsApp QUOTE_CREATED al cliente DESPUÉS del commit (#F06-10)."""
    quote = await repository.get_quote(db, quote_id)
    if quote is None:
        raise NotFoundError("Cotización no encontrada")
    if quote.status != QuoteStatus.DRAFT:
        raise BusinessRuleError("Solo las cotizaciones DRAFT pueden enviarse")
    quote.status = QuoteStatus.SENT
    await db.commit()
    await _audit(action="SEND_QUOTE", user_id=user.id, quote=quote)

    # --- después del commit: WhatsApp asíncrono (nunca dentro de la tx) ---
    try:
        from app.modules.whatsapp.application.service import send_event

        await send_event(
            db,
            event_type="QUOTE_CREATED",
            recipient=_whatsapp_recipient(quote.customer),
            variables={
                "customer_name": _customer_name(quote.customer),
                "quote_code": quote.code,
                "total": f"{quote.total}",
                "valid_until": quote.valid_until.isoformat(),
            },
            idempotency_key=f"quote-created:{quote.id}",
        )
        quote.sent_via_whatsapp = True
        await db.commit()
    except Exception:  # noqa: BLE001 — el envío ya quedó PENDING o se reintenta
        logger.exception("Fallo encolando WhatsApp para cotización %s", quote.code)

    fresh = await repository.get_quote(db, quote_id)
    assert fresh is not None
    return fresh


async def mark_viewed(db: AsyncSession, *, quote: Quote) -> Quote:
    """SENT → VIEWED cuando el cliente abre el link público."""
    if quote.status != QuoteStatus.SENT:
        return quote
    quote.status = QuoteStatus.VIEWED
    quote.viewed_at = datetime.now(UTC)
    await db.commit()
    return quote


async def _respondable_or_fail(quote: Quote) -> None:
    if quote.status not in QuoteStatus.RESPONDABLE:
        raise BusinessRuleError(
            f"La cotización en estado {quote.status} ya no puede responderse"
        )


async def accept_quote(db: AsyncSession, *, quote_id: uuid.UUID, actor: User | None = None) -> Quote:
    """SENT/VIEWED → ACCEPTED. Notifica OWNER y SALES (#F06-02)."""
    quote = await repository.get_quote(db, quote_id)
    if quote is None:
        raise NotFoundError("Cotización no encontrada")
    await _respondable_or_fail(quote)
    quote.status = QuoteStatus.ACCEPTED
    quote.responded_at = datetime.now(UTC)
    await db.commit()
    await _audit(action="ACCEPT_QUOTE", user_id=actor.id if actor else None, quote=quote)

    try:
        from app.modules.notifications.application.service import notify_roles

        await notify_roles(
            db,
            role_codes=["OWNER", "SALES"],
            type_="quote_accepted",
            title="Cotización aceptada",
            message=(
                f"El cliente aceptó la cotización {quote.code} "
                f"({_customer_name(quote.customer)}) por {quote.currency} {quote.total}"
            ),
            priority="HIGH",
            related_type="quote",
            related_id=quote.id,
        )
        await db.commit()

        from app.modules.whatsapp.application.service import send_event

        owner_recipient = await _owner_recipient(db)
        await send_event(
            db,
            event_type="QUOTE_ACCEPTED",
            recipient=owner_recipient,
            variables={
                "quote_code": quote.code,
                "customer_name": _customer_name(quote.customer),
                "total": f"{quote.total}",
            },
            idempotency_key=f"quote-accepted:{quote.id}",
        )
        await db.commit()
    except Exception:  # noqa: BLE001
        logger.exception("Fallo notificando aceptación de cotización %s", quote.code)

    fresh = await repository.get_quote(db, quote_id)
    assert fresh is not None
    return fresh


async def reject_quote(
    db: AsyncSession, *, quote_id: uuid.UUID, reason: str | None = None, actor: User | None = None
) -> Quote:
    """SENT/VIEWED → REJECTED con motivo opcional."""
    quote = await repository.get_quote(db, quote_id)
    if quote is None:
        raise NotFoundError("Cotización no encontrada")
    await _respondable_or_fail(quote)
    quote.status = QuoteStatus.REJECTED
    quote.responded_at = datetime.now(UTC)
    if reason:
        quote.notes = f"{quote.notes}\n[RECHAZO] {reason}".strip() if quote.notes else f"[RECHAZO] {reason}"
    await db.commit()
    await _audit(action="REJECT_QUOTE", user_id=actor.id if actor else None, quote=quote, extra={"reason": reason})
    fresh = await repository.get_quote(db, quote_id)
    assert fresh is not None
    return fresh


async def public_get_by_code(db: AsyncSession, *, code: str) -> Quote:
    """Vista pública sin login: marca VIEWED si estaba SENT (#F06-02)."""
    quote = await repository.get_by_code(db, code)
    if quote is None:
        raise NotFoundError("Cotización no encontrada")
    if quote.status == QuoteStatus.SENT:
        quote = await mark_viewed(db, quote=quote)
    return quote


async def _owner_recipient(db: AsyncSession) -> str | None:
    from app.modules.roles.domain.models import Role

    row = (
        await db.execute(select(User).join(User.roles).where(Role.code == "OWNER").limit(1))
    ).scalars().first()
    if row is None:
        return None
    return getattr(row, "phone_whatsapp", None) or getattr(row, "phone", None)


# ---------------------------------------------------------------------------
# #F06-04 — Expiración automática
# ---------------------------------------------------------------------------


async def expire_pending_quotes(db: AsyncSession) -> dict[str, Any]:
    """Tarea Celery diaria: EXPIRABLE con valid_until < hoy → EXPIRED. Idempotente."""
    expired = await repository.expire_pending(db)
    if expired:
        await db.commit()
        try:
            from app.modules.notifications.application.service import notify_roles

            codes = ", ".join(q.code for q in expired[:10])
            await notify_roles(
                db,
                role_codes=["OWNER", "SALES"],
                type_="quote_expired",
                title="Cotizaciones expiradas",
                message=f"{len(expired)} cotización(es) expiraron hoy: {codes}",
                priority="MEDIUM",
                related_type="quote",
                related_id=expired[0].id,
            )
            await db.commit()
        except Exception:  # noqa: BLE001
            logger.exception("Fallo notificando expiración de cotizaciones")
    return {"expired": len(expired)}


# ---------------------------------------------------------------------------
# #F06-03 — Conversión atómica a venta
# ---------------------------------------------------------------------------


def _quote_items_as_sale_items(quote: Quote) -> list[SimpleNamespace]:
    """Mapea QuoteItems a ítems de venta conservando los precios CONGELADOS."""
    return [
        SimpleNamespace(
            product_id=item.product_id,
            serialized_unit_id=None,
            quantity=item.quantity,
            discount_amount=item.discount_amount,
            unit_price=Decimal(str(item.unit_price)),
        )
        for item in quote.items
    ]


async def convert_quote_to_sale(db: AsyncSession, *, quote_id: uuid.UUID, data, user: User) -> Sale:
    """Convierte una cotización ACCEPTED en venta (CASH o CREDIT) sin reingreso.

    ATÓMICIDAD: los servicios internos corren con commit=False; el commit
    único ocurre aquí tras marcar CONVERTED. Cualquier fallo propaga la
    excepción y el llamador hace rollback: la cotización queda intacta.
    """
    quote = await repository.get_quote(db, quote_id)
    if quote is None:
        raise NotFoundError("Cotización no encontrada")
    if quote.status == QuoteStatus.CONVERTED:
        raise ConflictError("La cotización ya fue convertida en venta")
    if quote.status == QuoteStatus.EXPIRED or quote.valid_until < date.today():
        raise BusinessRuleError("La cotización está expirada y no puede convertirse")
    if quote.status != QuoteStatus.ACCEPTED:
        raise BusinessRuleError("Solo las cotizaciones ACCEPTED pueden convertirse en venta")

    items = _quote_items_as_sale_items(quote)
    idem = f"quote-convert:{quote.id}"
    notes = f"Convertida desde cotización {quote.code}"

    if data.sale_type == "CASH":
        from app.modules.sales.application.service import create_cash_sale

        sale_data = SimpleNamespace(
            customer_id=quote.customer_id,
            items=items,
            payments=data.payments
            or [{"method": "CASH", "amount": str(quote.total), "idempotency_key": idem}],
            cash_session_id=data.cash_session_id,
            currency=quote.currency,
            discount_authorization_id=None,
            idempotency_key=idem,
            notes=notes,
        )
        sale = await create_cash_sale(db, data=sale_data, user=user, commit=False)
    else:
        from app.modules.credits.application.service import create_credit_sale

        credit_data = SimpleNamespace(
            customer_id=quote.customer_id,
            items=items,
            total_amount=quote.total,
            initial_payment=data.initial_payment,
            number_of_installments=data.number_of_installments,
            interest_rate=data.interest_rate,
            interest_free_months=data.interest_free_months,
            first_due_date=data.first_due_date or (date.today() + timedelta(days=30)),
            currency=quote.currency,
            notes=notes,
            cash_session_id=data.cash_session_id,
            initial_method=data.initial_method,
            authorization_ids=list(data.authorization_ids),
        )
        agreement = await create_credit_sale(db, data=credit_data, user=user, commit=False)
        sale = agreement.sale

    quote.status = QuoteStatus.CONVERTED
    quote.converted_to_sale_id = sale.id
    await db.commit()
    await _audit(
        action="CONVERT_QUOTE",
        user_id=user.id,
        quote=quote,
        extra={"sale_id": str(sale.id), "sale_code": sale.code, "sale_type": data.sale_type},
    )

    # refrescar relaciones para respuesta
    fresh = await db.get(Sale, sale.id)
    return fresh  # type: ignore[return-value]
