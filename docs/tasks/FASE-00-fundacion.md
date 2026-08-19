# FASE 00 — Fundación y Arquitectura

**Rama:** `feature/fase-00-fundacion`
**Objetivo:** Base técnica sólida y reproducible. Todo el equipo puede levantar el proyecto con un solo comando.
**Prerrequisito:** Ninguno. Esta es la primera fase.
**Criterio de salida:** `docker-compose up` levanta todos los servicios, `/health` responde 200, CI pasa en verde.

---

## Progreso

| Completados | Total | Porcentaje |
|---|---|---|
| 0 | 18 | 0% |

---

## Issues

### INFRA

---

#### #F00-01 — Inicializar repositorio Git con estructura base
- **Tipo:** `[INFRA]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Asignado a:** —
- **Rama:** `feature/fase-00-fundacion`

**Descripción:**
Crear el repositorio monorepo con la estructura de carpetas completa definida en la arquitectura. No necesita código real aún, solo los directorios y archivos `.gitkeep` donde corresponda.

**Tareas:**
- [ ] Inicializar repositorio Git local (`git init`)
- [ ] Crear `.gitignore` raíz (Python, Node, .env, __pycache__, .next, etc.)
- [ ] Crear `.editorconfig` con configuración estándar (indent, charset, newline)
- [ ] Crear estructura completa de carpetas `apps/api/`, `apps/worker/`, `apps/web/`, `infra/`, `docs/`, `tests/`
- [ ] Crear estructura interna de módulos en `apps/api/app/modules/` (todos los 27 módulos como carpetas vacías con `__init__.py`)
- [ ] Primer commit: `chore: initialize monorepo structure`
- [ ] Subir a GitHub/GitLab y proteger ramas `main` y `develop`

**Definición de terminado:**
- [ ] `git log` muestra el primer commit
- [ ] Estructura de carpetas visible en el repositorio remoto
- [ ] Ramas `main` y `develop` protegidas (requieren PR)

---

#### #F00-02 — Configurar Docker Compose con todos los servicios
- **Tipo:** `[INFRA]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F00-01

**Descripción:**
Crear el `docker-compose.yml` con todos los servicios necesarios para el entorno de desarrollo local.

**Servicios a incluir:**
- `postgres` — PostgreSQL 16, con volumen persistente, puerto 5432
- `redis` — Redis 7 Alpine, con volumen persistente, puerto 6379
- `minio` — MinIO latest, puertos 9000 (API) y 9001 (console)
- `api` — FastAPI, puerto 8000, con hot-reload
- `worker` — Celery worker
- `worker-beat` — Celery beat (tareas programadas)
- `flower` — Monitor Celery, puerto 5555
- `web` — Next.js, puerto 3000, con hot-reload
- `nginx` — Reverse proxy, puerto 80

**Tareas:**
- [ ] Crear `infra/docker/docker-compose.yml`
- [ ] Crear `infra/docker/docker-compose.override.yml` (desarrollo local)
- [ ] Crear `infra/postgres/init.sql` (crear base de datos y usuario)
- [ ] Crear `infra/redis/redis.conf` (configuración básica)
- [ ] Crear `infra/nginx/nginx.conf` (proxy a api:8000 y web:3000)
- [ ] Crear `infra/storage/` con configuración inicial de MinIO
- [ ] Crear `Makefile` raíz con comandos: `make up`, `make down`, `make logs`, `make shell-api`, `make shell-db`, `make migrate`, `make test`
- [ ] Verificar que todos los servicios arrancan sin errores

**Definición de terminado:**
- [ ] `docker-compose up` sin errores
- [ ] PostgreSQL acepta conexiones en puerto 5432
- [ ] Redis acepta conexiones en puerto 6379
- [ ] MinIO console accesible en `http://localhost:9001`
- [ ] Nginx responde en puerto 80

---

