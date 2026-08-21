# Seguridad — Módulo de Autenticación y Control de Acceso

> FASE 01 · Rama `feature/fase-01-auth`

Este documento describe cómo funciona la autenticación, las sesiones y el
control de acceso basado en roles (RBAC) del sistema Inversiones Hasbun.

## Índice

1. [Flujo de autenticación](#flujo-de-autenticación)
2. [Cookies de sesión](#cookies-de-sesión)
3. [Sesiones y revocación](#sesiones-y-revocación)
4. [Sistema de permisos RBAC + overrides](#sistema-de-permisos-rbac--overrides)
5. [Cache de permisos e invalidación](#cache-de-permisos-e-invalidación)
6. [Protección de endpoints](#protección-de-endpoints)
7. [Rate limiting](#rate-limiting)
8. [Cambio de contraseña](#cambio-de-contraseña)
9. [Códigos de error](#códigos-de-error)
10. [Matriz de permisos](#matriz-de-permisos)

---

## Flujo de autenticación

1. El cliente envía `POST /api/v1/auth/login` con `{email, password}`.
2. El backend verifica credenciales con **bcrypt** (cost factor ≥ 12). Nunca se
   almacena ni se loguea la contraseña en texto plano.
3. Si son correctas, se generan dos JWT (access y refresh) y se entregan **solo**
   como cookies `HttpOnly`.
4. La respuesta incluye los datos del usuario autenticado (`UserMeResponse`):
   roles y permisos efectivos.
5. El frontend usa el estado de `GET /api/v1/auth/me` para renderizar la UI.

Los tokens **nunca** se guardan en `localStorage` ni en JavaScript. El frontend
solo dispone de ellos a través de la cookie, y el refresco automático ocurre en
el interceptor del cliente axios.

### Rotación de sesión

- `POST /api/v1/auth/refresh` — lee la cookie `refresh_token`, valida que el
  `jti` siga activo en Redis y emite un par nuevo (rotación).
- `POST /api/v1/auth/logout` — revoca el `jti` del refresh token en Redis y
  limpia ambas cookies.

---

## Cookies de sesión

| Cookie | Contenido | TTL | Atributos |
|---|---|---|---|
| `access_token` | JWT corto | 60 min (configurable) | `HttpOnly`, `SameSite=lax`, `Path=/` |
| `refresh_token` | JWT de rotación | 7 días (configurable) | `HttpOnly`, `SameSite=lax`, `Path=/` |

- `Secure=True` en producción; `Secure=False` en desarrollo local (HTTP).
- `SameSite=lax` mitiga CSRF en navegadores modernos.

---

## Sesiones y revocación

Las sesiones se registran en **Redis** con TTL:

- `session:<user_id>:<jti>` → par access+refresh válido.
- `blocklist_access:<jti>` → access token revocado antes de expirar.

Acciones que revocan sesiones:

- **Logout**: revoca el refresh `jti` actual.
- **Cambio de contraseña**: revoca todas las sesiones refresh del usuario **y**
  pone el access token actual en blocklist (la sesión muere de inmediato).

---

## Sistema de permisos RBAC + overrides

Modelos: `User`, `Role`, `Permission`, `UserRole`, `RolePermission`,
`UserPermissionOverride`.

El permiso efectivo de un usuario se resuelve en este **orden de precedencia**:

1. `UserPermissionOverride.granted=False` → **denegado** (revocación explícita).
2. `UserPermissionOverride.granted=True` → **permitido** (concesión explícita).
3. Permiso asignado a alguno de sus roles → **permitido**.
4. `User.is_superuser=True` → **permitido** para todo (permiso `*`).

Ejemplo: si `SALES` tiene `ventas.crear` por rol pero el OWNER revoca ese
permiso vía override, la revocación gana. Si el OWNER concede un permiso vía
override a un rol que no lo tenía, la concesión gana.

### Endpoints de gestión de permisos

- `POST /api/v1/users/{id}/permissions` — crear/actualizar override
  (`{codename, granted, reason}`).
- `DELETE /api/v1/users/{id}/permissions/{perm_id}` — quitar override.
- `GET /api/v1/roles` y `POST/DELETE /api/v1/roles/{id}/permissions` — gestión
  de la matriz por rol.

---

## Cache de permisos e invalidación

- Los permisos efectivos del usuario se cachean en Redis con **TTL 5 minutos**
  (clave `permissions:<user_id>`), para no consultar la BD en cada request.
- La caché se **invalida inmediatamente** al:
  - crear/modificar/eliminar un override (`user_permission_overrides`),
  - asignar o quitar un rol,
  - modificar los permisos de un rol,
  - desactivar un usuario.

---

## Protección de endpoints

- `Depends(get_current_user)` → valida la cookie de access, devuelve el `User`
  o lanza **401**.
- `Depends(get_current_active_user)` → además exige `is_active=True`.
- `Depends(require_permission("modulo.accion"))` → exige el permiso efectivo o
  lanza **403**.

| Role | Acceso de ejemplo |
|---|---|
| OWNER | Todo (`is_superuser=True` en seeds) |
| SALES | `ventas.*`, `pos.operar`, `caja.abrir/cerrar`, `clientes.gestionar`, ... |
| TECHNICIAN | `reparaciones.*`, `mantenimientos.*`, `instalaciones.*`, `repuestos.*` |
| SOFTWARE_DEVELOPER | `proyectos.*`, `publicaciones.editar`, `casos_exito.*` |
| CUSTOMER | `reportes.propios` |

---

## Rate limiting

- `slowapi` limita el login a **10 intentos por minuto por IP** (devolviendo
  **429**).
- Además, el servicio registra intentos fallidos por IP en Redis; tras 10
  fallos en 15 minutos se bloquea temporalmente el login desde esa IP
  (`LOGIN_BLOCKED`).

---

## Cambio de contraseña

`POST /api/v1/auth/change-password` con `{current_password, new_password}`.

- La nueva contraseña debe cumplir: **mínimo 8 caracteres, al menos una
  mayúscula y un número** (validación en schema, 422 si no cumple).
- Revoca **todas** las sesiones activas del usuario.
- Registra `CHANGE_PASSWORD` en el audit log.
- El access token actual se blocklistea → el siguiente `GET /auth/me` devuelve
  401 y el cliente redirige a `/login`.

---

## Códigos de error

| HTTP | Significado | Endpoints típicos |
|---|---|---|
| 401 | No autenticado / sesión inválida o revocada | cualquier endpoint protegido |
| 403 | Autenticado pero sin permiso | endpoints con `require_permission` |
| 422 | Validación de entrada (incluye contraseña débil) | login, change-password, create-user |
| 429 | Demasiados intentos de login | `/auth/login` |

Formato de error:

```json
{
  "error": {
    "code": "AUTHENTICATION_ERROR",
    "message": "...",
    "details": {},
    "request_id": "..."
  }
}
```

---

## Matriz de permisos

La matriz completa por rol está en [docs/permissions.md](./permissions.md).
Los codenames se crean mediante el seed idempotente
(`apps/api/app/database/seeds/permissions.py`).