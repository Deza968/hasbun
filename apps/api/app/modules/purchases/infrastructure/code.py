"""Generador transaccional de códigos de compra (#F03-09).

Formato: `OC-YYYY-XXXXX` (OC = orden de compra, año actual, correlativo).
Usa una tabla auxiliar `purchase_sequences` con `SELECT ... FOR UPDATE`.
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


async def next_purchase_code(db: AsyncSession) -> str:
    """Genera el siguiente código de compra de forma transaccional."""
    from app.modules.purchases.domain.models import PurchaseSequence

    year = datetime.now(UTC).year
    result = await db.execute(
        select(PurchaseSequence)
        .where(PurchaseSequence.year == year)
        .with_for_update()
    )
    seq = result.scalars().first()
    if seq is None:
        seq = PurchaseSequence(year=year, last_value=0)
        db.add(seq)
        await db.flush()

    seq.last_value += 1
    return f"OC-{year}-{seq.last_value:05d}"