#### #F00-03 — Configurar proyecto backend FastAPI
- **Tipo:** `[BE]` `[INFRA]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F00-01

**Descripción:**
Configurar el proyecto Python con todas las dependencias, estructura base y herramientas de calidad.

**Tareas:**
- [ ] Crear `apps/api/pyproject.toml` con dependencias:
  - `fastapi`, `uvicorn[standard]`
  - `sqlalchemy[asyncio]>=2.0`, `asyncpg`
  - `alembic`
  - `pydantic[email]>=2.0`, `pydantic-settings`
  - `redis`, `celery[redis]`
  - `boto3` (S3/MinIO)
  - `cryptography` (AES para credenciales)
  - `bcrypt`, `passlib`
  - `python-multipart`
  - `httpx` (HTTP client)
- [ ] Dependencias de desarrollo: `pytest`, `pytest-asyncio`, `pytest-cov`, `ruff`, `mypy`, `httpx`
- [ ] Crear `apps/api/Dockerfile` multi-stage (dev y prod)
- [ ] Crear `apps/api/.env.example` con todas las variables documentadas
- [ ] Configurar `ruff` para linting (`pyproject.toml` sección `[tool.ruff]`)
- [ ] Configurar `mypy` para type checking (`pyproject.toml` sección `[tool.mypy]`)
- [ ] Verificar instalación: `pip install -e ".[dev]"` sin errores

**Definición de terminado:**
- [ ] `ruff check apps/api/` sin errores
- [ ] `mypy apps/api/app/` sin errores críticos
- [ ] Dockerfile construye correctamente

---

#### #F00-04 — Configurar proyecto frontend Next.js
- **Tipo:** `[FE]` `[INFRA]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F00-01

**Descripción:**
Inicializar el proyecto Next.js con App Router, TypeScript, Tailwind y todas las dependencias del stack.

**Tareas:**
- [ ] Crear proyecto Next.js 14+ con App Router y TypeScript en `apps/web/`
- [ ] Instalar y configurar Tailwind CSS
- [ ] Instalar shadcn/ui e inicializar (`npx shadcn-ui@latest init`)
- [ ] Instalar: `@tanstack/react-query`, `react-hook-form`, `zod`, `@hookform/resolvers`
- [ ] Instalar: `axios` o `ky` para HTTP client
- [ ] Crear estructura de layouts: `(public)/layout.tsx`, `(auth)/layout.tsx`, `admin/layout.tsx`, `customer/layout.tsx`
- [ ] Crear `apps/web/Dockerfile` multi-stage
- [ ] Configurar `eslint` con reglas estrictas
- [ ] Configurar `tsconfig.json` con paths absolutos (`@/`)
- [ ] Crear `apps/web/.env.example`
- [ ] Instalar componentes shadcn/ui base: `button`, `input`, `form`, `table`, `dialog`, `toast`, `badge`, `card`, `sidebar`

**Definición de terminado:**
- [ ] `npm run dev` arranca sin errores
- [ ] `npm run build` compila sin errores de TypeScript
- [ ] `npx eslint .` sin errores críticos
- [ ] Layouts de navegación independientes creados

---

#### #F00-05 — Configurar Alembic para migraciones
- **Tipo:** `[DB]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F00-03

**Descripción:**
Configurar Alembic con soporte async para PostgreSQL. No crear migraciones todavía, solo la infraestructura.

**Tareas:**
- [ ] Inicializar Alembic: `alembic init apps/api/alembic`
- [ ] Configurar `alembic/env.py` para SQLAlchemy async con asyncpg
- [ ] Configurar `alembic.ini` para leer `DATABASE_URL` de variables de entorno
- [ ] Crear `apps/api/app/database/base.py` — `DeclarativeBase` de SQLAlchemy 2
- [ ] Crear `apps/api/app/database/session.py` — `AsyncSessionLocal`, `get_db` dependency
- [ ] Crear `apps/api/app/database/mixins.py` — mixin con `id (UUID)`, `created_at`, `updated_at`
- [ ] Verificar que `alembic current` funciona contra la BD en Docker

**Definición de terminado:**
- [ ] `alembic current` sin errores
- [ ] `alembic history` muestra historial vacío
- [ ] Session async conecta correctamente a PostgreSQL

---

### BACKEND BASE

---

#### #F00-06 — Implementar configuración central (pydantic-settings)
- **Tipo:** `[BE]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F00-03

**Descripción:**
Centralizar toda la configuración de la aplicación usando `pydantic-settings`. Nunca hardcodear valores.

**Tareas:**
- [ ] Crear `apps/api/app/core/config.py` con clase `Settings(BaseSettings)`:
  - `DATABASE_URL`
  - `REDIS_URL`
  - `SECRET_KEY`, `ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`
  - `S3_ENDPOINT`, `S3_ACCESS_KEY`, `S3_SECRET_KEY`, `S3_BUCKET_NAME`
  - `WHATSAPP_PROVIDER`, `WHATSAPP_TOKEN`, `WHATSAPP_PHONE_ID`
  - `EXCHANGE_RATE_PROVIDER`
  - `ENVIRONMENT` (development / staging / production)
  - `DEBUG`
  - `ALLOWED_ORIGINS` (lista de orígenes CORS)
