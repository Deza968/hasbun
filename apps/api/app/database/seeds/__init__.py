"""Seeders por módulo. Uso: `make seed` o `python -m app.database.seeds`."""

from __future__ import annotations

from app.database.seeds.permissions import seed_permissions
from app.database.seeds.roles import seed_roles
from app.database.seeds.users import seed_users

__all__ = ["seed_roles", "seed_permissions", "seed_users"]
