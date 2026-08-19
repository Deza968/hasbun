# FASE 01 — Autenticación, Usuarios y Permisos

**Rama:** `feature/fase-01-auth`
**Objetivo:** Sistema de identidad completo. Ninguna operación posterior es posible sin este módulo.
**Prerrequisito:** FASE 00 completada y mergeada a `develop`.
**Criterio de salida:** Login funciona con cookies seguras, 403 en endpoints protegidos, 401 sin auth, auditoría registra acciones críticas.

---

## Progreso

| Completados | Total | Porcentaje |
|---|---|---|
| 0 | 22 | 0% |

---

## Issues

### BASE DE DATOS

---

#### #F01-01 — Modelos de dominio: User, Role, Permission
- **Tipo:** `[BE]` `[DB]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** FASE-00 completa

**Descripción:**
Crear los modelos SQLAlchemy para el sistema de identidad y control de acceso.

**Tareas:**
- [ ] Crear `apps/api/app/modules/users/domain/models.py`:
  ```
  User:
    id (UUID, PK)
    email (VARCHAR, unique, not null)
    username (VARCHAR, unique, not null)
    password_hash (VARCHAR, not null)
    full_name (VARCHAR)
    phone (VARCHAR)
    is_active (BOOLEAN, default True)
    is_superuser (BOOLEAN, default False)
    last_login_at (TIMESTAMPTZ)
    created_at (TIMESTAMPTZ)
    updated_at (TIMESTAMPTZ)
  ```
- [ ] Crear `apps/api/app/modules/roles/domain/models.py`:
  ```
  Role:
    id (UUID, PK)
    name (VARCHAR, unique)  — OWNER, SALES, TECHNICIAN, SOFTWARE_DEVELOPER, CUSTOMER
    description (TEXT)
    is_system (BOOLEAN)     — roles del sistema no se pueden eliminar
    created_at (TIMESTAMPTZ)
  ```
- [ ] Crear `apps/api/app/modules/permissions/domain/models.py`:
  ```
  Permission:
    id (UUID, PK)
    codename (VARCHAR, unique) — ej: "ventas.crear", "caja.cerrar"
    description (TEXT)
    module (VARCHAR)           — ventas, caja, inventario, etc.
    created_at (TIMESTAMPTZ)

  UserRole:
    user_id (UUID, FK → User)
    role_id (UUID, FK → Role)
    assigned_at (TIMESTAMPTZ)
    assigned_by (UUID, FK → User)
    PK: (user_id, role_id)

  RolePermission:
    role_id (UUID, FK → Role)
    permission_id (UUID, FK → Permission)
    PK: (role_id, permission_id)

  UserPermissionOverride:
    id (UUID, PK)
    user_id (UUID, FK → User)
    permission_id (UUID, FK → Permission)
    granted (BOOLEAN)   — True = conceder, False = revocar
    reason (TEXT)
    assigned_by (UUID, FK → User)
    created_at (TIMESTAMPTZ)
    UNIQUE: (user_id, permission_id)
  ```
- [ ] Importar todos los modelos en `alembic/env.py` para que Alembic los detecte

**Definición de terminado:**
- [ ] Modelos importan sin errores
- [ ] Mypy pasa en todos los archivos de modelos

---

#### #F01-02 — Migración Alembic: tablas de identidad
- **Tipo:** `[DB]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F01-01

**Tareas:**
- [ ] Generar migración: `alembic revision --autogenerate -m "create_identity_tables"`
- [ ] Revisar manualmente el archivo generado — nunca aplicar sin revisar
- [ ] Verificar que incluye: `users`, `roles`, `permissions`, `user_roles`, `role_permissions`, `user_permission_overrides`
- [ ] Verificar constraints: unique en email/username, FK correctos, PK compuestas
- [ ] Aplicar: `alembic upgrade head`
- [ ] Verificar en psql que las tablas existen con la estructura correcta

**Definición de terminado:**
- [ ] `alembic upgrade head` sin errores
- [ ] `alembic downgrade -1` + `alembic upgrade head` funciona (migración reversible)
- [ ] Todas las tablas y constraints presentes en PostgreSQL

---

### SEGURIDAD Y AUTH

---