- [ ] Instancia singleton `settings = Settings()`
- [ ] Validar que todos los campos requeridos existen al arrancar
- [ ] Documentar cada variable en `.env.example`

**Definición de terminado:**
- [ ] La app arranca con errores claros si falta una variable requerida
- [ ] Mypy pasa sin errores en `config.py`

---

#### #F00-07 — Implementar manejo centralizado de excepciones
- **Tipo:** `[BE]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F00-06

**Descripción:**
Definir excepciones de dominio y handlers globales que devuelven el formato estándar de error.

**Tareas:**
- [ ] Crear `apps/api/app/core/exceptions.py`:
  - `HasbunException` (base)
  - `NotFoundError(404)`
  - `ValidationError(422)`
  - `AuthenticationError(401)`
  - `AuthorizationError(403)`
  - `BusinessRuleError(400)` — para reglas de negocio violadas
  - `ConflictError(409)` — para duplicados, concurrencia
  - `InsufficientStockError(400)`
- [ ] Crear exception handlers en `main.py` para cada tipo
- [ ] Formato de respuesta estándar:
  ```json
  {
    "error": {
      "code": "INSUFFICIENT_STOCK",
      "message": "...",
      "details": {},
      "request_id": "..."
    }
  }
  ```
- [ ] Nunca exponer stack traces en producción (`ENVIRONMENT != development`)

**Definición de terminado:**
- [ ] Cada excepción retorna el formato correcto
- [ ] Stack trace solo visible en `ENVIRONMENT=development`
- [ ] Test: lanzar cada excepción y verificar formato y código HTTP

---

#### #F00-08 — Implementar logging estructurado
- **Tipo:** `[BE]`
- **Prioridad:** 🟠 ALTO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F00-06

**Descripción:**
Configurar logging en JSON con campos estándar para facilitar búsqueda y monitoreo.

**Tareas:**
- [ ] Crear `apps/api/app/core/logging.py`
- [ ] Configurar `structlog` o logger estándar con formato JSON
- [ ] Campos obligatorios en cada log: `timestamp`, `level`, `request_id`, `user_id`, `module`, `action`, `duration_ms`
- [ ] Middleware que genera `request_id` (UUID) por cada request y lo inyecta en contexto
- [ ] Configurar que NUNCA se logueen: passwords, tokens, claves de cifrado, datos financieros completos
- [ ] Log de cada request: método, path, status_code, duration_ms, request_id

**Definición de terminado:**
- [ ] Logs en formato JSON
- [ ] `request_id` presente en todos los logs de un mismo request
- [ ] No aparecen contraseñas ni tokens en logs bajo ninguna circunstancia

---

#### #F00-09 — Implementar health checks
- **Tipo:** `[BE]`
- **Prioridad:** 🟠 ALTO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F00-07

**Descripción:**
Endpoints de salud para monitoreo y readiness probes.

**Tareas:**
- [ ] `GET /health` — liveness: la app está viva (responde 200 siempre que el proceso corra)
- [ ] `GET /ready` — readiness: BD, Redis y Storage son accesibles
  - Verifica conexión a PostgreSQL
  - Verifica conexión a Redis
  - Verifica conexión a MinIO/S3
  - Si alguno falla: responde 503 con detalle de cuál falló
- [ ] Respuesta formato:
  ```json
  { "status": "ok", "checks": { "db": "ok", "redis": "ok", "storage": "ok" } }
  ```
- [ ] Estos endpoints NO requieren autenticación

**Definición de terminado:**
- [ ] `GET /health` → 200 siempre
- [ ] `GET /ready` → 200 cuando todos los servicios están up
- [ ] `GET /ready` → 503 cuando PostgreSQL está down

---

#### #F00-10 — Configurar CORS y middlewares de seguridad
- **Tipo:** `[BE]` `[SEC]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F00-06

**Descripción:**
Configurar CORS estricto, headers de seguridad HTTP y rate limiting básico.

