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
from app.database.seeds import seed_catalog, seed_permissions, seed_roles, seed_users  # noqa: E402
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
    client = fake_aioredis.FakeRedis()
    monkeypatch.setattr("app.core.redis.redis_client", client)
    yield


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def db_setup() -> AsyncGenerator[None, None]:
    """Crea el esquema y siembra los datos base una sola vez por sesión."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    async with TestSessionLocal() as session:
        await seed_roles(session)
        await seed_permissions(session)
        await seed_users(session)
        await seed_catalog(session)
    yield
    async with test_engine.begin() as conn:
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
