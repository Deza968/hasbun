# Arquitectura — Inversiones Hasbun

## Visión general

Sistema monolítico modular (modular monolith) con 3 aplicaciones desplegables:

```
                    ┌─────────────┐
   Browser ───────▶ │    nginx    │
                    └──────┬──────┘
              ┌────────────┴────────────┐
              ▼                         ▼
       ┌───────────┐             ┌───────────┐
       │    Web    │             │    API    │
       │ Next.js 14│             │  FastAPI  │
       └───────────┘             └─────┬─────┘
                                       │
        ┌──────────┬───────────────────┼───────────────┐
        ▼          ▼                   ▼               ▼
  ┌─────────┐ ┌─────────┐      ┌────────────┐   ┌────────────┐
  │PostgreSQL│ │ Redis   │      │   Celery   │   │   MinIO    │
  │   16     │ │   7     │      │ worker/beat│   │ (S3 files) │
  └─────────┘ └─────────┘      └────────────┘   └────────────┘
```

## Decisiones clave

### Dinero
- Todo importe monetario es `NUMERIC(14,2)` en PostgreSQL. **Nunca** `float` (errores de redondeo).
- Cálculos de moneda vía decimales (Python `Decimal`) usando el módulo `ExchangeRate`.

### Inventario
- El **stock no es un campo editable**: es la suma derivada de la tabla `inventory_movements`.
- Cada entrada/salida genera un movimiento con referencia a la orden que lo originó (compra, venta, reparación, etc.).

### Identificadores
- Todos los `id` son **UUID v4** (mixin `UUIDPrimaryKeyMixin`).
- Las claves naturales (correlativos, RUC) llevan índices únicos propios.

### Autenticación y permisos
- **RBAC**: roles `OWNER`, `SALES`, `TECHNICIAN`, `SOFTWARE_DEVELOPER`, `CUSTOMER`.
- El rol `OWNER` puede conceder/revocar permisos individuales (overrides) sin cambiar el rol.
- JWT (access + refresh) con rotación; rate limiting por IP con Redis.

### Auditoría
- Toda mutación sensible se registra en `audit_logs` (quién, qué, cuándo, desde dónde).
- Los `updated_at` se mantienen vía `TimestampMixin`.

## Estructura del backend (modular)

```
apps/api/app/
├── core/          # config, excepciones, logging, seguridad
├── database/      # base declarativa, sesión, alembic, seeds
├── modules/       # 33 módulos de negocio
│   └── <modulo>/
│       ├── domain/         # modelos y reglas de negocio
│       ├── application/    # servicios/casos de uso
│       ├── infrastructure/ # repos y adaptadores
│       └── api/            # routers FastAPI
└── main.py
```

Cada módulo es autocontenido; las dependencias entre módulos se resuelven por servicios, no por acceso directo a tablas.

## Frontend

- Next.js 14 App Router, TypeScript estricto, Tailwind + shadcn/ui.
- Layouts segmentados por rol: `(public)`, `(auth)`, `admin/`, `customer/`.
- Estado con React Query (server state) + React Hook Form / Zod (formularios).

## Infraestructura

- **Docker Compose** orquesta postgres, redis, minio, api, worker, beat, flower, web, nginx (`infra/docker/`).
- **CI**: GitHub Actions — backend (ruff, mypy, pytest con Postgres) y frontend (typecheck, lint, build).
- **Migraciones**: Alembic async; `make migrate` / `make makemigration`.
- **Seeds**: `make seed` (idempotente) crea roles y usuarios de desarrollo.

## Flujo de trabajo por fase

1. Implementar issues de la fase según `docs/tasks/FASE-XX-*.md`.
2. Cada issue: código + tests + migración (si aplica) + actualizar el checklist.
3. CI en verde antes de avanzar a la siguiente fase.
4. Completar la "Definición de terminado" de la fase.