**Tareas:**
- [ ] Configurar `CORSMiddleware` con `ALLOWED_ORIGINS` desde settings
- [ ] Agregar headers de seguridad: `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, `Referrer-Policy: strict-origin-when-cross-origin`
- [ ] Implementar `TrustedHostMiddleware` en producción
- [ ] Configurar rate limiting básico con Redis (usando `slowapi` o implementación propia)
  - Default: 100 requests/minuto por IP
  - Endpoints de auth: 10 intentos/minuto por IP
- [ ] Middleware de `request_id` que inyecta UUID en cada request

**Definición de terminado:**
- [ ] CORS bloquea orígenes no permitidos
- [ ] Headers de seguridad presentes en todas las respuestas
- [ ] Rate limiting activo y devuelve 429 al superar el límite

---

#### #F00-11 — Configurar Celery con Redis
- **Tipo:** `[TASK]` `[INFRA]`
- **Prioridad:** 🟠 ALTO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F00-03

**Descripción:**
Configurar Celery para procesamiento asíncrono de tareas (WhatsApp, mora, reportes, backups).

**Tareas:**
- [ ] Crear `apps/worker/celery_app.py` con configuración de Celery + Redis broker
- [ ] Configurar Celery Beat para tareas programadas (cron)
- [ ] Crear estructura `apps/worker/tasks/` con módulos por dominio:
  - `notifications.py`
  - `whatsapp.py`
  - `reports.py`
  - `exchange_rates.py`
  - `backups.py`
- [ ] Crear tarea de prueba: `tasks.health.ping()` que retorna `"pong"`
- [ ] Verificar que Flower muestra la tarea ejecutada en `http://localhost:5555`

**Definición de terminado:**
- [ ] Worker arranca sin errores
- [ ] Tarea `ping` se ejecuta y aparece en Flower
- [ ] Beat schedule configurado (aunque sin tareas reales aún)

---

### CI/CD

---

