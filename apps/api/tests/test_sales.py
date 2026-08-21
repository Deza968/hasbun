"""Tests ventas placeholder (#F04-08) — verifica endpoints existen."""
import httpx

async def test_sales_list_requires_auth(client: httpx.AsyncClient):
    resp = await client.get("/api/v1/sales")
    assert resp.status_code in (401, 403)

async def test_sales_create_requires_auth(client: httpx.AsyncClient):
    resp = await client.post("/api/v1/sales", json={})
    assert resp.status_code in (401, 403, 422)

async def test_discount_request_requires_auth(client: httpx.AsyncClient):
    resp = await client.post("/api/v1/discounts/request", json={})
    assert resp.status_code in (401, 403, 422)
