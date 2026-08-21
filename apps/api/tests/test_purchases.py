"""Tests de compras (#F03-13)."""

from __future__ import annotations

from decimal import Decimal

import httpx

OWNER = {"email": "owner@hasbun.dev", "password": "Owner2026!"}
SALES = {"email": "ventas@hasbun.dev", "password": "Ventas2026!"}


async def _login(client: httpx.AsyncClient, creds: dict[str, str]) -> None:
    await client.post("/api/v1/auth/login", json=creds)


async def _make_product(client: httpx.AsyncClient, name: str, cost: str = "100.00") -> str:
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


async def _create_purchase(
    client: httpx.AsyncClient, product_id: str, qty: str = "10", cost: str = "100.00"
) -> tuple[str, str]:
    await _login(client, OWNER)
    suppliers = (await client.get("/api/v1/suppliers")).json()["items"]
    response = await client.post(
        "/api/v1/purchases",
        json={
            "supplier_id": suppliers[0]["id"],
            "currency": "PEN",
            "exchange_rate": "1",
            "items": [{"product_id": product_id, "quantity": qty, "unit_cost": cost}],
        },
    )
    assert response.status_code == 201, response.text
    data = response.json()
    return data["id"], data["items"][0]["id"]


async def test_purchase_reception_creates_inventory_movement(client: httpx.AsyncClient) -> None:
    product_id = await _make_product(client, "Compra movimiento")
    purchase_id, item_id = await _create_purchase(client, product_id, "10", "100.00")

    received = await client.post(
        f"/api/v1/purchases/{purchase_id}/receive",
        json={"received_items": [{"item_id": item_id, "received_quantity": "10"}]},
    )
    assert received.status_code == 200, received.text
    assert received.json()["status"] == "RECEIVED"

    from app.database.session import AsyncSessionLocal
    from app.modules.inventory.domain.models import InventoryMovement, MovementType
    from sqlalchemy import select

    async with AsyncSessionLocal() as db:  # type: ignore[type-arg]
        movements = (
            await db.execute(
                select(InventoryMovement).where(
                    InventoryMovement.movement_type == MovementType.PURCHASE
                )
            )
        ).scalars().all()
    assert any(str(m.reference_id) == received.json()["id"] for m in movements)


async def test_purchase_reception_increases_stock(client: httpx.AsyncClient) -> None:
    product_id = await _make_product(client, "Compra stock")
    purchase_id, item_id = await _create_purchase(client, product_id, "10", "100.00")
    before = (await client.get(f"/api/v1/inventory/stock/{product_id}")).json()["available"]

    await client.post(
        f"/api/v1/purchases/{purchase_id}/receive",
        json={"received_items": [{"item_id": item_id, "received_quantity": "10"}]},
    )
    after = (await client.get(f"/api/v1/inventory/stock/{product_id}")).json()["available"]
    assert Decimal(after) == Decimal(before) + Decimal("10")


async def test_partial_reception(client: httpx.AsyncClient) -> None:
    product_id = await _make_product(client, "Compra parcial")
    purchase_id, item_id = await _create_purchase(client, product_id, "10", "100.00")

    received = await client.post(
        f"/api/v1/purchases/{purchase_id}/receive",
        json={"received_items": [{"item_id": item_id, "received_quantity": "4"}]},
    )
    assert received.status_code == 200
    assert received.json()["status"] == "PARTIAL"
    stock = (await client.get(f"/api/v1/inventory/stock/{product_id}")).json()["available"]
    assert Decimal(stock) == Decimal("4")


async def test_cancel_received_purchase_blocked(client: httpx.AsyncClient) -> None:
    product_id = await _make_product(client, "Compra cancelar")
    purchase_id, item_id = await _create_purchase(client, product_id, "5", "100.00")
    await client.post(
        f"/api/v1/purchases/{purchase_id}/receive",
        json={"received_items": [{"item_id": item_id, "received_quantity": "5"}]},
    )
    response = await client.post(
        f"/api/v1/purchases/{purchase_id}/cancel",
        json={"reason": "No se puede cancelar recibida"},
    )
    assert response.status_code == 409


async def test_purchase_in_usd_stores_exchange_rate(client: httpx.AsyncClient) -> None:
    product_id = await _make_product(client, "Compra USD")
    await _login(client, OWNER)
    suppliers = (await client.get("/api/v1/suppliers")).json()["items"]
    response = await client.post(
        "/api/v1/purchases",
        json={
            "supplier_id": suppliers[0]["id"],
            "currency": "USD",
            "exchange_rate": "3.75",
            "items": [{"product_id": product_id, "quantity": "2", "unit_cost": "50.00"}],
        },
    )
    assert response.status_code == 201, response.text
    assert Decimal(response.json()["exchange_rate"]) == Decimal("3.7500")
    assert response.json()["currency"] == "USD"


async def test_sales_cannot_create_purchase(client: httpx.AsyncClient) -> None:
    await _login(client, SALES)
    response = await client.post(
        "/api/v1/purchases",
        json={
            "supplier_id": "00000000-0000-0000-0000-000000000000",
            "currency": "PEN",
            "exchange_rate": "1",
            "items": [{"product_id": "00000000-0000-0000-0000-000000000000", "quantity": "1", "unit_cost": "1"}],
        },
    )
    assert response.status_code == 403


async def test_sales_cannot_manage_suppliers(client: httpx.AsyncClient) -> None:
    await _login(client, SALES)
    response = await client.post(
        "/api/v1/suppliers",
        json={"razon_social": "Proveedor sin permiso"},
    )
    assert response.status_code == 403
