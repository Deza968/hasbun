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

## FASE 03 — Inventario y Compras

### `inventory_movements` (#F03-01)

`product_id FK→products`, `serialized_unit_id` UUID, `quantity NUMERIC(14,3)` firmado, `movement_type VARCHAR(30)`, `reference_type/id`, `warehouse default principal`, `unit_cost NUMERIC(14,2)`, `authorization_id UUID` (obligatorio si `ADJUSTMENT_*`), `created_by FK→users`. Índices: `(product_id, created_at DESC)`, `(reference_type, reference_id)`, `(movement_type, created_at)`. Check: `ADJUSTMENT_* = (authorization_id IS NOT NULL)`. Inmutable (sin UPDATE/DELETE).

### `v_product_stock` / `v_product_stock_summary` (#F03-02)

Vista que agrega por `products.id`: `physical`, `reserved`, `partially_paid`, `on_credit`, `available`. Usada por `GET /inventory/stock` paginado. `GET /inventory/kardex/{id}` calcula `running_balance` en Python y `GET .../export` deja CSV.

### `suppliers` (#F03-07)

`razon_social`, `ruc UNIQUE`, `nombre_comercial`, `contacto_nombre`, `telefono`, `telefono_whatsapp`, `email`, `direccion`, `ciudad`, `active`, `notes`, `created_by FK→users`. Índice `razon_social`.

### `purchases` / `purchase_items` / `purchase_sequences` (#F03-08/#F03-09)

`purchases`: `code UNIQUE` (`OC-YYYY-XXXXX` vía `purchase_sequences(year,last_value)` transaccional `FOR UPDATE`), `supplier_id FK→suppliers RESTRICT`, `status DRAFT/ORDERED/RECEIVED/PARTIAL/CANCELLED`, `total NUMERIC(14,2)`, `currency`, `exchange_rate NUMERIC(10,4)`, `invoice_file_id FK→file_objects`, `received_at`. `purchase_items`: `quantity NUMERIC(14,3) CHECK>0`, `unit_cost/subtotal NUMERIC(14,2)`. Recepción atómica genera `InventoryMovement(PURCHASE)` y si `product.is_serialized` crea `serialized_units`.

### Seeds (#F03-11/#F03-18)

`apps/api/app/database/seeds/inventory.py`: 5 proveedores + 21 compras `RECEIVED` que llaman a `next_purchase_code()` y generan `InventoryMovement` + `SerializedUnit(AVAILABLE)` para productos serializados.

### Tareas Celery (#F03-15/#F03-19)

`worker.tasks.inventory.check_low_stock` (Beat 9:00 y 15:00 `America/Lima`, idempotente por `product_id:fecha`) y `generate_daily_stock_report` (Beat 8:00, stub completo en FASE 12).

---
*Referencia: [architecture.md](architecture.md), [REQUIREMENTS.md](REQUIREMENTS.md)*