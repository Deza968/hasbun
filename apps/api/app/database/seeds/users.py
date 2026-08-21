"""Seed de usuarios ficticios de desarrollo (uno por rol)."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.modules.roles.domain.models import Role
from app.modules.users.domain.models import User

# (email, username, nombre, rol, teléfono)
USERS: list[tuple[str, str, str, str, str]] = [
    ("owner@hasbun.dev", "owner", "Dueña Hasbun", "OWNER", "900000001"),
    ("ventas@hasbun.dev", "ventas", "Vendedor Demo", "SALES", "900000002"),
    ("tecnico@hasbun.dev", "tecnico", "Técnico Demo", "TECHNICIAN", "900000003"),
    ("software@hasbun.dev", "software", "Dev Demo", "SOFTWARE_DEVELOPER", "900000004"),
    ("cliente@hasbun.dev", "cliente", "Cliente Demo", "CUSTOMER", "900000005"),
]

DEV_PASSWORDS: dict[str, str] = {
    "owner@hasbun.dev": "Owner2026!",
    "ventas@hasbun.dev": "Ventas2026!",
    "tecnico@hasbun.dev": "Tecnico2026!",
    "software@hasbun.dev": "Software2026!",
    "cliente@hasbun.dev": "Cliente2026!",
}


async def seed_users(db: AsyncSession) -> dict[str, int]:
    """Inserta un usuario por rol (contraseñas de desarrollo) de forma idempotente."""
    result = await db.execute(select(Role))
    roles = {role.code: role for role in result.scalars().all()}

    existing_emails = set((await db.execute(select(User.email))).scalars().all())
    created = 0
    for email, username, name, role_code, phone in USERS:
        if email in existing_emails:
            continue
        role = roles[role_code]
        user = User(
            email=email,
            username=username,
            full_name=name,
            phone=phone,
            password_hash=hash_password(DEV_PASSWORDS[email]),
            is_active=True,
            is_superuser=(role_code == "OWNER"),
        )
        user.roles.append(role)
        db.add(user)
        created += 1
    await db.commit()
    return {"users_created": created, "users_total": len(USERS)}
