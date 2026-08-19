"""Ejecuta los seeds: `python -m app.database.seeds`."""

from __future__ import annotations

import asyncio

import app.modules.auth.domain.models  # noqa: F401 - registrar modelos
from app.database.base import Base
from app.database.seeds import seed_roles, seed_users
from app.database.session import AsyncSessionLocal, engine


async def main() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with AsyncSessionLocal() as db:
        print(await seed_roles(db))
        print(await seed_users(db))
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
