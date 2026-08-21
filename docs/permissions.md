# Matriz de Permisos por Rol

> Fuente: `apps/api/app/database/seeds/permissions.py` (seed idempotente) ·
> Referencia: REQUIREMENTS §7

Los permisos usan el formato `<módulo>.<acción>`. El sistema aplica **RBAC con
overrides** (ver [docs/security.md](./security.md)): un override por usuario
puede conceder (`granted=True`) o revocar (`granted=False`) cualquier permiso,
y tiene prioridad sobre la matriz del rol.

## Permisos disponibles

| Código | Descripción | Módulo |
|---|---|---|
| `usuarios.ver` | Ver usuarios | usuarios |
| `usuarios.crear` | Crear usuarios | usuarios |
| `usuarios.editar` | Editar usuarios | usuarios |
| `usuarios.desactivar` | Desactivar usuarios | usuarios |
| `usuarios.permisos` | Gestionar permisos de usuarios | usuarios |
| `roles.ver` | Ver roles | usuarios |
| `roles.editar` | Editar roles | usuarios |
| `auditoria.ver` | Ver auditoría | auditoria |
| `configuracion.editar` | Editar configuración del sistema | configuracion |
| `productos.ver` | Ver productos | productos |
| `productos.crear` | Crear productos | productos |
| `productos.editar` | Editar productos | productos |
| `productos.editar_costo` | Editar costo de productos | productos |
| `productos.eliminar` | Eliminar productos | productos |
| `productos.publicar` | Publicar productos | productos |
| `categorias.gestionar` | Gestionar categorías | productos |
| `marcas.gestionar` | Gestionar marcas | productos |
| `inventario.ver` | Ver inventario | inventario |
| `inventario.ajustar` | Ajustar inventario | inventario |
| `compras.crear` | Crear compras | compras |
| `compras.ver` | Ver compras | compras |
| `proveedores.gestionar` | Gestionar proveedores | compras |
| `ventas.crear` | Crear ventas | ventas |
| `ventas.ver` | Ver ventas | ventas |
| `ventas.cancelar` | Cancelar ventas | ventas |
| `ventas.descuento` | Autorizar descuentos | ventas |
| `pos.operar` | Operar el POS | ventas |
| `caja.abrir` | Abrir caja | caja |
| `caja.cerrar` | Cerrar caja | caja |
| `caja.ver_todas` | Ver cajas de todos los usuarios | caja |
| `caja.transferir` | Transferir entre cajas | caja |
| `clientes.gestionar` | Gestionar clientes | clientes |
| `cotizaciones.crear` | Crear cotizaciones | cotizaciones |
| `cotizaciones.aprobar` | Aprobar cotizaciones | cotizaciones |
| `pedidos.gestionar` | Gestionar pedidos | ventas |
| `creditos.aprobar` | Aprobar créditos | creditos |
| `creditos.ver` | Ver créditos | creditos |
| `cuotas.gestionar` | Gestionar cuotas | creditos |
| `reparaciones.crear` | Crear reparaciones | reparaciones |
| `reparaciones.ver` | Ver reparaciones | reparaciones |
| `reparaciones.diagnosticar` | Diagnosticar reparaciones | reparaciones |
| `mantenimientos.gestionar` | Gestionar mantenimientos | mantenimientos |
| `instalaciones.gestionar` | Gestionar instalaciones | instalaciones |
| `repuestos.solicitar` | Solicitar repuestos de inventario | inventario |
| `garantias.gestionar` | Gestionar garantías | garantias |
| `envios.gestionar` | Gestionar envíos | envios |
| `delivery.gestionar` | Gestionar delivery | envios |
| `proyectos.gestionar` | Gestionar proyectos de software | software |
| `publicaciones.editar` | Editar publicaciones web | software |
| `casos_exito.gestionar` | Gestionar casos de éxito | software |
| `reportes.todos` | Ver todos los reportes | reportes |
| `reportes.propios` | Ver reportes propios | reportes |

## Matriz por rol

| Permiso | OWNER | SALES | TECHNICIAN | SW_DEV | CUSTOMER |
|---|---|---|---|---|---|
| `usuarios.ver` | ✔ | | | | |
| `usuarios.crear` | ✔ | | | | |
| `usuarios.editar` | ✔ | | | | |
| `usuarios.desactivar` | ✔ | | | | |
| `usuarios.permisos` | ✔ | | | | |
| `roles.ver` | ✔ | | | | |
| `roles.editar` | ✔ | | | | |
| `auditoria.ver` | ✔ | | | | |
| `configuracion.editar` | ✔ | | | | |
| `productos.ver` | ✔ | ✔ | ✔ | | |
| `productos.crear` | ✔ | | | | |
| `productos.editar` | ✔ | | | | |
| `productos.editar_costo` | ✔ | | | | |
| `productos.eliminar` | ✔ | | | | |
| `productos.publicar` | ✔ | | | | |
| `categorias.gestionar` | ✔ | | | | |
| `marcas.gestionar` | ✔ | | | | |
| `inventario.ver` | ✔ | | | | |
| `inventario.ajustar` | ✔ | | | | |
| `compras.crear` | ✔ | | | | |
| `compras.ver` | ✔ | | | | |
| `proveedores.gestionar` | ✔ | | | | |
| `ventas.crear` | ✔ | ✔ | | | |
| `ventas.ver` | ✔ | ✔ | | | |
| `ventas.cancelar` | ✔ | | | | |
| `ventas.descuento` | ✔ | | | | |
| `pos.operar` | ✔ | ✔ | | | |
| `caja.abrir` | ✔ | ✔ | | | |
| `caja.cerrar` | ✔ | ✔ | | | |
| `caja.ver_todas` | ✔ | | | | |
| `caja.transferir` | ✔ | | | | |
| `clientes.gestionar` | ✔ | ✔ | ✔ | ✔ | |
| `cotizaciones.crear` | ✔ | ✔ | | | |
| `cotizaciones.aprobar` | ✔ | | | | |
| `pedidos.gestionar` | ✔ | ✔ | | | |
| `creditos.aprobar` | ✔ | | | | |
| `creditos.ver` | ✔ | ✔ | | | |
| `cuotas.gestionar` | ✔ | | | | |
| `reparaciones.crear` | ✔ | | ✔ | | |
| `reparaciones.ver` | ✔ | | ✔ | | |
| `reparaciones.diagnosticar` | ✔ | | ✔ | | |
| `mantenimientos.gestionar` | ✔ | | ✔ | | |
| `instalaciones.gestionar` | ✔ | | ✔ | | |
| `repuestos.solicitar` | ✔ | | ✔ | | |
| `garantias.gestionar` | ✔ | | | | |
| `envios.gestionar` | ✔ | | | | |
| `delivery.gestionar` | ✔ | | | | |
| `proyectos.gestionar` | ✔ | | | ✔ | |
| `publicaciones.editar` | ✔ | | | ✔ | |
| `casos_exito.gestionar` | ✔ | | | ✔ | |
| `reportes.todos` | ✔ | | | | |
| `reportes.propios` | ✔ | ✔ | ✔ | ✔ | ✔ |

> Nota: en los seeds, el rol `OWNER` recibe todos los permisos y el usuario
> `owner@hasbun.dev` además es `is_superuser=True` (permiso efectivo `*`).
> `CUSTOMER` solo tiene `reportes.propios`; el resto de su portal se cubre en
> fases posteriores.