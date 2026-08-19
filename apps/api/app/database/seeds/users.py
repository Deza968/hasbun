"""Seed de usuarios ficticios de desarrollo (uno por rol)."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.modules.auth.domain.models import Role, User

# (email, nombre, rol, teléfono)
USERS: list[tuple[str, str, str, str]] = [
    ("owner@hasbun.local", "Dueña Hasbun", "OWNER", "900000001"),
    ("ventas@hasbun.local", "Vendedor Demo", "SALES", "900000002"),
    ("tecnico@hasbun.local", "Técnico Demo", "TECHNICIAN", "900000003"),
    ("dev@hasbun.local", "Dev Demo", "SOFTWARE_DEVELOPER", "900000004"),
    ("cliente@hasbun.local", "Cliente Demo", "CUSTOMER", "900000005"),
]

# Contraseña de desarrollo compartida (solo entorno local/CI)
DEV_PASSWORD = "Hasbun123!"  # noqa: S105


async def seed_users(db: AsyncSession) -> dict[str, int]:
    """Inserta un usuario por rol (contraseña de desarrollo) de forma idempotente."""
    result = await db.execute(select(Role))
    roles = {role.code: role for role in result.scalars().all()}

    existing_emails = set(
        (await db.execute(select(User.email))).scalars().all()
    )
    created = 0
    for email, name, role_code, phone in USERS:
        if email in existing_emails:
            continue
        role = roles[role_code]
        db.add(
            User(
                email=email,
                full_name=name,
                phone=phone,
                hashed_password=hash_password(DEV_PASSWORD),
                is_active=True,
                role_id=role.id,
            )
        )
        created += 1
    await db.commit()
    return {"users_created": created, "users_total": len(USERS)}
