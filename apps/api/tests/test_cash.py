"""Tests caja placeholder (#F04-02)."""
import httpx

async def test_cash_active_requires_auth(client: httpx.AsyncClient):
    resp = await client.get("/api/v1/cash/sessions/active")
    assert resp.status_code in (401, 403)

async def test_cash_open_requires_auth(client: httpx.AsyncClient):
    resp = await client.post("/api/v1/cash/sessions/open", json={})
    assert resp.status_code in (401, 403, 422)

async def test_cash_registers_requires_auth(client: httpx.AsyncClient):
    resp = await client.get("/api/v1/cash/registers")
    assert resp.status_code in (401, 403)
