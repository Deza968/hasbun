"""Fixtures base para tests.

- `client`: httpx AsyncClient contra la app de tests.
- `db`: sesión async de tests.
- `db_setup`: crea el esquema y siembra roles/permisos/usuarios de prueba.
- Redis: se reemplaza `redis_client` por una instancia fakeredis (sin infra).
"""

from __future__ import annotations

import os
from collections.abc import AsyncGenerator

import httpx
import pytest_asyncio
from fakeredis import aioredis as fake_aioredis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production")
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://hasbun:hasbun@localhost:5433/hasbun_test",
)
os.environ.setdefault("REDIS_URL", "redis://localhost:6380/15")

from app.database.base import Base  # noqa: E402
from app.database.seeds import (  # noqa: E402
    seed_catalog,
    seed_inventory,
    seed_permissions,
    seed_roles,
    seed_users,
)
from app.main import app  # noqa: E402

test_engine = create_async_engine(
    os.environ["DATABASE_URL"], poolclass=NullPool
)
TestSessionLocal = async_sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False
)

# El rate limit de slowapi depende de Redis real; se desactiva en tests.
app.state.limiter.enabled = False


@pytest_asyncio.fixture(autouse=True)
async def _fake_redis(monkeypatch) -> AsyncGenerator[None, None]:
    """Reemplaza el cliente Redis global por fakeredis en cada test."""
    client = fake_aioredis.FakeRedis(decode_responses=True)
    monkeypatch.setattr("app.core.redis.redis_client", client)
    yield


_V_STOCK_SQL = """
CREATE OR REPLACE VIEW v_product_stock AS
SELECT
    p.id AS product_id,
    p.sku,
    p.name AS product_name,
    p.stock_minimum,
    p.is_serialized,
    p.active,
    p.published,
    COALESCE(
        SUM(
            CASE
                WHEN m.movement_type IN ('PURCHASE','ADJUSTMENT_IN','RETURN','REPAIR_RETURN',
                                         'SALE','ADJUSTMENT_OUT','REPAIR_USAGE','DAMAGED')
                THEN m.quantity
                ELSE 0
            END
        ), 0
    ) AS physical,
    COALESCE(
        -SUM(CASE WHEN m.movement_type IN ('RESERVATION','RELEASE_RESERVATION') THEN m.quantity ELSE 0 END), 0
    ) AS reserved,
    COALESCE(
        -SUM(CASE WHEN m.movement_type = 'PARTIAL_PAYMENT_HOLD' THEN m.quantity ELSE 0 END), 0
    ) AS partially_paid,
    COALESCE(
        -SUM(CASE WHEN m.movement_type IN ('CREDIT_DELIVERY','SALE_COMPLETED') THEN m.quantity ELSE 0 END), 0
    ) AS on_credit,
    COALESCE(
        SUM(
            CASE
                WHEN m.movement_type IN ('PURCHASE','ADJUSTMENT_IN','RETURN','REPAIR_RETURN',
                                         'SALE','ADJUSTMENT_OUT','REPAIR_USAGE','DAMAGED')
                THEN m.quantity
                ELSE 0
            END
        ), 0
    ) - COALESCE(
        -SUM(CASE WHEN m.movement_type IN ('RESERVATION','RELEASE_RESERVATION') THEN m.quantity ELSE 0 END), 0
    ) - COALESCE(
        -SUM(CASE WHEN m.movement_type = 'PARTIAL_PAYMENT_HOLD' THEN m.quantity ELSE 0 END), 0
    ) - COALESCE(
        -SUM(CASE WHEN m.movement_type IN ('CREDIT_DELIVERY','SALE_COMPLETED') THEN m.quantity ELSE 0 END), 0
    ) AS available
FROM products p
LEFT JOIN inventory_movements m ON m.product_id = p.id
GROUP BY p.id
"""

_V_STOCK_SUMMARY_SQL = """
CREATE OR REPLACE VIEW v_product_stock_summary AS
SELECT
    product_id,
    sku,
    product_name,
    stock_minimum,
    is_serialized,
    active,
    published,
    physical,
    reserved,
    partially_paid,
    on_credit,
    available,
    physical AS total_physical
FROM v_product_stock
"""


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def db_setup() -> AsyncGenerator[None, None]:
    """Crea el esquema y siembra los datos base una sola vez por sesión."""
    async with test_engine.begin() as conn:
        await conn.execute(text("DROP VIEW IF EXISTS v_product_stock_summary"))
        await conn.execute(text("DROP VIEW IF EXISTS v_product_stock"))
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
        await conn.execute(text(_V_STOCK_SQL))
        await conn.execute(text(_V_STOCK_SUMMARY_SQL))
    async with TestSessionLocal() as session:
        await seed_roles(session)
        await seed_permissions(session)
        await seed_users(session)
        await seed_catalog(session)
        await seed_inventory(session)
    yield
    async with test_engine.begin() as conn:
        await conn.execute(text("DROP VIEW IF EXISTS v_product_stock_summary"))
        await conn.execute(text("DROP VIEW IF EXISTS v_product_stock"))
        await conn.run_sync(Base.metadata.drop_all)
    await test_engine.dispose()


@pytest_asyncio.fixture
async def db(db_setup: None) -> AsyncGenerator[AsyncSession, None]:
    async with TestSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def client(db_setup: None) -> AsyncGenerator[httpx.AsyncClient, None]:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport, base_url="http://testserver"
    ) as ac:
        yield ac


async def login_as(client: httpx.AsyncClient, email: str, password: str) -> int:
    """Helper: inicia sesión con el cliente y retorna el status code."""
    response = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": password}
    )
    return response.status_code
