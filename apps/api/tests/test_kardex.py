"""Tests de kardex (#F03-14)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import httpx

OWNER = {"email": "owner@hasbun.dev", "password": "Owner2026!"}


async def _login(client: httpx.AsyncClient) -> None:
    await client.post("/api/v1/auth/login", json=OWNER)


async def _setup(client: httpx.AsyncClient) -> str:
    """Crea producto, lo compra (10) y hace una venta (3) → kardex con 2 movimientos."""
    await _login(client)
    product = await client.post(
        "/api/v1/products",
        json={
            "name": "Producto kardex",
            "cost_price": "100.00",
            "sale_price": "150.00",
            "currency": "PEN",
            "price_rule": "MANUAL",
            "published": False,
            "is_serialized": False,
            "attributes": [],
        },
    )
    assert product.status_code == 201, product.text
    product_id = product.json()["id"]

    suppliers = (await client.get("/api/v1/suppliers")).json()["items"]
    purchase = await client.post(
        "/api/v1/purchases",
        json={
            "supplier_id": suppliers[0]["id"],
            "currency": "PEN",
            "exchange_rate": "1",
            "items": [{"product_id": product_id, "quantity": "10", "unit_cost": "100.00"}],
        },
    )
    assert purchase.status_code == 201, purchase.text
    pdata = purchase.json()
    item_id = pdata["items"][0]["id"]
    await client.post(
        f"/api/v1/purchases/{pdata['id']}/receive",
        json={"received_items": [{"item_id": item_id, "received_quantity": "10"}]},
    )

    # Ajuste de salida -3 para simular una venta/consumo.
    adj = await client.post(
        "/api/v1/inventory/adjustments",
        json={"product_id": product_id, "quantity": "-3", "reason": "Venta de prueba"},
    )
    assert adj.status_code == 201, adj.text
    return product_id


async def test_kardex_shows_all_movements_in_order(client: httpx.AsyncClient) -> None:
    product_id = await _setup(client)
    kardex = (await client.get(f"/api/v1/inventory/kardex/{product_id}")).json()
    assert kardex["total"] >= 2
    types = [m["movement_type"] for m in kardex["items"]]
    assert "PURCHASE" in types
    assert "ADJUSTMENT_OUT" in types
    # Orden cronológico (created_at ascendente).
    timestamps = [m["created_at"] for m in kardex["items"]]
    assert timestamps == sorted(timestamps)


async def test_kardex_running_balance_correct(client: httpx.AsyncClient) -> None:
    product_id = await _setup(client)
    kardex = (await client.get(f"/api/v1/inventory/kardex/{product_id}")).json()
    balance = Decimal("0")
    physical = {"PURCHASE", "ADJUSTMENT_IN", "RETURN", "REPAIR_RETURN", "SALE", "ADJUSTMENT_OUT", "REPAIR_USAGE", "DAMAGED"}
    for movement in kardex["items"]:
        if movement["movement_type"] in physical:
            balance += Decimal(movement["quantity"])
        assert Decimal(movement["balance"]) == balance


async def test_kardex_filter_by_movement_type(client: httpx.AsyncClient) -> None:
    product_id = await _setup(client)
    kardex = (
        await client.get(
            f"/api/v1/inventory/kardex/{product_id}?movement_type=ADJUSTMENT_OUT"
        )
    ).json()
    assert kardex["total"] == 1
    assert all(m["movement_type"] == "ADJUSTMENT_OUT" for m in kardex["items"])


async def test_kardex_filter_by_date_range(client: httpx.AsyncClient) -> None:
    from urllib.parse import quote

    product_id = await _setup(client)
    tomorrow = quote((datetime.now(UTC) + timedelta(days=1)).isoformat())
    kardex = (
        await client.get(
            f"/api/v1/inventory/kardex/{product_id}?date_to={tomorrow}"
        )
    ).json()
    assert kardex["total"] >= 2


