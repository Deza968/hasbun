"""Generador transaccional de SKU (#F02-06).

Usa una tabla auxiliar `sku_sequences` y `SELECT ... FOR UPDATE` dentro de la
misma transacción que crea el producto, garantizando unicidad bajo concurrencia.
Formato: `{prefix}-{value:05d}` → `LAP-00001`.
"""

from __future__ import annotations

from app.core.config import settings
from app.modules.products.domain.models import SkuSequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Prefijos de semilla por defecto (categorías) #F02-06
DEFAULT_SKU_PREFIXES: list[str] = [
    "LAP",
    "IMP",
    "CAM",
    "ACC",
    "ELE",
    "SRV",
    "SBL",
    "MON",
    "CEL",
    "TAB",
    "RED",
    "ALM",
]


def prefix_for_category(category_slug: str | None) -> str:
    """Resuelve el prefijo según el slug de la categoría (configurable)."""
    if category_slug and category_slug in settings.SKU_PREFIX_BY_CATEGORY_SLUG:
        return settings.SKU_PREFIX_BY_CATEGORY_SLUG[category_slug]
    return settings.SKU_DEFAULT_PREFIX


async def generate_sku(db: AsyncSession, prefix: str) -> str:
    """Genera el siguiente SKU para un prefijo, de forma transaccional.

    Debe llamarse dentro de la transacción que crea el producto. Usa
    `FOR UPDATE` para bloquear la fila de la secuencia mientras se incrementa.
    """
    prefix = prefix.upper()
    result = await db.execute(
        select(SkuSequence).where(SkuSequence.prefix == prefix).with_for_update()
    )
    seq = result.scalars().first()
    if seq is None:
        seq = SkuSequence(prefix=prefix, last_value=0)
        db.add(seq)
        await db.flush()

    seq.last_value += 1
    sku = f"{prefix}-{seq.last_value:05d}"
    return sku


async def seed_sku_prefixes(db: AsyncSession) -> int:
    """Inserta los prefijos base si no existen. Idempotente."""
    created = 0
    for prefix in DEFAULT_SKU_PREFIXES:
        exists = (
            await db.execute(select(SkuSequence).where(SkuSequence.prefix == prefix))
        ).scalars().first()
        if exists is None:
            db.add(SkuSequence(prefix=prefix, last_value=0))
            created += 1
    await db.commit()
    return created
