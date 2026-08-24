"""Seed de permisos del sistema según matriz REQUIREMENTS §7."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.permissions.domain.models import Permission
from app.modules.roles.domain.models import Role

# (codename, descripción, módulo)
PERMISSIONS: list[tuple[str, str, str]] = [
    # Usuarios y permisos
    ("usuarios.ver", "Ver usuarios", "usuarios"),
    ("usuarios.crear", "Crear usuarios", "usuarios"),
    ("usuarios.editar", "Editar usuarios", "usuarios"),
    ("usuarios.desactivar", "Desactivar usuarios", "usuarios"),
    ("usuarios.permisos", "Gestionar permisos de usuarios", "usuarios"),
    ("roles.ver", "Ver roles", "usuarios"),
    ("roles.editar", "Editar roles", "usuarios"),
    ("auditoria.ver", "Ver auditoría", "auditoria"),
    ("configuracion.editar", "Editar configuración del sistema", "configuracion"),
    # Productos y catálogo
    ("productos.ver", "Ver productos", "productos"),
    ("productos.crear", "Crear productos", "productos"),
    ("productos.editar", "Editar productos", "productos"),
    ("productos.editar_costo", "Editar costo de productos", "productos"),
    ("productos.eliminar", "Eliminar productos", "productos"),
    ("productos.publicar", "Publicar productos", "productos"),
    ("categorias.gestionar", "Gestionar categorías", "productos"),
    ("marcas.gestionar", "Gestionar marcas", "productos"),
    # Inventario y compras
    ("inventario.ver", "Ver inventario", "inventario"),
    ("inventario.ajustar", "Ajustar inventario", "inventario"),
    ("compras.crear", "Crear compras", "compras"),
    ("compras.ver", "Ver compras", "compras"),
    ("proveedores.gestionar", "Gestionar proveedores", "compras"),
    # Ventas, POS y caja
    ("ventas.crear", "Crear ventas", "ventas"),
    ("ventas.ver", "Ver ventas", "ventas"),
    ("ventas.cancelar", "Cancelar ventas", "ventas"),
    ("ventas.descuento", "Autorizar descuentos", "ventas"),
    ("pos.operar", "Operar el POS", "ventas"),
    ("caja.abrir", "Abrir caja", "caja"),
    ("caja.cerrar", "Cerrar caja", "caja"),
    ("caja.ver_todas", "Ver cajas de todos los usuarios", "caja"),
    ("caja.transferir", "Transferir entre cajas", "caja"),
    ("clientes.gestionar", "Gestionar clientes", "clientes"),
    ("cotizaciones.crear", "Crear cotizaciones", "cotizaciones"),
    ("cotizaciones.aprobar", "Aprobar cotizaciones", "cotizaciones"),
    ("cotizaciones.ver", "Ver cotizaciones", "cotizaciones"),
    ("whatsapp.gestionar", "Gestionar panel de WhatsApp", "whatsapp"),
    ("pedidos.gestionar", "Gestionar pedidos", "ventas"),
    # Créditos y cuotas
    ("creditos.aprobar", "Aprobar créditos", "creditos"),
    ("creditos.ver", "Ver créditos", "creditos"),
    ("cuotas.gestionar", "Gestionar cuotas", "creditos"),
    # Reparaciones, mantenimientos, instalaciones
    ("reparaciones.crear", "Crear reparaciones", "reparaciones"),
    ("reparaciones.ver", "Ver reparaciones", "reparaciones"),
    ("reparaciones.diagnosticar", "Diagnosticar reparaciones", "reparaciones"),
    ("mantenimientos.gestionar", "Gestionar mantenimientos", "mantenimientos"),
    ("instalaciones.gestionar", "Gestionar instalaciones", "instalaciones"),
    ("repuestos.solicitar", "Solicitar repuestos de inventario", "inventario"),
    # Garantías, envíos, delivery
    ("garantias.gestionar", "Gestionar garantías", "garantias"),
    ("envios.gestionar", "Gestionar envíos", "envios"),
    ("delivery.gestionar", "Gestionar delivery", "envios"),
    # Software y web
    ("proyectos.gestionar", "Gestionar proyectos de software", "software"),
    ("publicaciones.editar", "Editar publicaciones web", "software"),
    ("casos_exito.gestionar", "Gestionar casos de éxito", "software"),
    # Reportes
    ("reportes.todos", "Ver todos los reportes", "reportes"),
    ("reportes.propios", "Ver reportes propios", "reportes"),
]

# Permisos por rol (matriz REQUIREMENTS §7)
ROLE_PERMISSIONS: dict[str, list[str]] = {
    "OWNER": [codename for codename, _, _ in PERMISSIONS],
    "SALES": [
        "ventas.crear",
        "ventas.ver",
        "pos.operar",
        "caja.abrir",
        "caja.cerrar",
        "clientes.gestionar",
        "productos.ver",
        "cotizaciones.crear",
        "cotizaciones.ver",
        "pedidos.gestionar",
        "creditos.ver",
        "reportes.propios",
    ],
    "TECHNICIAN": [
        "reparaciones.crear",
        "reparaciones.ver",
        "reparaciones.diagnosticar",
        "mantenimientos.gestionar",
        "instalaciones.gestionar",
        "repuestos.solicitar",
        "clientes.gestionar",
        "productos.ver",
        "reportes.propios",
    ],
    "SOFTWARE_DEVELOPER": [
        "proyectos.gestionar",
        "publicaciones.editar",
        "casos_exito.gestionar",
        "clientes.gestionar",
        "reportes.propios",
    ],
    "CUSTOMER": [
        "reportes.propios",
    ],
}


async def seed_permissions(db: AsyncSession) -> dict[str, int]:
    """Inserta permisos y los asigna a roles de forma idempotente."""
    existing = set((await db.execute(select(Permission.codename))).scalars().all())
    permission_ids: dict[str, object] = {}
    created = 0
    for codename, description, module in PERMISSIONS:
        if codename not in existing:
            perm = Permission(codename=codename, description=description, module=module)
            db.add(perm)
            await db.flush()
            created += 1
        else:
            perm = (
                await db.execute(select(Permission).where(Permission.codename == codename))
            ).scalar_one()
        permission_ids[codename] = perm.id

    roles = {role.code: role for role in (await db.execute(select(Role))).scalars().all()}
    assigned = 0
    for role_code, codenames in ROLE_PERMISSIONS.items():
        role = roles.get(role_code)
        if role is None:
            continue
        for codename in codenames:
            perm_id = permission_ids[codename]
            # verificar si ya está asignado
            exists = await db.execute(
                select(Role)
                .join(Role.permissions)
                .where(Role.id == role.id, Permission.id == perm_id)
            )
            if exists.scalar_one_or_none() is None:
                role.permissions.append(
                    (
                        await db.execute(
                            select(Permission).where(Permission.id == perm_id)
                        )
                    ).scalar_one()
                )
                assigned += 1

    await db.commit()
    return {
        "permissions_created": created,
        "permissions_total": len(PERMISSIONS),
        "assignments": assigned,
    }
