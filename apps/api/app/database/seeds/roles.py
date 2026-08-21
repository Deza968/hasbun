"""Seed de roles del sistema."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.roles.domain.models import Role

ROLES: list[dict[str, str | bool]] = [
    {
        "name": "Dueña / Administradora",
        "code": "OWNER",
        "description": "Acceso total sin restricciones",
        "is_system": True,
    },
    {
        "name": "Vendedor",
        "code": "SALES",
        "description": "Ventas, POS, clientes, cotizaciones",
        "is_system": True,
    },
    {
        "name": "Técnico",
        "code": "TECHNICIAN",
        "description": "Reparaciones, mantenimientos, instalaciones",
        "is_system": True,
    },
    {
        "name": "Desarrollador de software",
        "code": "SOFTWARE_DEVELOPER",
        "description": "Proyectos, publicaciones web",
        "is_system": True,
    },
    {
        "name": "Cliente",
        "code": "CUSTOMER",
        "description": "Portal propio, compras, garantías",
        "is_system": True,
    },
]


async def seed_roles(db: AsyncSession) -> dict[str, int]:
    """Inserta los roles base de forma idempotente. Devuelve conteo."""
    existing = set((await db.execute(select(Role.code))).scalars().all())
    created = 0
    for data in ROLES:
        if data["code"] not in existing:
            db.add(Role(**data))
            created += 1
    await db.commit()
    return {"roles_created": created, "roles_total": len(ROLES)}