#### #F01-03 — Implementar hashing de contraseñas
- **Tipo:** `[BE]` `[SEC]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F01-01

**Descripción:**
Funciones de seguridad para contraseñas. Nunca texto plano.

**Tareas:**
- [ ] Crear `apps/api/app/core/security.py`:
  - `hash_password(password: str) -> str` — bcrypt con salt
  - `verify_password(plain: str, hashed: str) -> bool`
  - `create_session_token(data: dict) -> str` — JWT firmado
  - `decode_session_token(token: str) -> dict` — decodificar y verificar
- [ ] Configurar bcrypt con cost factor mínimo 12
- [ ] Nunca loguear contraseñas en ningún punto del flujo

**Definición de terminado:**
- [ ] `verify_password("abc", hash_password("abc"))` → True
- [ ] `verify_password("xyz", hash_password("abc"))` → False
- [ ] Test unitario cubre ambos casos

---

#### #F01-04 — Implementar servicio de autenticación
- **Tipo:** `[BE]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F01-02, #F01-03

**Descripción:**
Lógica de negocio de autenticación: login, logout, refresh de sesión.

**Tareas:**
- [ ] Crear `apps/api/app/modules/auth/application/service.py`:
  - `login(email, password, ip, user_agent) -> TokenPair`
    - Buscar usuario por email
    - Verificar contraseña con bcrypt
    - Verificar `is_active = True`
    - Registrar `last_login_at`
    - Generar access token + refresh token
    - Registrar en AuditLog: `LOGIN_SUCCESS`
    - Si falla: AuditLog `LOGIN_FAILED` (sin revelar si email existe)
  - `logout(user_id, session_id)`
    - Invalidar sesión en Redis (blocklist)
    - AuditLog: `LOGOUT`
  - `refresh(refresh_token) -> TokenPair`
    - Verificar refresh token en Redis
    - Generar nuevos tokens
    - Invalidar tokens anteriores
- [ ] Implementar sesiones en Redis con TTL configurable
- [ ] Rate limiting: máx. 10 intentos de login fallidos por IP en 15 minutos → bloqueo temporal

**Definición de terminado:**
- [ ] Login exitoso genera tokens
- [ ] Login con contraseña incorrecta → error sin revelar si email existe
- [ ] Logout invalida la sesión inmediatamente
- [ ] Test: 11 intentos fallidos → bloqueo

---

#### #F01-05 — Implementar cookies HttpOnly Secure
- **Tipo:** `[BE]` `[SEC]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F01-04

**Descripción:**
Los tokens de sesión deben vivir SOLO en cookies HttpOnly. Nunca en localStorage.

**Tareas:**
- [ ] Crear `apps/api/app/modules/auth/api/router.py`:
  - `POST /api/v1/auth/login` — recibe `{email, password}`, responde seteando cookies
  - `POST /api/v1/auth/logout` — limpia cookies
  - `POST /api/v1/auth/refresh` — rota tokens usando cookie de refresh
  - `GET /api/v1/auth/me` — retorna datos del usuario autenticado
- [ ] Cookies con atributos: `HttpOnly=True`, `Secure=True` (prod), `SameSite="lax"`, `Path="/"`
- [ ] Access token TTL: 60 minutos (configurable)
- [ ] Refresh token TTL: 7 días (configurable)
- [ ] En desarrollo: `Secure=False` para HTTP local

**Definición de terminado:**
- [ ] `POST /auth/login` exitoso → cookies seteadas en respuesta
- [ ] Cookies no son accesibles desde JavaScript (`HttpOnly`)
- [ ] `GET /auth/me` sin cookie → 401
- [ ] `GET /auth/me` con cookie válida → datos del usuario

---

#### #F01-06 — Implementar middleware de autenticación
- **Tipo:** `[BE]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F01-05

**Descripción:**
Dependency de FastAPI que extrae y valida el usuario autenticado en cada request protegido.

**Tareas:**
- [ ] Crear `apps/api/app/core/dependencies.py`:
  - `get_current_user(request: Request) -> User` — lee cookie, valida token, retorna User
  - `get_current_active_user(user: User = Depends(get_current_user)) -> User` — verifica `is_active`
  - `require_permission(codename: str)` — factory que retorna dependency que verifica permiso
- [ ] `require_permission` verifica en este orden:
  1. `UserPermissionOverride` con `granted=False` → denegar
  2. `UserPermissionOverride` con `granted=True` → permitir
  3. `RolePermission` del rol del usuario → verificar
  4. Si es superuser (`is_superuser=True`) → permitir todo