#### #F00-12 — Configurar GitHub Actions CI — Backend
- **Tipo:** `[INFRA]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F00-03

**Descripción:**
Pipeline de CI para el backend que bloquea el merge si falla.

**Tareas:**
- [ ] Crear `.github/workflows/ci-backend.yml`
- [ ] Pasos del pipeline:
  1. Checkout
  2. Setup Python 3.12
  3. Install dependencies
  4. `ruff check apps/api/` — lint
  5. `mypy apps/api/app/` — type check
  6. Levantar PostgreSQL y Redis como services en el job
  7. Ejecutar migraciones
  8. `pytest apps/api/tests/ --cov` — tests con cobertura
- [ ] Configurar que el pipeline corre en: push a `feature/*`, PR a `develop`, PR a `main`
- [ ] Configurar branch protection: CI debe pasar antes de merge

**Definición de terminado:**
- [ ] Pipeline verde en un PR de prueba
- [ ] Pipeline rojo si se introduce un error de sintaxis

---

#### #F00-13 — Configurar GitHub Actions CI — Frontend
- **Tipo:** `[INFRA]`
- **Prioridad:** 🟠 ALTO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F00-04

**Descripción:**
Pipeline de CI para el frontend.

**Tareas:**
- [ ] Crear `.github/workflows/ci-frontend.yml`
- [ ] Pasos del pipeline:
  1. Checkout
  2. Setup Node.js 20
  3. `npm ci`
  4. `npm run lint` — eslint
  5. `npx tsc --noEmit` — type check
  6. `npm run build` — build de producción
- [ ] Corre en los mismos eventos que el CI backend

**Definición de terminado:**
- [ ] Pipeline verde en un PR de prueba
- [ ] Pipeline rojo si hay error de TypeScript

---

### DOCUMENTACIÓN

---

#### #F00-14 — Crear README.md principal
- **Tipo:** `[DOCS]`
- **Prioridad:** 🟡 MEDIO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F00-02

**Descripción:**
Documentación de arranque para cualquier desarrollador nuevo.

**Tareas:**
- [ ] Crear `README.md` raíz con:
  - Descripción del proyecto
  - Prerrequisitos (Docker, Node.js, Python)
  - Instrucciones de arranque local (`make up` o `docker-compose up`)
  - Variables de entorno requeridas (referencia a `.env.example`)
  - Comandos útiles (make targets)
  - Estructura del proyecto
  - Referencia a documentación técnica en `docs/`
  - Convenciones de commits y ramas

**Definición de terminado:**
- [ ] Un desarrollador nuevo puede levantar el proyecto siguiendo solo el README

---

#### #F00-15 — Crear docs/architecture.md
- **Tipo:** `[DOCS]`
- **Prioridad:** 🟡 MEDIO
- **Estado:** ⬜ Pendiente

**Tareas:**
- [ ] Documentar la arquitectura de capas (DOMAIN / APPLICATION / INFRASTRUCTURE / API)
- [ ] Documentar la estructura interna de cada módulo
- [ ] Documentar el flujo de un request de extremo a extremo
- [ ] Documentar las decisiones de arquitectura importantes (ADRs básicos)

---

### SEEDS Y PRUEBA INICIAL

---

#### #F00-16 — Crear script de datos sintéticos (seed básico)
- **Tipo:** `[BE]` `[DB]`
- **Prioridad:** 🟡 MEDIO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F00-05

**Descripción:**
Script para poblar la base de datos con datos ficticios de desarrollo. **Nunca usar datos reales.**

**Tareas:**
- [ ] Crear `apps/api/app/database/seeds/` con seeders por módulo
- [ ] Seed de roles: OWNER, SALES, TECHNICIAN, SOFTWARE_DEVELOPER, CUSTOMER
- [ ] Seed de usuarios ficticios (uno por rol) con contraseñas de desarrollo
- [ ] Comando: `make seed` o `python -m app.database.seeds`
- [ ] El seed es idempotente (puede ejecutarse múltiples veces sin duplicar)

**Definición de terminado:**
- [ ] `make seed` crea los 5 usuarios base sin error
- [ ] El seed puede ejecutarse dos veces sin errores ni duplicados

---

#### #F00-17 — Verificación final de FASE 00
- **Tipo:** `[INFRA]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** Todos los anteriores

**Checklist de salida de fase:**
- [ ] `docker-compose up` levanta todos los servicios sin errores
- [ ] `GET http://localhost:8000/health` → `{"status": "ok"}`
- [ ] `GET http://localhost:8000/ready` → `{"status": "ok", "checks": {...}}`
- [ ] `GET http://localhost:3000` → Next.js carga correctamente
- [ ] `ruff check apps/api/` → sin errores
- [ ] `mypy apps/api/app/` → sin errores críticos
- [ ] `npx tsc --noEmit` en `apps/web/` → sin errores
- [ ] CI verde en GitHub Actions
- [ ] `alembic current` → sin errores
- [ ] Flower accesible en `http://localhost:5555`
- [ ] MinIO console accesible en `http://localhost:9001`
- [ ] PR mergeado a `develop`

---

#### #F00-18 — Crear conftest.py y base de tests
- **Tipo:** `[TEST]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F00-05

**Descripción:**
Infraestructura base para tests. Todos los tests futuros dependen de esto.

**Tareas:**
- [ ] Crear `apps/api/tests/conftest.py` con:
  - Fixture `db` — sesión de BD de tests (con rollback automático por test)
  - Fixture `client` — `httpx.AsyncClient` apuntando a la app de tests
  - Fixture `db_setup` — crea y destruye esquema para cada sesión de tests
- [ ] Configurar base de datos de tests separada (`DATABASE_URL_TEST`)
- [ ] Configurar `pytest.ini` o sección en `pyproject.toml`
- [ ] Test de prueba: `test_health.py` que verifica `GET /health` → 200
- [ ] Verificar que `pytest` corre y el test de salud pasa

**Definición de terminado:**
- [ ] `pytest apps/api/tests/` → 1 test pasa (health check)
- [ ] Cada test tiene su propia transacción que se revierte al terminar

---

## Resumen de dependencias FASE 00

```
#F00-01 (repo)
    ├── #F00-02 (docker)
    │       └── #F00-14 (README)
    ├── #F00-03 (backend)
    │       ├── #F00-05 (alembic)
    │       │       ├── #F00-16 (seeds)
    │       │       └── #F00-18 (conftest)
    │       ├── #F00-06 (config)
    │       │       ├── #F00-07 (exceptions)
    │       │       │       └── #F00-09 (health)
    │       │       │               └── #F00-17 (verificación final)
    │       │       ├── #F00-08 (logging)
    │       │       └── #F00-10 (cors/security)
    │       ├── #F00-11 (celery)
    │       └── #F00-12 (CI backend)
    ├── #F00-04 (frontend)
    │       └── #F00-13 (CI frontend)
    └── #F00-15 (architecture.md)
```

---

*Referencia: [REQUIREMENTS.md](../REQUIREMENTS.md) §4 Arquitectura, §37 Despliegue*
*Siguiente fase: [FASE 01 — Auth](FASE-01-auth.md)*
