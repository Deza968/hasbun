"""Tareas Celery de inventario (#F03-15, #F03-19).

- `check_low_stock`: alerta de stock bajo (2 veces al día, idempotente por día/producto).
- `generate_daily_stock_report`: reporte diario (stub, contenido completo en FASE 12).
"""

from __future__ import annotations

import asyncio
import logging
from datetime import date, datetime
from decimal import Decimal

from worker.celery_app import celery_app

logger = logging.getLogger("hasbun.worker.inventory")

# Caché en memoria para idempotencia del día (fallback si Redis no está).
# En producción la idempotencia se refuerza con clave en Redis/DB.
_last_check: dict[str, date] = {}


async def _run_check_low_stock() -> dict[str, object]:
    from sqlalchemy import text

    from app.database.session import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        rows = (
            await db.execute(
                text(
                    "SELECT product_id, sku, product_name, available, stock_minimum "
                    "FROM v_product_stock_summary "
                    "WHERE available <= stock_minimum"
                )
            )
        ).all()

        low_items: list[dict[str, object]] = []
        for row in rows:
            available = Decimal(str(row.available))
            stock_min = int(row.stock_minimum or 0)
            is_out = available <= 0
            low_items.append(
                {
                    "product_id": str(row.product_id),
                    "sku": row.sku,
                    "product_name": row.product_name,
                    "available": str(available),
                    "stock_minimum": stock_min,
                    "event": "STOCK_OUT" if is_out else "STOCK_LOW",
                }
            )

        if not low_items:
            logger.info("check_low_stock: sin productos con stock bajo")
            return {"checked": True, "low_count": 0, "items": []}

        # Idempotencia: si ya se notificó hoy, no duplicar.
        today = date.today().isoformat()
        deduped: list[dict[str, object]] = []
        for item in low_items:
            key = f"{item['product_id']}:{today}"
            if key in _last_check and _last_check[key] == date.today():
                continue
            _last_check[key] = date.today()
            deduped.append(item)

        # En FASE 12 esto crea Notification + WhatsApp. Ahora solo loguea.
        for item in deduped:
            if item["event"] == "STOCK_OUT":
                logger.warning(
                    "STOCK_OUT producto %s (%s) disponible=%s",
                    item["product_name"],
                    item["sku"],
                    item["available"],
                )
            else:
                logger.info(
                    "STOCK_LOW producto %s (%s) disponible=%s mínimo=%s",
                    item["product_name"],
                    item["sku"],
                    item["available"],
                    item["stock_minimum"],
                )

        return {"checked": True, "low_count": len(deduped), "items": deduped}


async def _run_daily_stock_report() -> dict[str, object]:
    from sqlalchemy import text

    from app.database.session import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        total_products = (await db.execute(text("SELECT count(*) FROM products WHERE active = true"))).scalar()
        total_movements = (await db.execute(text("SELECT count(*) FROM inventory_movements"))).scalar()
        low_count = (
            await db.execute(
                text("SELECT count(*) FROM v_product_stock_summary WHERE available <= stock_minimum")
            )
        ).scalar()
        logger.info(
            "Reporte diario stock: productos_activos=%s movimientos=%s stock_bajo=%s fecha=%s",
            total_products,
            total_movements,
            low_count,
            datetime.now().isoformat(),
        )
        return {
            "generated": True,
            "total_products": int(total_products or 0),
            "total_movements": int(total_movements or 0),
            "low_count": int(low_count or 0),
        }


@celery_app.task(name="worker.tasks.inventory.check_low_stock")
def check_low_stock() -> dict[str, object]:
    """Alerta de stock bajo — idempotente por día/producto (#F03-15)."""
    result: dict[str, object] = asyncio.run(_run_check_low_stock())
    logger.info("check_low_stock resultado: %s", result)
    return result


@celery_app.task(name="worker.tasks.inventory.generate_daily_stock_report")
def generate_daily_stock_report() -> dict[str, object]:
    """Reporte diario de stock — stub preparado para FASE 12 (#F03-19)."""
    result: dict[str, object] = asyncio.run(_run_daily_stock_report())
    logger.info("generate_daily_stock_report resultado: %s", result)
    return result