- [ ] Caché de permisos del usuario en Redis (TTL 5 minutos para no consultar BD en cada request)
- [ ] Invalidar caché al modificar permisos

**Definición de terminado:**
- [ ] Endpoint sin `Depends(get_current_user)` → acceso sin auth
- [ ] Endpoint con `Depends(get_current_user)` → 401 sin cookie
- [ ] Endpoint con `Depends(require_permission("ventas.crear"))` → 403 si no tiene permiso
- [ ] Test de cada caso

---

### MÓDULO USERS

---

#### #F01-07 — CRUD de usuarios
- **Tipo:** `[BE]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F01-06

**Tareas:**
- [ ] Crear `apps/api/app/modules/users/infrastructure/repository.py`:
  - `get_by_id`, `get_by_email`, `get_by_username`, `list_users`, `create`, `update`, `deactivate`
- [ ] Crear `apps/api/app/modules/users/application/service.py`:
  - `create_user(data, created_by)` — solo OWNER puede crear usuarios
  - `update_user(id, data, updated_by)` — solo OWNER puede modificar
  - `deactivate_user(id, deactivated_by)` — soft delete
  - `assign_role(user_id, role_id, assigned_by)` — solo OWNER
  - `remove_role(user_id, role_id, removed_by)` — solo OWNER
- [ ] Crear `apps/api/app/modules/users/application/schemas.py`:
  - `UserCreate`, `UserUpdate`, `UserResponse`, `UserListResponse`
- [ ] Crear `apps/api/app/modules/users/api/router.py`:
  - `GET /api/v1/users` — lista (solo OWNER)
  - `POST /api/v1/users` — crear (solo OWNER)
  - `GET /api/v1/users/{id}` — detalle (solo OWNER)
  - `PUT /api/v1/users/{id}` — modificar (solo OWNER)
  - `DELETE /api/v1/users/{id}` — desactivar (solo OWNER)
  - `POST /api/v1/users/{id}/roles` — asignar rol (solo OWNER)
  - `DELETE /api/v1/users/{id}/roles/{role_id}` — quitar rol (solo OWNER)

**Definición de terminado:**
- [ ] CRUD completo funciona
- [ ] SALES intenta crear usuario → 403
- [ ] AuditLog registra creación y modificación de usuarios

---

#### #F01-08 — CRUD de roles y permisos
- **Tipo:** `[BE]`
- **Prioridad:** 🟠 ALTO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F01-06

**Tareas:**
- [ ] Crear repositorios y servicios para Role y Permission
- [ ] `GET /api/v1/roles` — lista todos los roles (solo OWNER)
- [ ] `GET /api/v1/roles/{id}/permissions` — permisos de un rol (solo OWNER)
- [ ] `POST /api/v1/roles/{id}/permissions` — asignar permiso a rol (solo OWNER)
- [ ] `DELETE /api/v1/roles/{id}/permissions/{perm_id}` — quitar permiso de rol (solo OWNER)
- [ ] `GET /api/v1/permissions` — lista todos los permisos (solo OWNER)
- [ ] `POST /api/v1/users/{id}/permissions` — override de permiso individual (solo OWNER)
- [ ] `DELETE /api/v1/users/{id}/permissions/{perm_id}` — quitar override (solo OWNER)
- [ ] Invalidar caché de permisos en Redis al modificar

**Definición de terminado:**
- [ ] OWNER puede asignar/quitar permisos
- [ ] Cambio de permiso invalida caché del usuario afectado inmediatamente
- [ ] AuditLog registra cada cambio de permiso con OWNER como `authorized_by`

---

### AUDITORÍA BASE

---

#### #F01-09 — Modelo y servicio de auditoría
- **Tipo:** `[BE]` `[DB]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F01-02

**Descripción:**
El módulo de auditoría es transversal. Se implementa ahora porque todos los módulos posteriores lo usan.

**Tareas:**
- [ ] Crear `apps/api/app/modules/audit/domain/models.py`:
  ```
  AuditLog:
    id (UUID, PK)
    user_id (UUID, FK → User, nullable — para eventos de sistema)
    action (VARCHAR, not null)     — ej: LOGIN_SUCCESS, CREATE_SALE
    module (VARCHAR, not null)     — auth, ventas, caja, etc.
    entity_type (VARCHAR)          — User, Sale, CashSession, etc.
    entity_id (UUID)
    old_values (JSONB)
    new_values (JSONB)
    authorization_id (UUID)        — si la acción fue autorizada por otro usuario
    ip_address (VARCHAR)
    user_agent (TEXT)
    request_id (UUID)
    timestamp (TIMESTAMPTZ, not null, index)
  ```
