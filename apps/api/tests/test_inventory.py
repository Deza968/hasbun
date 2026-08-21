"""Tests de inventario: stock por movimientos, concurrencia, ajustes (#F03-12)."""

from __future__ import annotations

import asyncio
import inspect
import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import httpx

OWNER = {"email": "owner@hasbun.dev", "password": "Owner2026!"}
SALES = {"email": "ventas@hasbun.dev", "password": "Ventas2026!"}


async def _login(client: httpx.AsyncClient, creds: dict[str, str]) -> None:
    await client.post("/api/v1/auth/login", json=creds)


async def _create_product(client: httpx.AsyncClient, name: str, cost: str = "100.00") -> str:
    await _login(client, OWNER)
    response = await client.post(
        "/api/v1/products",
        json={
            "name": name,
            "cost_price": cost,
            "sale_price": "150.00",
            "currency": "PEN",
            "price_rule": "MANUAL",
            "published": False,
            "is_serialized": False,
            "attributes": [],
        },
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


async def _create_purchase(client: httpx.AsyncClient, product_id: str, qty: str, cost: str) -> str:
    suppliers = (await client.get("/api/v1/suppliers")).json()["items"]
    supplier_id = suppliers[0]["id"]
    response = await client.post(
        "/api/v1/purchases",
        json={
            "supplier_id": supplier_id,
            "currency": "PEN",
            "exchange_rate": "1",
            "items": [{"product_id": product_id, "quantity": qty, "unit_cost": cost}],
        },
    )
    assert response.status_code == 201, response.text
    purchase_id = response.json()["id"]
    received = await client.post(
        f"/api/v1/purchases/{purchase_id}/receive",
        json={"received_items": [{"item_id": response.json()["items"][0]["id"], "received_quantity": qty}]},
    )
    assert received.status_code == 200, received.text
    return purchase_id


async def test_stock_calculated_from_movements(client: httpx.AsyncClient) -> None:
    await _login(client, OWNER)
    product_id = await _create_product(client, "Stock por movimientos")
    await _create_purchase(client, product_id, "10", "100.00")

    stock = (await client.get(f"/api/v1/inventory/stock/{product_id}")).json()
    assert Decimal(stock["available"]) == Decimal("10")
    assert Decimal(stock["total_physical"]) == Decimal("10")


async def test_stock_cannot_go_negative(client: httpx.AsyncClient) -> None:
    """Movimiento que genera negativo → InsufficientStockError (400)."""
    await _login(client, OWNER)
    product_id = await _create_product(client, "Stock negativo")

    # Ajuste de salida sin stock → error
    response = await client.post(
        "/api/v1/inventory/adjustments",
        json={"product_id": product_id, "quantity": "-5", "reason": "Prueba negativa"},
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INSUFFICIENT_STOCK"


async def test_reserve_reduces_available_but_not_total(client: httpx.AsyncClient) -> None:
    await _login(client, OWNER)
    product_id = await _create_product(client, "Reserva")
    await _create_purchase(client, product_id, "10", "100.00")

    from app.database.session import AsyncSessionLocal
    from app.modules.inventory.application.service import reserve_stock
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncSession

    async with AsyncSessionLocal() as db:  # type: ignore[type-arg]
        async with db.begin():
            await reserve_stock(
                db,
                product_id=uuid.UUID(product_id),
                qty=Decimal("3"),
                reference_type="sale",
                reference_id=uuid.uuid4(),
                created_by=None,
            )

    stock = (await client.get(f"/api/v1/inventory/stock/{product_id}")).json()
    assert Decimal(stock["available"]) == Decimal("7")
    assert Decimal(stock["reserved"]) == Decimal("3")
    assert Decimal(stock["total_physical"]) == Decimal("10")


async def test_release_reservation_restores_stock(client: httpx.AsyncClient) -> None:
    await _login(client, OWNER)
    product_id = await _create_product(client, "Liberar reserva")
    await _create_purchase(client, product_id, "10", "100.00")

    from app.database.session import AsyncSessionLocal
    from app.modules.inventory.application.service import release_reservation, reserve_stock

    ref_id = uuid.uuid4()
    async with AsyncSessionLocal() as db:  # type: ignore[type-arg]
        async with db.begin():
            await reserve_stock(
                db,
                product_id=uuid.UUID(product_id),
                qty=Decimal("3"),
                reference_type="sale",
                reference_id=ref_id,
                created_by=None,
            )
        async with db.begin():
            await release_reservation(
                db,
                product_id=uuid.UUID(product_id),
                qty=Decimal("3"),
                reference_id=ref_id,
                created_by=None,
            )

    stock = (await client.get(f"/api/v1/inventory/stock/{product_id}")).json()
    assert Decimal(stock["available"]) == Decimal("10")
    assert Decimal(stock["reserved"]) == Decimal("0")


async def test_concurrent_sales_same_stock(client: httpx.AsyncClient) -> None:
    """5 ventas simultáneas con stock=3 → exactamente 3 exitosas, 2 con error."""
    from app.database.session import AsyncSessionLocal
    from app.modules.inventory.application.service import confirm_sale
    from app.core.exceptions import InsufficientStockError

    await _login(client, OWNER)
    product_id = await _create_product(client, "Concurrencia venta")
    await _create_purchase(client, product_id, "3", "100.00")
    pid = uuid.UUID(product_id)

    async def try_sale(i: int) -> bool:
        async with AsyncSessionLocal() as db:  # type: ignore[type-arg]
            async with db.begin():
                try:
                    await confirm_sale(
                        db,
                        product_id=pid,
                        qty=Decimal("1"),
                        reference_id=uuid.uuid4(),
                        created_by=None,
                    )
                    return True
                except InsufficientStockError:
                    return False

    results = await asyncio.gather(*(try_sale(i) for i in range(5)))
    assert sum(results) == 3, f"Esperado 3 exitosos, obtenido {sum(results)}"
    assert sum(1 for r in results if not r) == 2


async def test_concurrent_serialized_unit_sale(client: httpx.AsyncClient) -> None:
    """2 ventas simultáneas de 1 unidad serializada → 1 ok, 1 error."""
    await _login(client, OWNER)
    response = await client.post(
        "/api/v1/products",
        json={
            "name": "Laptop serial concurrencia",
            "cost_price": "1000.00",
            "sale_price": "1200.00",
            "currency": "PEN",
            "price_rule": "MANUAL",
            "published": False,
            "is_serialized": True,
            "serials": [{"serial_number": "CONC-SERIAL-1"}],
            "attributes": [],
        },
    )
    assert response.status_code == 201, response.text
    product_id = response.json()["id"]
    # Stock = 1 unidad por compra.
    await _create_purchase(client, product_id, "1", "1000.00")

    from app.database.session import AsyncSessionLocal
    from app.modules.inventory.application.service import confirm_sale
    from app.core.exceptions import InsufficientStockError

    async def try_sale() -> bool:
        async with AsyncSessionLocal() as db:  # type: ignore[type-arg]
            async with db.begin():
                try:
                    await confirm_sale(
                        db,
                        product_id=uuid.UUID(product_id),
                        qty=Decimal("1"),
                        reference_id=uuid.uuid4(),
                        created_by=None,
                    )
                    return True
                except InsufficientStockError:
                    return False

    results = await asyncio.gather(try_sale(), try_sale())
    assert sum(results) == 1, f"Esperado 1 exitoso, obtenido {results}"


async def test_adjustment_requires_owner(client: httpx.AsyncClient) -> None:
    await _login(client, OWNER)
    product_id = await _create_product(client, "Ajuste permisos")

    await _login(client, SALES)
    response = await client.post(
        "/api/v1/inventory/adjustments",
        json={"product_id": product_id, "quantity": "5", "reason": "Sin permiso"},
    )
    assert response.status_code == 403


async def test_adjustment_creates_audit_log(client: httpx.AsyncClient, db) -> None:
    await _login(client, OWNER)
    product_id = await _create_product(client, "Ajuste auditoría")
    await _create_purchase(client, product_id, "10", "100.00")

    response = await client.post(
        "/api/v1/inventory/adjustments",
        json={"product_id": product_id, "quantity": "2", "reason": "Conteo físico"},
    )
    assert response.status_code == 201, response.text
    movement = response.json()
    assert movement["authorization_id"] is not None

    from app.modules.audit.domain.models import AuditLog
    from sqlalchemy import select

    audit = (
        await db.execute(
            select(AuditLog).where(
                AuditLog.module == "inventory",
                AuditLog.action == "ADJUST_INVENTORY",
            )
        )
    ).scalars().all()
    assert any(
        a.new_values.get("qty") == "2" and a.new_values.get("reason") == "Conteo físico"
        for a in audit
    )


async def test_inventory_movement_immutable(client: httpx.AsyncClient) -> None:
    """No existe endpoint de actualización ni métodos update/delete en el repositorio."""
    from app.modules.inventory.infrastructure import repository as inventory_repo

    source = inspect.getsource(inventory_repo)
    assert "def update" not in source
    assert "def delete" not in source
    assert "def add_movement" in source

    await _login(client, OWNER)
    response = await client.put("/api/v1/inventory/stock/00000000-0000-0000-0000-000000000000", json={})
    assert response.status_code == 405  # solo métodos GET/POST definidos


async def test_stock_zero_precision(client: httpx.AsyncClient) -> None:
    """Suma de 100 movimientos de 0.1 = exactamente 10.0 (sin error flotante)."""
    from app.database.session import AsyncSessionLocal
    from app.modules.inventory.application.service import register_purchase

    await _login(client, OWNER)
    product_id = await _create_product(client, "Precisión decimal")
    pid = uuid.UUID(product_id)

    async with AsyncSessionLocal() as db:  # type: ignore[type-arg]
        async with db.begin():
            for _ in range(100):
                await register_purchase(
                    db,
                    product_id=pid,
                    qty=Decimal("0.1"),
                    reference_id=uuid.uuid4(),
                    created_by=None,
                    unit_cost=Decimal("1"),
                )

    stock = (await client.get(f"/api/v1/inventory/stock/{product_id}")).json()
    assert Decimal(stock["available"]) == Decimal("10.0")