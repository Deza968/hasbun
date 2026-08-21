"""Generador de código de venta transaccional (#F04-09)."""

from __future__ import annotations

from datetime import UTC

from app.modules.sales.domain.models import DocumentSequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


async def next_document_code(db: AsyncSession, prefix: str, year: int) -> str:
    row = (await db.execute(select(DocumentSequence).where(DocumentSequence.prefix == prefix, DocumentSequence.year == year).with_for_update())).scalar_one_or_none()
    if row is None:
        row = DocumentSequence(prefix=prefix, year=year, last_value=1)
        db.add(row)
        await db.flush()
        return f"{prefix}-{year}-{1:05d}"
    row.last_value += 1
    await db.flush()
    return f"{prefix}-{year}-{row.last_value:05d}"


async def next_sale_code(db: AsyncSession) -> str:
    from datetime import datetime

    year = datetime.now(UTC).year
    return await next_document_code(db, "VTA", year)
