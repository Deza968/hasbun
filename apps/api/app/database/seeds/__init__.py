"""Seeders por módulo. Uso: `make seed` o `python -m app.database.seeds`."""

from __future__ import annotations

# Registrar todos los modelos para configurar mappers correctamente
# (equivalente a lo que hace alembic/env.py).
import app.modules.attributes.domain.models  # noqa: F401
import app.modules.brands.domain.models  # noqa: F401
import app.modules.categories.domain.models  # noqa: F401
import app.modules.exchange_rates.domain.models  # noqa: F401
import app.modules.files.domain.models  # noqa: F401
import app.modules.permissions.domain.models  # noqa: F401
import app.modules.products.domain.models  # noqa: F401
import app.modules.roles.domain.models  # noqa: F401
import app.modules.users.domain.models  # noqa: F401
from app.database.seeds.catalog import seed_catalog
from app.database.seeds.permissions import seed_permissions
from app.database.seeds.roles import seed_roles
from app.database.seeds.users import seed_users

__all__ = ["seed_roles", "seed_permissions", "seed_users", "seed_catalog"]
