"""Tests de productos, SKU, seriales y ofertas (#F02-19)."""

from __future__ import annotations

from datetime import UTC

import httpx

OWNER = {"email": "owner@hasbun.dev", "password": "Owner2026!"}
SALES = {"email": "ventas@hasbun.dev", "password": "Ventas2026!"}


async def _login(client: httpx.AsyncClient, creds: dict[str, str]) -> None:
    await client.post("/api/v1/auth/login", json=creds)


PRODUCT_PAYLOAD = {
    "name": "Laptop de prueba SKU única",
    "brand_id": None,
    "category_id": None,
    "cost_price": "1500.00",
    "sale_price": "1899.00",
    "currency": "PEN",
    "price_rule": "MANUAL",
    "published": True,
    "is_serialized": False,
    "attributes": [],
}


async def test_create_product_generates_unique_sku(client: httpx.AsyncClient) -> None:
    await _login(client, OWNER)
    response = await client.post("/api/v1/products", json=PRODUCT_PAYLOAD)
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["sku"].startswith("PRD-")
    assert len(data["sku"].split("-")[-1]) == 5


async def test_sku_unique_under_concurrency(client: httpx.AsyncClient) -> None:
    """10 requests simultáneos generan SKUs únicos (concurrencia)."""
    import asyncio

    await _login(client, OWNER)

    async def create_one(i: int):
        from app.database.session import AsyncSessionLocal
        from app.modules.products.application.schemas import ProductCreate
        from app.modules.products.application.service import create_product

        async with AsyncSessionLocal() as db:
            from app.modules.users.domain.models import User
            from sqlalchemy import select

            owner = (
                await db.execute(
                    select(User).where(User.email == "owner@hasbun.dev")
                )
            ).scalars().first()
            product = await create_product(
                db,
                data=ProductCreate(
                    name=f"Laptop concurrencia {i}",
                    cost_price="100.00",
                    sale_price="150.00",
                    currency="PEN",
                    price_rule="MANUAL",
                ),
                created_by=owner,
            )
            sku = product.sku
            await db.commit()
            return sku

    skus = await asyncio.gather(*(create_one(i) for i in range(10)))
    assert len(set(skus)) == 10
    assert all(s.startswith("LAP-") or s.startswith("PRD-") for s in skus)


async def test_owner_can_change_price_and_audits(client: httpx.AsyncClient, db) -> None:
    await _login(client, OWNER)
    created = await client.post("/api/v1/products", json=PRODUCT_PAYLOAD)
    product_id = created.json()["id"]

    response = await client.put(
        f"/api/v1/products/{product_id}",
        json={"sale_price": "2099.00"},
    )
    assert response.status_code == 200

    from app.modules.audit.domain.models import AuditLog
    from sqlalchemy import select

    audit = (
        await db.execute(
            select(AuditLog).where(
                AuditLog.module == "products",
                AuditLog.action.in_(["UPDATE_PRODUCT_PRICE", "CREATE_PRODUCT"]),
            )
        )
    ).scalars().all()
    assert any(a.action == "CREATE_PRODUCT" for a in audit)
    assert any(
        a.action == "UPDATE_PRODUCT_PRICE"
        and a.old_values.get("sale_price") == "1899.00"
        and a.new_values.get("sale_price") == "2099.00"
        for a in audit
    )


async def test_sales_cannot_change_cost(client: httpx.AsyncClient) -> None:
    await _login(client, SALES)
    response = await client.post("/api/v1/products", json=PRODUCT_PAYLOAD)
    assert response.status_code == 403


async def test_sales_cannot_change_sale_price(client: httpx.AsyncClient) -> None:
    await _login(client, OWNER)
    created = await client.post("/api/v1/products", json=PRODUCT_PAYLOAD)
    product_id = created.json()["id"]

    await _login(client, SALES)
    response = await client.put(f"/api/v1/products/{product_id}", json={"sale_price": "3000.00"})
    assert response.status_code == 403


async def test_product_offer_active_within_dates(client: httpx.AsyncClient) -> None:
    from datetime import datetime, timedelta

    await _login(client, OWNER)
    created = await client.post("/api/v1/products", json=PRODUCT_PAYLOAD)
    product_id = created.json()["id"]

    now = datetime.now(UTC)
    offer = await client.post(
        f"/api/v1/products/{product_id}/offers",
        json={
            "normal_price": "1899.00",
            "offer_price": "1499.00",
            "start_at": (now - timedelta(days=1)).isoformat(),
            "end_at": (now + timedelta(days=1)).isoformat(),
        },
    )
    assert offer.status_code == 201

    detail = await client.get(f"/api/v1/products/{product_id}")
    assert detail.status_code == 200
    assert detail.json()["current_price"] == "1499.00"


async def test_product_offer_inactive_outside_dates(client: httpx.AsyncClient) -> None:
    from datetime import datetime, timedelta

    await _login(client, OWNER)
    created = await client.post("/api/v1/products", json=PRODUCT_PAYLOAD)
    product_id = created.json()["id"]

    now = datetime.now(UTC)
    offer = await client.post(
        f"/api/v1/products/{product_id}/offers",
        json={
            "normal_price": "1899.00",
            "offer_price": "1499.00",
            "start_at": (now - timedelta(days=10)).isoformat(),
            "end_at": (now - timedelta(days=9)).isoformat(),
        },
    )
    assert offer.status_code == 201

    detail = await client.get(f"/api/v1/products/{product_id}")
    assert detail.json()["current_price"] == "1899.00"


async def test_cannot_duplicate_serial_number(client: httpx.AsyncClient) -> None:
    await _login(client, OWNER)
    payload = {
        **PRODUCT_PAYLOAD,
        "name": "Laptop serializada única X",
        "is_serialized": True,
        "serials": [{"serial_number": "SERIAL-A1"}],
    }
    created = await client.post("/api/v1/products", json=payload)
    assert created.status_code == 201, created.text
    product_id = created.json()["id"]

    dup = await client.post(
        f"/api/v1/products/{product_id}/serials",
        json={"serial_number": "SERIAL-A1", "status": "AVAILABLE"},
    )
    assert dup.status_code == 409


async def test_deactivate_product_soft(client: httpx.AsyncClient) -> None:
    await _login(client, OWNER)
    created = await client.post("/api/v1/products", json=PRODUCT_PAYLOAD)
    product_id = created.json()["id"]

    response = await client.delete(f"/api/v1/products/{product_id}")
    assert response.status_code == 200
    assert response.json()["active"] is False


async def test_published_product_visible_in_public_api(client: httpx.AsyncClient) -> None:
    # Sin autenticación
    response = await client.get("/api/v1/products?published=true&active=true")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    for item in data["items"]:
        assert item["published"] is True
        assert item["active"] is True
        # No se expone el costo en modo público
        assert item["cost_price"] == "0"


async def test_guest_cannot_create_product(client: httpx.AsyncClient) -> None:
    response = await client.post("/api/v1/products", json=PRODUCT_PAYLOAD)
    assert response.status_code == 401


async def test_assign_attributes_to_product(client: httpx.AsyncClient) -> None:
    await _login(client, OWNER)
    created = await client.post("/api/v1/products", json=PRODUCT_PAYLOAD)
    product_id = created.json()["id"]

    response = await client.post(
        f"/api/v1/products/{product_id}/attributes",
        json={"attributes": [{"attribute": "RAM", "value": "16GB"}]},
    )
    assert response.status_code == 200
    attrs = response.json()["attributes"]
    assert any(a["attribute"] == "RAM" and a["value"] == "16GB" for a in attrs)
