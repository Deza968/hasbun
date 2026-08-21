# Inversiones Hasbun

Sistema ERP + POS + E-Commerce para **Inversiones Hasbun**, tienda de tecnología, electrodomésticos y servicios en Sicuani, Cusco, Perú.

## Arquitectura

Monorepo con 3 aplicaciones y servicios de soporte:

| App | Tecnología | Ruta |
|---|---|---|
| API | FastAPI + SQLAlchemy 2 (async) + PostgreSQL | `apps/api/` |
| Worker | Celery + Redis | `apps/worker/` |
| Web | Next.js 14 + TypeScript + Tailwind + shadcn/ui | `apps/web/` |
| Infra | Docker Compose, nginx, MinIO/S3 | `infra/` |

Servicios de soporte: PostgreSQL 16, Redis 7, MinIO (S3 compatible).

## Requisitos previos

- Docker + Docker Compose
- Node 20+ (solo para desarrollo local del frontend)
- Python 3.12+ (solo para desarrollo local del backend)

## Puesta en marcha

```bash
cp apps/api/.env.example apps/api/.env      # ajustar credenciales
cp apps/web/.env.example apps/web/.env.local
make up                                      # levanta toda la infra
make migrate                                 # ejecuta migraciones Alembic
make seed                                    # roles + usuarios de desarrollo
```

Servicios:
- API: http://localhost:8000 (docs en `/docs`)
- Web: http://localhost:3000
- nginx: http://localhost
- Flower (Celery): http://localhost:5555
- MinIO console: http://localhost:9001 (`minioadmin` / `minioadmin`)

## Desarrollo local (sin Docker)

```bash
make api-install      # pip install -e ".[dev]"  en apps/api
make web-install      # npm install               en apps/web
make test-api         # pytest
make lint             # ruff + mypy
```

## Estado del proyecto

Proyecto en construcción por fases (ver `docs/TASKS.md`):

- **FASE 00 — Fundación y Arquitectura**: ✅ completada
- **FASE 01 — Autenticación y RBAC**: ✅ completada
- **FASE 02 — Catálogo de Productos**: ✅ completada (backend verificado: 51/51 tests, ruff, mypy)
- ... hasta FASE 13 — Producción / Hardening

## Credenciales de desarrollo (seeds)

| Rol | Email | Contraseña |
|---|---|---|
| OWNER | owner@hasbun.dev | Owner2026! |
| SALES | ventas@hasbun.dev | Ventas2026! |
| TECHNICIAN | tecnico@hasbun.dev | Tecnico2026! |
| SOFTWARE_DEVELOPER | software@hasbun.dev | Software2026! |
| CUSTOMER | cliente@hasbun.dev | Cliente2026! |

> Solo para entornos de desarrollo/CI. Nunca usar en producción.

## Documentación

- `docs/REQUIREMENTS.md` — especificación funcional completa
- `docs/TASKS.md` — índice de fases
- `docs/architecture.md` — decisiones de arquitectura
- `docs/database.md` — esquema de base de datos (catálogo, atributos, archivos)
- `docs/business-rules.md` — reglas de precios, ofertas y generador de SKU