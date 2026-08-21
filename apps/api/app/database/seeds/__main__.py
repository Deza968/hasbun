"""Ejecuta los seeds: `python -m app.database.seeds`."""

from __future__ import annotations

import asyncio

from app.database.base import Base
from app.database.seeds import (
    seed_cash_registers,
    seed_catalog,
    seed_credits,
    seed_customers,
    seed_inventory,
    seed_permissions,
    seed_roles,
    seed_sales,
    seed_users,
)
from app.database.session import AsyncSessionLocal, engine
from app.modules.attributes.domain import models as attributes_models  # noqa: F401
from app.modules.brands.domain import models as brands_models  # noqa: F401
from app.modules.cash.domain import models as cash_models  # noqa: F401
from app.modules.categories.domain import models as categories_models  # noqa: F401
from app.modules.credits.domain import models as credits_models  # noqa: F401
from app.modules.customers.domain import models as customers_models  # noqa: F401
from app.modules.exchange_rates.domain import models as exchange_rates_models  # noqa: F401
from app.modules.files.domain import models as files_models  # noqa: F401
from app.modules.inventory.domain import models as inventory_models  # noqa: F401
from app.modules.permissions.domain import models as permissions_models  # noqa: F401
from app.modules.products.domain import models as products_models  # noqa: F401
from app.modules.purchases.domain import models as purchases_models  # noqa: F401
from app.modules.roles.domain import models as roles_models  # noqa: F401
from app.modules.sales.domain import models as sales_models  # noqa: F401
from app.modules.suppliers.domain import models as suppliers_models  # noqa: F401
from app.modules.users.domain import models as users_models  # noqa: F401


async def main() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with AsyncSessionLocal() as db:
        print(await seed_roles(db))
        print(await seed_permissions(db))
        print(await seed_users(db))
        print(await seed_catalog(db))
        print(await seed_inventory(db))
        print(await seed_customers(db))
        print(await seed_cash_registers(db))
        print(await seed_sales(db))
        print(await seed_credits(db))
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
