# Base de Datos — Documentación

Modelos del sistema Hasbun. Convenciones: `id` UUID PK en todas las tablas, `created_at`/`updated_at` TIMESTAMPTZ en los modelos con `BaseModel`. Naming convention de constraints: `ck_<tabla>_<nombre>`, `fk_<tabla>_<columna>`.

## FASE 02 — Catálogo de Productos

### Atributos dinámicos

En lugar de una columna por atributo (RAM, SSD, CPU, Color, ...), se usa un sistema de tres tablas:

| Tabla | Propósito |
|---|---|
| `attributes` | Define el atributo: `name` (único), `data_type` (`text`/`number`/`boolean`/`list`), `unit` opcional. |
| `attribute_values` | Valores permitidos de un atributo. `UNIQUE(attribute_id, value)`. |
| `product_attribute_values` | Tabla asociativa `product_id` + `attribute_value_id` (PK compuesta). |

**Ejemplo:** `Color` (list) → valores `Negro`, `Blanco`, `Plateado`, `Azul`, `Rojo`. Un producto se vincula a un `AttributeValue` concreto (no escribe texto libre), garantizando consistencia en el catálogo.

Endpoints:
- `GET /api/v1/attributes` — lista atributos (con valores).
- `POST /api/v1/attributes` — crear atributo (solo `productos.editar`).
- `GET /api/v1/attributes/{id}/values` — valores de un atributo.
- `POST /api/v1/attributes/{id}/values` — agregar valor.

### Productos

`products`:

| Columna | Notas |
|---|---|
| `sku` | Único, generado automáticamente (ver SKU). Nunca se modifica tras la creación. |
| `barcode` | Único, opcional. |
| `slug` | Único, derivado del nombre. |
| `cost_price`, `sale_price` | `NUMERIC(14,2)`. Constraints `>= 0`. |
| `currency` | `PEN` o `USD`. |
| `price_rule` | Enum de regla de precio (ver `business-rules.md`). |
| `active` / `published` | `active` = disponible en el sistema; `published` = visible en tienda pública. La tienda solo muestra `active AND published`. |
| `is_serialized` | Si `true`, el producto exige unidades serializadas. |
| `stock_minimum` | Umbral para badge de stock bajo. |

`sku_sequences`: tabla auxiliar `(prefix PK, last_value BIGINT)`. El generador hace `SELECT ... FOR UPDATE`, incrementa y formatea `{prefix}-{value:05d}` (ej. `LAP-00001`). Ver `docs/business-rules.md`.

`serialized_units`: unidad física con `serial_number` único, `imei` único, `imei2`, `mac_address`, estado enum `AVAILABLE/RESERVED/PARTIALLY_PAID/DELIVERED_ON_CREDIT/SOLD/IN_REPAIR/RETURNED/DAMAGED`. `purchase_item_id` es UUID nullable **sin FK** (la tabla `purchases` llega en FASE 03).

`product_offers`: `normal_price`, `offer_price` con constraints `offer_price < normal_price`, `offer_price > 0`, `end_at > start_at`.

`product_images`: `product_id` + `file_id` (→ `file_objects`), `display_order`, `is_primary`.

### Archivos

`file_objects`:

| Columna | Notas |
|---|---|
| `storage_key` | Ruta en S3/MinIO: `uploads/<uuid>`. |
| `bucket` | Bucket de almacenamiento. |
| `original_name` | Nombre original del archivo. |
| `mime_type` | MIME real detectado por magic bytes. |
| `size` | Bytes. |
| `checksum` | SHA-256 hex del contenido. |
| `is_deleted` | Soft delete. |
| `uploaded_by` | FK a `users`. |

Reglas: solo imágenes `image/jpeg`, `image/png`, `image/webp`, `image/gif`; máximo 10 MB; el MIME se valida del **contenido real**, no de la extensión ni del header `Content-Type` declarado.