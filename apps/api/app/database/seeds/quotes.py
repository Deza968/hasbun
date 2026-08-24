"""Seeds de cotizaciones ficticias (#F06-20): SENT, ACCEPTED y EXPIRED.

Idempotente: no duplica códigos existentes. Usa clientes/productos ya sembrados.
"""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.customers.domain.models import Customer
from app.modules.products.domain.models import Product
from app.modules.quotes.domain.models import Quote, QuoteItem, QuoteStatus
from app.modules.users.domain.models import User

TARGET_QUOTES = 3


async def seed_quotes(db: AsyncSession) -> dict[str, int]:
    existing = set((await db.execute(select(Quote.code))).scalars().all())
    if len(existing) >= TARGET_QUOTES:
        return {"quotes_created": 0, "quotes_total": len(existing)}

    ventas = (
        await db.execute(select(User).where(User.email == "ventas@hasbun.dev"))
    ).scalars().first()
    customer = (
        await db.execute(select(Customer).where(Customer.active.is_(True)).limit(1))
    ).scalars().first()
    products = (
        await db.execute(
            select(Product).where(Product.active.is_(True), Product.is_serialized.is_(False)).limit(3)
        )
    ).scalars().all()
    if customer is None or not products or ventas is None:
        return {"quotes_created": 0, "quotes_total": len(existing), "skipped": 1}

    year = datetime.now(UTC).year
    today = date.today()
    plans = [
        # (status, valid_until_offset)
        (QuoteStatus.SENT, 7),
        (QuoteStatus.ACCEPTED, 15),
        (QuoteStatus.EXPIRED, -1),
    ]
    created = 0
    seq = len(existing) + 1
    for status, offset in plans:
        code = f"COT-{year}-{seq:05d}"
        while code in existing:  # nunca chocar con códigos reales
            seq += 1
            code = f"COT-{year}-{seq:05d}"
        seq += 1

        quote = Quote(
            code=code,
            customer_id=customer.id,
            status=status,
            subtotal=Decimal("0.00"),
            discount_amount=Decimal("0.00"),
            total=Decimal("0.00"),
            currency="PEN",
            exchange_rate=Decimal("3.7500"),
            exchange_rate_source="mock",
            exchange_rate_timestamp=datetime.now(UTC),
            valid_until=today + timedelta(days=offset),
            notes="Cotización de demostración (seed)",
            sent_via_whatsapp=status in (QuoteStatus.SENT, QuoteStatus.VIEWED, QuoteStatus.ACCEPTED),
            viewed_at=datetime.now(UTC) - timedelta(hours=2) if status == QuoteStatus.EXPIRED else None,
            responded_at=datetime.now(UTC) - timedelta(days=2) if status == QuoteStatus.ACCEPTED else None,
            created_by=ventas.id,
        )
        db.add(quote)
        await db.flush()

        total = Decimal("0.00")
        subtotal = Decimal("0.00")
        qty = Decimal("1")
        for product in products[:2]:
            price = Decimal(str(product.sale_price)).quantize(Decimal("0.01"))
            sub = (price * qty).quantize(Decimal("0.01"))
            db.add(
                QuoteItem(
                    quote_id=quote.id,
                    product_id=product.id,
                    quantity=qty,
                    unit_price=price,
                    discount_amount=Decimal("0.00"),
                    subtotal=sub,
                )
            )
            subtotal += sub
            total += sub
        quote.subtotal = subtotal.quantize(Decimal("0.01"))
        quote.total = total.quantize(Decimal("0.01"))
        created += 1

    await db.commit()
    return {"quotes_created": created, "quotes_total": TARGET_QUOTES}