- [ ] Migración para `audit_logs`
- [ ] Crear `apps/api/app/modules/audit/application/service.py`:
  - `log(action, module, entity_type, entity_id, old_values, new_values, context)` — async
  - El servicio nunca lanza excepción: si falla el log, registra en logger pero no interrumpe el flujo
- [ ] Crear `apps/api/app/modules/audit/api/router.py`:
  - `GET /api/v1/audit` — listado con filtros (solo OWNER)
  - Filtros: módulo, usuario, acción, fecha desde/hasta, entity_type, entity_id
  - Paginación obligatoria

**Definición de terminado:**
- [ ] `audit_service.log(...)` no lanza excepción incluso si hay error de BD
- [ ] OWNER puede consultar auditoría con filtros
- [ ] SALES intenta ver auditoría → 403
- [ ] Los registros son inmutables (no hay endpoint de update/delete)

---

### SEEDS DE AUTH

---

#### #F01-10 — Seeds de roles, permisos y usuarios de desarrollo
- **Tipo:** `[BE]` `[DB]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F01-02, #F01-08

**Descripción:**
Poblar la BD con roles, permisos y usuarios ficticios para desarrollo y tests.

**Tareas:**
- [ ] Seed de roles del sistema: `OWNER`, `SALES`, `TECHNICIAN`, `SOFTWARE_DEVELOPER`, `CUSTOMER`
- [ ] Seed de permisos (codenames completos para todos los módulos):
  ```
  Ejemplos:
  ventas.crear, ventas.cancelar, ventas.descuento
  caja.abrir, caja.cerrar, caja.ver_todas, caja.transferir
  inventario.ver, inventario.ajustar
  creditos.aprobar, creditos.ver
  reparaciones.crear, reparaciones.diagnosticar
  usuarios.crear, usuarios.editar, usuarios.permisos
  auditoria.ver
  reportes.todos, reportes.propios
  ... (lista completa basada en REQUIREMENTS §7)
  ```
- [ ] Asignar permisos a roles según la matriz de permisos de REQUIREMENTS §7
- [ ] Seed de usuarios ficticios (datos falsos, no reales):
  - `owner@hasbun.test` / `Owner2026!` — rol OWNER
  - `ventas@hasbun.test` / `Ventas2026!` — rol SALES
  - `tecnico@hasbun.test` / `Tecnico2026!` — rol TECHNICIAN
  - `software@hasbun.test` / `Software2026!` — rol SOFTWARE_DEVELOPER
  - `cliente@hasbun.test` / `Cliente2026!` — rol CUSTOMER
- [ ] El seed es idempotente

**Definición de terminado:**
- [ ] `make seed` crea todos los roles, permisos y usuarios sin error
- [ ] Login con `owner@hasbun.test` funciona y retorna cookie
- [ ] Login con `ventas@hasbun.test` funciona con permisos correctos

---

### FRONTEND AUTH

---

#### #F01-11 — Página de login
- **Tipo:** `[FE]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F01-05

**Tareas:**
- [ ] Crear `apps/web/app/(auth)/login/page.tsx`
- [ ] Formulario con React Hook Form + Zod: `email` y `password`
- [ ] Llamada a `POST /api/v1/auth/login` via API client
- [ ] Al login exitoso: redirigir según rol del usuario:
  - OWNER, SALES, TECHNICIAN, SW_DEV → `/admin/dashboard`
  - CUSTOMER → `/customer/dashboard`
- [ ] Manejo de errores: credenciales inválidas, cuenta inactiva, rate limit
- [ ] Loading state en el botón (previene doble submit)
- [ ] Diseño con shadcn/ui, responsive

**Definición de terminado:**
- [ ] Login exitoso redirige al dashboard correcto
- [ ] Credenciales incorrectas muestra mensaje de error sin revelar si el email existe
- [ ] El botón se deshabilita durante el request

---

