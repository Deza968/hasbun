"""Fixtures base para tests.

- `client`: httpx AsyncClient contra la app de tests.
- `db`: sesión async de tests con rollback por test.
- `db_setup`: crea el esquema de tests (usar DATABASE_URL_TEST).
"""

from __future__ import annotations

import asyncio
import os
from collections.abc import AsyncGenerator

import httpx
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://hasbun:hasbun@localhost:5432/hasbun_test")

from app.database.base import Base  # noqa: E402
from app.main import app  # noqa: E402

test_engine = create_async_engine(os.environ["DATABASE_URL"])
TestSessionLocal = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def db_setup() -> AsyncGenerator[None, None]:
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await test_engine.dispose()


@pytest_asyncio.fixture
async def db(db_setup: None) -> AsyncGenerator[AsyncSession, None]:
    async with TestSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[httpx.AsyncClient, None]:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport, base_url="http://testserver"
    ) as ac:
        yield ac


@pytest_asyncio.fixture
async def client_db(db_setup: None, client: httpx.AsyncClient) -> httpx.AsyncClient:
    return client
