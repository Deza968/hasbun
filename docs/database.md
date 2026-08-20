# Base de Datos — Itinerario de tablas

Este documento describe las tablas y convenciones de la base de datos del sistema Inversiones Hasbun.

Convenciones generales:
- Todas las tablas tienen PK `id UUID` por defecto (salvo tablas auxiliares).
- `created_at` y `updated_at` son `TIMESTAMPTZ`.
- Todo el dinero se maneja como `NUMERIC` y en el código como `Decimal` (nunca `float`).
- Migraciones con Alembic: `apps/api/alembic/versions/`.

---

## FASE 02 — Catálogo de Productos

### Sistema de atributos dinámicos

En lugar de una columna por característica (RAM, SSD, CPU, color, etc.), el catálogo usa tres tablas:

| Tabla | Columnas | Notas |
|---|---|---|
| `attributes` | `id` (UUID PK), `name` (VARCHAR unique), `data_type` (VARCHAR), `unit` (VARCHAR nullable) | `name` ej.: RAM, SSD, CPU, Color. `data_type`: STRING / INTEGER / DECIMAL / BOOLEAN. `unit` ej.: GB, GHz, pulgadas. |
| `attribute_values` | `id` (UUID PK), `attribute_id` (FK → attributes), `value` (VARCHAR) | `UNIQUE (attribute_id, value)`. Ej.: "8GB", "512GB", "Negro". |
| `product_attribute_values` | `product_id` (FK → products), `attribute_value_id` (FK → attribute_values) | PK compuesto `(product_id, attribute_value_id)`. |

Ventajas:
- Se agregan atributos nuevos sin tocar el esquema (`ALTER TABLE`).
- Un producto puede tener N atributos, y un atributo se reutiliza en N productos.

Modelos: `apps/api/app/modules/attributes/domain/models.py`.

---

### Marcas y categorías

- `brands`: `name` y `slug` únicos; `logo_file_id` (FK → `file_objects`, nullable); `active` boolean.
- `categories`: jerárquicas con `parent_id` (FK → categories, nullable); `slug` único; `active` boolean.

El listado público devuelve el árbol jerárquico (`parent` → `children`).

---

### Productos

- `products`: `sku` único, `barcode` único nullable, `slug` único, `brand_id` FK → brands, `category_id` FK → categories, precios `NUMERIC(14,2)`, `currency` (PEN/USD), `price_rule`, `active`, `published`, `stock_minimum`, `is_serialized`, `weight_kg`.
- Check constraints: `cost_price >= 0`, `sale_price >= 0`.
- SKU nunca se modifica tras la creación.

Tablas relacionadas:
- `product_images` — ordenada por `display_order`; la primera imagen creada es `is_primary`, y hay endpoint para cambiar la principal.
- `product_offers` — ofertas por tiempo; se aplica automáticamente la vigente (ver reglas de precio).
- `serialized_units` — unidades vendibles individualmente (seriales/IMEI); `serial_number` único global (nunca vender el mismo serial dos veces). Estados: AVAILABLE, RESERVED, PARTIALLY_PAID, DELIVERED_ON_CREDIT, SOLD, IN_REPAIR, RETURNED, DAMAGED.
- `sku_sequences` — tabla auxiliar del generador de SKU (prefijo → contador). Ver `docs/business-rules.md`.

---

### Tipo de cambio

- `exchange_rates`: `currency_from`/`currency_to` (VARCHAR(3)), `rate` `NUMERIC(10,4)`, `source` (mock / sunat / bcp), `effective_at` `TIMESTAMPTZ`.
- Índice `(currency_from, currency_to, effective_at DESC)`.
- La tasa del día se persiste la primera vez que se consulta y se actualiza por tarea Celery diaria (idempotente).

---

### Archivos

- `file_objects`: `storage_key` (ruta en el bucket p. ej. `products/<id>.jpg`), `bucket`, `original_name`, `mime_type`, `size` (BIGINT), `checksum` (SHA-256), `metadata` (JSONB), `uploaded_by` (FK → users).
- El MIME se valida por contenido real (magic bytes), no por la extensión. Tipos permitidos: `image/jpeg`, `image/png`, `image/webp`, `application/pdf`. Tamaño máximo configurable (por defecto 10 MB).

---
*Referencia: [architecture.md](architecture.md), [REQUIREMENTS.md](REQUIREMENTS.md)*