#### #F01-12 — Protección de rutas y layout admin
- **Tipo:** `[FE]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F01-11

**Tareas:**
- [ ] Crear `apps/web/app/admin/layout.tsx` con:
  - Verificación de autenticación (llama `GET /auth/me`)
  - Si no autenticado → redirect a `/login`
  - Sidebar con navegación completa (todos los módulos del panel)
  - Header con nombre de usuario, rol y botón de logout
- [ ] Crear `apps/web/hooks/useCurrentUser.ts` — TanStack Query para datos del usuario actual
- [ ] Crear `apps/web/hooks/usePermission.ts` — verifica si el usuario tiene un permiso
- [ ] Implementar logout: llama `POST /auth/logout`, limpia estado local, redirige a `/login`
- [ ] Sidebar colapsable para pantallas pequeñas
- [ ] Indicador de notificaciones no leídas en header (preparar estructura, implementar contenido en FASE 12)

**Definición de terminado:**
- [ ] Acceder a `/admin/*` sin sesión → redirige a `/login`
- [ ] Logout funciona correctamente
- [ ] Sidebar muestra solo secciones según rol (TECHNICIAN no ve sección Caja, etc.)

---

#### #F01-13 — Layout portal del cliente
- **Tipo:** `[FE]`
- **Prioridad:** 🟡 MEDIO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F01-11

**Tareas:**
- [ ] Crear `apps/web/app/customer/layout.tsx`
- [ ] Navegación simplificada: Mis compras, Mis cuotas, Mis reparaciones, Mi perfil
- [ ] Protección igual que admin layout

**Definición de terminado:**
- [ ] CUSTOMER autenticado accede a `/customer/*`
- [ ] CUSTOMER no puede acceder a `/admin/*` → redirige a `/customer/dashboard`

---

### TESTS

---

#### #F01-14 — Tests de autenticación
- **Tipo:** `[TEST]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F01-05, #F01-10

**Tareas:**
- [ ] `test_login_success` — credenciales correctas → 200, cookies seteadas
- [ ] `test_login_wrong_password` — contraseña incorrecta → 401, sin revelar info
- [ ] `test_login_inactive_user` — usuario inactivo → 401
- [ ] `test_login_rate_limit` — 11 intentos fallidos → 429
- [ ] `test_logout` — logout limpia sesión, siguiente request → 401
- [ ] `test_refresh_token` — refresh válido → nuevos tokens
- [ ] `test_refresh_invalid` — token inválido → 401
- [ ] `test_get_me_authenticated` — con cookie → 200 + datos de usuario
- [ ] `test_get_me_unauthenticated` — sin cookie → 401

---

#### #F01-15 — Tests de permisos
- **Tipo:** `[TEST]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F01-06, #F01-10

**Tareas:**
- [ ] `test_owner_can_create_user` → 201
- [ ] `test_sales_cannot_create_user` → 403
- [ ] `test_technician_cannot_see_audit` → 403
- [ ] `test_customer_cannot_access_admin` → 403
- [ ] `test_permission_override_grant` — SALES con override puede hacer acción vedada → 200
- [ ] `test_permission_override_revoke` — OWNER con override revocado no puede → 403
- [ ] `test_superuser_can_do_everything` → 200 en cualquier endpoint
- [ ] `test_unauthenticated_request` → 401 en cualquier endpoint protegido

---

#### #F01-16 — Tests de auditoría
- **Tipo:** `[TEST]`
- **Prioridad:** 🟠 ALTO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F01-09

**Tareas:**
- [ ] `test_login_creates_audit_log` — login exitoso crea AuditLog con action=LOGIN_SUCCESS
- [ ] `test_failed_login_creates_audit_log` — login fallido crea AuditLog con action=LOGIN_FAILED
- [ ] `test_create_user_creates_audit_log` — creación de usuario auditada
- [ ] `test_permission_change_creates_audit_log` — cambio de permiso auditado
- [ ] `test_audit_logs_immutable` — no hay endpoint de DELETE en audit logs

---

### DOCUMENTACIÓN

---

#### #F01-17 — Documentar módulo de auth en docs/security.md
- **Tipo:** `[DOCS]`
- **Prioridad:** 🟡 MEDIO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F01-05

**Tareas:**
- [ ] Documentar el flujo de autenticación completo
- [ ] Documentar el sistema de permisos RBAC + overrides
- [ ] Documentar los codenames de permisos completos
- [ ] Documentar el flujo de invalidación de caché de permisos
- [ ] Crear `docs/permissions.md` con matriz completa de permisos por rol

---

#### #F01-18 — Documentar API de auth en OpenAPI
- **Tipo:** `[DOCS]`
- **Prioridad:** 🟡 MEDIO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F01-05

**Tareas:**
- [ ] Verificar que todos los endpoints tienen docstrings y descripciones en OpenAPI
- [ ] Verificar que los schemas de request/response están documentados
- [ ] Verificar que los códigos de error están documentados (401, 403, 422, 429)
- [ ] Swagger UI accesible en `http://localhost:8000/docs`

---

### VERIFICACIÓN FINAL

---

#### #F01-19 — Cambio de contraseña
- **Tipo:** `[BE]` `[FE]`
- **Prioridad:** 🟠 ALTO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F01-07

**Tareas:**
- [ ] `POST /api/v1/auth/change-password` — requiere contraseña actual + nueva
- [ ] Validar que la nueva contraseña cumple requisitos mínimos (8+ chars, 1 mayúscula, 1 número)
- [ ] Invalidar todas las sesiones activas al cambiar contraseña
- [ ] AuditLog: `CHANGE_PASSWORD`
- [ ] Frontend: formulario en perfil de usuario

---

#### #F01-20 — Gestión de perfil de usuario
- **Tipo:** `[BE]` `[FE]`
- **Prioridad:** 🟡 MEDIO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F01-07

**Tareas:**
- [ ] `GET /api/v1/users/me` — ver perfil propio
- [ ] `PUT /api/v1/users/me` — actualizar nombre, teléfono (no email, no rol)
- [ ] Frontend: página de perfil en panel admin y portal cliente

---

#### #F01-21 — Panel de usuarios en frontend (admin)
- **Tipo:** `[FE]`
- **Prioridad:** 🟡 MEDIO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F01-07, #F01-08

**Tareas:**
- [ ] Crear `apps/web/app/admin/usuarios/page.tsx` — tabla de usuarios
- [ ] Crear `apps/web/app/admin/usuarios/nuevo/page.tsx` — formulario de creación
- [ ] Crear `apps/web/app/admin/usuarios/[id]/page.tsx` — detalle con roles y permisos
- [ ] Filtros: rol, estado (activo/inactivo)
- [ ] Acción de desactivar usuario con confirmación
- [ ] Solo visible para OWNER

---

#### #F01-22 — Verificación final de FASE 01
- **Tipo:** `[INFRA]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** Todos los anteriores

**Checklist de salida de fase:**
- [ ] Login funciona con cookies HttpOnly
- [ ] Logout invalida sesión inmediatamente
- [ ] 401 en endpoints protegidos sin autenticación
- [ ] 403 en endpoints sin el permiso requerido
- [ ] OWNER tiene acceso completo
- [ ] SALES, TECHNICIAN, SW_DEV, CUSTOMER tienen acceso restringido según matriz
- [ ] AuditLog registra login, logout, creación de usuario, cambios de permiso
- [ ] Cambio de permiso invalida caché en Redis
- [ ] Seeds funcionan y crean los 5 usuarios de desarrollo
- [ ] CI verde (lint + typecheck + todos los tests)
- [ ] Swagger UI documenta todos los endpoints de auth
- [ ] PR mergeado a `develop`

---

## Resumen de dependencias FASE 01

```
FASE-00
  └── #F01-01 (modelos)
        └── #F01-02 (migración)
              ├── #F01-03 (security) → #F01-04 (auth service)
              │                              └── #F01-05 (cookies)
              │                                    └── #F01-06 (middleware)
              │                                          ├── #F01-07 (users CRUD)
              │                                          │     └── #F01-19 (cambio pw)
              │                                          │     └── #F01-20 (perfil)
              │                                          └── #F01-08 (roles/permisos)
              ├── #F01-09 (auditoría)
              └── #F01-10 (seeds)
                    ├── #F01-14 (tests auth)
                    └── #F01-15 (tests permisos)
  Frontend:
    #F01-11 (login page) → #F01-12 (admin layout) → #F01-21 (panel usuarios)
                        → #F01-13 (customer layout)
  Tests: #F01-16 (audit tests)
  Docs:  #F01-17 (security.md), #F01-18 (OpenAPI)
  Final: #F01-22 (verificación)
```

---

*Referencia: [REQUIREMENTS.md](../REQUIREMENTS.md) §7 Usuarios y Permisos, §32 Seguridad, §26 Auditoría*
*Fase anterior: [FASE 00](FASE-00-fundacion.md) | Siguiente fase: [FASE 02](FASE-02-catalogo.md)*
