"""Tests de productos del catálogo (#F02-19)."""

from __future__ import annotations

import httpx

OWNER = {"email": "owner@hasbun.dev", "password": "Owner2026!"}
SALES = {"email": "ventas@hasbun.dev", "password": "Ventas2026!"}


async def _login(client: httpx.AsyncClient, creds: dict[str, str]) -> None:
    response = await client.post("/api/v1/auth/login", json=creds)
    assert response.status_code == 200


async def _create_category(client: httpx.AsyncClient, name: str) -> str:
    response = await client.post("/api/v1/categories", json={"name": name})
    assert response.status_code == 201, response.text
    return response.json()["id"]


async def _create_brand(client: httpx.AsyncClient, name: str) -> str:
    response = await client.post("/api/v1/brands", json={"name": name})
    assert response.status_code == 201, response.text
    return response.json()["id"]


async def _create_attribute(client: httpx.AsyncClient, name: str) -> str:
    response = await client.post(
        "/api/v1/attributes", json={"name": name, "data_type": "text"}
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


async def _create_product(client: httpx.AsyncClient, category_id: str, **overrides) -> dict:
    payload = {
        "name": "Producto Test",
        "category_id": category_id,
        "cost_price": 100,
        "sale_price": 150,
        "currency": "PEN",
        "price_rule": "FIXED_PEN",
    }
    payload.update(overrides)
    response = await client.post("/api/v1/products", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


async def test_create_product_generates_unique_sku(
    client: httpx.AsyncClient,
) -> None:
    await _login(client, OWNER)
    category_id = await _create_category(client, "Laptops Test")
    product = await _create_product(client, category_id, name="Laptop Alpha")
    assert product["sku"].startswith("LAP-")
    assert len(product["sku"].split("-")[1]) == 5


async def test_sku_sequential_no_duplicates(client: httpx.AsyncClient) -> None:
    await _login(client, OWNER)
    category_id = await _create_category(client, "Impresoras Test")
    skus = set()
    for i in range(5):
        product = await _create_product(
            client, category_id, name=f"Impresora Test {i}"
        )
        skus.add(product["sku"])
    assert len(skus) == 5


async def test_owner_can_change_price_creates_audit_log(
    client: httpx.AsyncClient, db
) -> None:
    await _login(client, OWNER)
    category_id = await _create_category(client, "Monitores Test")
    product = await _create_product(client, category_id, name="Monitor Audit")

    response = await client.put(
        f"/api/v1/products/{product['id']}",
        json={"sale_price": 199},
    )
    assert response.status_code == 200, response.text
    assert response.json()["sale_price"] == "199.00"

    from app.modules.audit.domain.models import AuditLog
    from sqlalchemy import select

    logs = (
        await db.execute(
            select(AuditLog).where(AuditLog.entity_id == product["id"])
        )
    ).scalars().all()
    actions = {log.action for log in logs}
    assert "PRODUCT_PRICE_CHANGED" in actions
    assert "UPDATE_PRODUCT" in actions


async def test_sales_cannot_change_cost(client: httpx.AsyncClient) -> None:
    # OWNER crea un producto
    await _login(client, OWNER)
    category_id = await _create_category(client, "Monitores Costo")
    product = await _create_product(client, category_id, name="Monitor Costo")

    # SALES intenta modificar el costo → 403
    await _login(client, SALES)
    response = await client.put(
        f"/api/v1/products/{product['id']}",
        json={"cost_price": 1},
    )
    assert response.status_code == 403


async def test_sales_cannot_create_product(client: httpx.AsyncClient) -> None:
    await _login(client, SALES)
    response = await client.post(
        "/api/v1/products",
        json={"name": "Prohibido", "cost_price": 1, "sale_price": 2},
    )
    assert response.status_code == 403


async def test_product_offer_active_within_dates(
    client: httpx.AsyncClient,
) -> None:
    await _login(client, OWNER)
    category_id = await _create_category(client, "Cámaras Test")
    product = await _create_product(client, category_id, name="Cámara Oferta")

    offer_response = await client.post(
        f"/api/v1/products/{product['id']}/offers",
        json={
            "normal_price": 150,
            "offer_price": 120,
            "start_at": "2026-01-01T00:00:00Z",
            "end_at": "2030-01-01T00:00:00Z",
        },
    )
    assert offer_response.status_code == 201, offer_response.text

    public = await client.get("/api/v1/products")
    items = public.json()["items"]
    assert items == []  # aún no publicado

    await client.post(f"/api/v1/products/{product['id']}/publish")
    public = await client.get(f"/api/v1/products/{product['id']}")
    data = public.json()
    assert data["current_price"] == "120.00"
    assert data["active_offer"]["offer_price"] == "120.00"


async def test_product_offer_inactive_outside_dates(
    client: httpx.AsyncClient,
) -> None:
    await _login(client, OWNER)
    category_id = await _create_category(client, "Tablets Test")
    product = await _create_product(client, category_id, name="Tablet Oferta")

    response = await client.post(
        f"/api/v1/products/{product['id']}/offers",
        json={
            "normal_price": 150,
            "offer_price": 120,
            "start_at": "2000-01-01T00:00:00Z",
            "end_at": "2001-01-01T00:00:00Z",
        },
    )
    assert response.status_code == 201, response.text

    await client.post(f"/api/v1/products/{product['id']}/publish")
    public = await client.get(f"/api/v1/products/{product['id']}")
    data = public.json()
    assert data["current_price"] == "150.00"
    assert data["active_offer"] is None


async def test_offer_invalid_price_rejected(client: httpx.AsyncClient) -> None:
    await _login(client, OWNER)
    category_id = await _create_category(client, "Televisores Test")
    product = await _create_product(client, category_id, name="TV Oferta")

    response = await client.post(
        f"/api/v1/products/{product['id']}/offers",
        json={
            "normal_price": 150,
            "offer_price": 200,
            "start_at": "2026-01-01T00:00:00Z",
            "end_at": "2030-01-01T00:00:00Z",
        },
    )
    assert response.status_code == 422


async def test_cannot_duplicate_serial_number(client: httpx.AsyncClient) -> None:
    await _login(client, OWNER)
    category_id = await _create_category(client, "Celulares Test")
    product = await _create_product(
        client, category_id, name="Celular Serial", is_serialized=True
    )

    payload = {"serial_number": "SN-DUPLICADO-001"}
    first = await client.post(
        f"/api/v1/products/{product['id']}/serials", json=payload
    )
    assert first.status_code == 201, first.text

    second = await client.post(
        f"/api/v1/products/{product['id']}/serials", json=payload
    )
    assert second.status_code == 409


async def test_serial_on_non_serialized_product_rejected(
    client: httpx.AsyncClient,
) -> None:
    await _login(client, OWNER)
    category_id = await _create_category(client, "Routers Test")
    product = await _create_product(client, category_id, name="Router Serial")

    response = await client.post(
        f"/api/v1/products/{product['id']}/serials",
        json={"serial_number": "SN-NO-SERIAL"},
    )
    assert response.status_code == 400


async def test_serial_status_change_logged(client: httpx.AsyncClient, db) -> None:
    await _login(client, OWNER)
    category_id = await _create_category(client, "Sublimación Test")
    product = await _create_product(
        client, category_id, name="Taza Serial", is_serialized=True
    )
    serial = await client.post(
        f"/api/v1/products/{product['id']}/serials",
        json={"serial_number": "SN-Estado-001"},
    )
    serial_id = serial.json()["id"]

    response = await client.put(
        f"/api/v1/products/{product['id']}/serials/{serial_id}",
        json={"status": "SOLD"},
    )
    assert response.status_code == 200, response.text
    assert response.json()["status"] == "SOLD"

    from app.modules.audit.domain.models import AuditLog
    from sqlalchemy import select

    logs = (
        await db.execute(
            select(AuditLog).where(AuditLog.entity_id == serial_id)
        )
    ).scalars().all()
    assert any(log.action == "UPDATE_SERIAL_STATUS" for log in logs)


async def test_published_product_visible_in_public_api(
    client: httpx.AsyncClient,
) -> None:
    await _login(client, OWNER)
    category_id = await _create_category(client, "Almacenamiento Test")
    product = await _create_product(client, category_id, name="SSD Público")

    # No publicado → no aparece
    public = await client.get("/api/v1/products")
    assert public.json()["total"] == 0

    # Publicado → aparece en tienda pública
    await client.post(f"/api/v1/products/{product['id']}/publish")
    public = await client.get(f"/api/v1/products/{product['id']}")
    assert public.status_code == 200
    assert public.json()["name"] == "SSD Público"
    # La respuesta pública no expone el costo
    assert "cost_price" not in public.json()

    # Despublicado → ya no aparece
    await client.post(f"/api/v1/products/{product['id']}/unpublish")
    public = await client.get(f"/api/v1/products/{product['id']}")
    assert public.status_code == 404


async def test_product_attributes_assignable(client: httpx.AsyncClient) -> None:
    await _login(client, OWNER)
    category_id = await _create_category(client, "Accesorios Test")
    attribute_id = await _create_attribute(client, "Color Test")
    product = await _create_product(client, category_id, name="Accesorio Atributo")

    response = await client.post(
        f"/api/v1/products/{product['id']}/attributes",
        json=[{"attribute_id": attribute_id, "value": "Negro"}],
    )
    assert response.status_code == 200, response.text
    attrs = response.json()["attributes"]
    assert any(a["attribute_name"] == "Color Test" and a["value"] == "Negro" for a in attrs)


async def test_duplicate_sku_rejected_at_db(client: httpx.AsyncClient, db) -> None:
    from app.modules.products.domain.models import Product

    await _login(client, OWNER)
    category_id = await _create_category(client, "Duplicados Test")
    product = await _create_product(client, category_id, name="SKU Duplicado")

    dup = Product(
        sku=product["sku"],
        name="SKU Duplicado 2",
        slug="sku-duplicado-2",
        cost_price=10,
        sale_price=20,
        currency="PEN",
    )
    db.add(dup)
    import pytest
    from sqlalchemy.exc import IntegrityError

    with pytest.raises(IntegrityError):
        await db.commit()
