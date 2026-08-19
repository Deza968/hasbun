# FASE 02 — Catálogo de Productos

**Rama:** `feature/fase-02-catalogo`
**Objetivo:** Gestión completa de productos, categorías, marcas, atributos dinámicos, tipo de cambio y almacenamiento de archivos.
**Prerrequisito:** FASE 01 completada y mergeada a `develop`.
**Criterio de salida:** CRUD de productos funciona con SKU automático, atributos dinámicos, ofertas y upload de imágenes. Tipo de cambio disponible. Permisos correctos por rol.

---

## Progreso

| Completados | Total | Porcentaje |
|---|---|---|
| 0 | 24 | 0% |

---

## Issues

### TIPO DE CAMBIO

---

#### #F02-01 — Módulo ExchangeRate: modelos y migración
- **Tipo:** `[BE]` `[DB]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** FASE-01 completa

**Descripción:**
El tipo de cambio debe estar disponible antes que los productos porque los precios dependen de él.

**Tareas:**
- [ ] Crear `apps/api/app/modules/exchange_rates/domain/models.py`:
  ```
  ExchangeRate:
    id (UUID, PK)
    currency_from (VARCHAR(3))   — USD
    currency_to (VARCHAR(3))     — PEN
    rate (NUMERIC(10,4))
    source (VARCHAR(50))         — mock / manual / sunat / bcp
    effective_at (TIMESTAMPTZ)
    created_at (TIMESTAMPTZ)
    INDEX: (currency_from, currency_to, effective_at DESC)
  ```
- [ ] Migración Alembic para `exchange_rates`
- [ ] Crear interfaz `ExchangeRateProvider` (ABC):
  - `get_current_rate(from_currency, to_currency) -> Decimal`
- [ ] Implementar `MockExchangeRateProvider`:
  - USD→PEN = 3.75 (configurable en settings)
  - No hace llamadas externas
- [ ] Preparar `ExternalExchangeRateProvider` (stub vacío documentado, no implementar)
- [ ] Servicio `ExchangeRateService`:
  - `get_current_rate(from_currency, to_currency) -> ExchangeRate`
  - `get_rate_at(from_currency, to_currency, timestamp) -> ExchangeRate`
  - `update_rates()` — llamado por tarea Celery diaria

**Definición de terminado:**
- [ ] `GET /api/v1/exchange-rates/current?from=USD&to=PEN` retorna tipo de cambio vigente
- [ ] La tasa se guarda en BD al consultarse por primera vez en el día
- [ ] Test unitario de cálculo de conversión con `Decimal` (no `float`)

---

#### #F02-02 — Tarea Celery: actualización diaria de tipo de cambio
- **Tipo:** `[TASK]`
- **Prioridad:** 🟡 MEDIO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F02-01

**Tareas:**
- [ ] Crear `apps/worker/tasks/exchange_rates.py`:
  - Tarea `update_exchange_rates()` — ejecuta `ExchangeRateService.update_rates()`
- [ ] Configurar en Celery Beat: ejecutar diariamente a la hora configurada en settings
- [ ] La tarea es idempotente: si ya existe tasa del día, no crea duplicado
- [ ] Loguear resultado de actualización

---

### MARCAS Y CATEGORÍAS

---

#### #F02-03 — Modelos Brand y Category con migración
- **Tipo:** `[BE]` `[DB]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** FASE-01 completa

**Tareas:**
- [ ] Crear modelos:
  ```
  Brand:
    id (UUID, PK)
    name (VARCHAR, unique)
    slug (VARCHAR, unique)
    logo_file_id (UUID, FK → FileObject, nullable)
    active (BOOLEAN, default True)
    created_at, updated_at (TIMESTAMPTZ)

  Category:
    id (UUID, PK)
    name (VARCHAR)
    slug (VARCHAR, unique)
    parent_id (UUID, FK → Category, nullable)  — categorías anidadas
    description (TEXT)
    active (BOOLEAN, default True)
    created_at, updated_at (TIMESTAMPTZ)
  ```
- [ ] Migración Alembic para ambas tablas
- [ ] CRUD completo con repositorios y servicios
- [ ] Endpoints:
  - `GET /api/v1/brands` — público (para tienda)
  - `POST /api/v1/brands` — solo OWNER
  - `PUT /api/v1/brands/{id}` — solo OWNER
  - `DELETE /api/v1/brands/{id}` — solo OWNER (soft delete si tiene productos)
  - `GET /api/v1/categories` — público, árbol jerárquico
  - `POST /api/v1/categories` — solo OWNER
  - `PUT /api/v1/categories/{id}` — solo OWNER
  - `DELETE /api/v1/categories/{id}` — solo OWNER (verifica si tiene productos activos)

**Definición de terminado:**
- [ ] CRUD funciona con permisos correctos
- [ ] Categorías devuelven árbol jerárquico (parent → children)
- [ ] No se puede eliminar una categoría con productos activos (devuelve 409)

---

### ATRIBUTOS DINÁMICOS

---

#### #F02-04 — Sistema de atributos dinámicos
- **Tipo:** `[BE]` `[DB]`
- **Prioridad:** 🟠 ALTO
- **Estado:** ⬜ Pendiente
- **Depende de:** FASE-01 completa

**Descripción:**
En lugar de columnas por atributo (RAM, SSD, CPU, etc.), se usa un sistema dinámico de tres tablas.

**Tareas:**
- [ ] Crear modelos:
  ```
  Attribute:
    id (UUID, PK)
    name (VARCHAR, unique)    — RAM, SSD, CPU, Color, etc.
    data_type (ENUM)          — text / number / boolean / list
    unit (VARCHAR)            — GB, GHz, pulgadas, etc. (opcional)
    created_at (TIMESTAMPTZ)

  AttributeValue:
    id (UUID, PK)
    attribute_id (UUID, FK → Attribute)
    value (VARCHAR)           — "8GB", "512GB", "Intel i5", "Negro", etc.
    UNIQUE: (attribute_id, value)

  ProductAttributeValue:
    product_id (UUID, FK → Product)
    attribute_value_id (UUID, FK → AttributeValue)
    PK: (product_id, attribute_value_id)
  ```
- [ ] Migración Alembic
- [ ] Endpoints:
  - `GET /api/v1/attributes` — lista atributos (filtrar por categoría opcional)
  - `POST /api/v1/attributes` — crear atributo (solo OWNER)
  - `GET /api/v1/attributes/{id}/values` — valores de un atributo
  - `POST /api/v1/attributes/{id}/values` — agregar valor (solo OWNER)
- [ ] Seed de atributos comunes: RAM, SSD, CPU, Pantalla, Color, Capacidad, Resolución, Modelo, Voltaje, Tipo de cámara, Megapíxeles

**Definición de terminado:**
- [ ] Se pueden crear atributos y valores
- [ ] Un producto puede tener múltiples atributos con sus valores

---

### PRODUCTOS

---

#### #F02-05 — Modelo Product con migración
- **Tipo:** `[BE]` `[DB]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F02-03, #F02-04

**Tareas:**
- [ ] Crear `apps/api/app/modules/products/domain/models.py`:
  ```
  Product:
    id (UUID, PK)
    sku (VARCHAR, unique, not null)
    barcode (VARCHAR, unique, nullable)
    name (VARCHAR, not null)
    slug (VARCHAR, unique, not null)
    description (TEXT)
    short_description (TEXT)
    brand_id (UUID, FK → Brand)
    category_id (UUID, FK → Category)
    cost_price (NUMERIC(14,2), not null)
    sale_price (NUMERIC(14,2), not null)
    currency (VARCHAR(3), not null)    — PEN o USD
    price_rule (ENUM)                  — FIXED_PEN/FIXED_USD/USD_CONVERTED/COST_USD_MARGIN/MANUAL
    active (BOOLEAN, default True)
    published (BOOLEAN, default False)
    stock_minimum (INTEGER, default 0)
    is_serialized (BOOLEAN, default False)
    weight_kg (NUMERIC(8,3))
    notes (TEXT)
    created_at, updated_at (TIMESTAMPTZ)
  ```
- [ ] Migración Alembic
- [ ] Constraint: `cost_price >= 0`, `sale_price >= 0`

---

#### #F02-06 — Generador de SKU transaccional
- **Tipo:** `[BE]` `[DB]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F02-05

**Descripción:**
El SKU se genera automáticamente. El generador debe ser transaccional para evitar duplicados bajo concurrencia.

**Tareas:**
- [ ] Crear tabla auxiliar `sku_sequences`:
  ```
  sku_sequences:
    prefix (VARCHAR, PK)    — LAP, IMP, CAM, ACC, ELE, etc.
    last_value (INTEGER)
  ```
- [ ] Migración para `sku_sequences`
- [ ] Función `generate_sku(prefix, session) -> str`:
  - `SELECT last_value FROM sku_sequences WHERE prefix = :prefix FOR UPDATE`
  - Incrementar en 1
  - Formatear: `{prefix}-{value:05d}` → `LAP-00001`
  - Todo dentro de la misma transacción que crea el producto
- [ ] Seed de prefijos: LAP, IMP, CAM, ACC, ELE, SRV, SBL, MON, CEL, TAB, RED, ALM
- [ ] Mapa de categoría → prefijo configurable

**Definición de terminado:**
- [ ] Crear 100 productos simultáneamente → 100 SKUs únicos (test de concurrencia)
- [ ] SKU nunca se modifica después de creado

---

#### #F02-07 — Unidades serializadas (SerializedUnit)
- **Tipo:** `[BE]` `[DB]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F02-05

**Tareas:**
- [ ] Crear modelo `SerializedUnit`:
  ```
  SerializedUnit:
    id (UUID, PK)
    product_id (UUID, FK → Product)
    serial_number (VARCHAR, unique, not null)
    imei (VARCHAR, unique, nullable)
    imei2 (VARCHAR, nullable)
    mac_address (VARCHAR, nullable)
    status (ENUM): AVAILABLE/RESERVED/PARTIALLY_PAID/
                   DELIVERED_ON_CREDIT/SOLD/IN_REPAIR/RETURNED/DAMAGED
    purchase_item_id (UUID, FK → PurchaseItem, nullable)
    notes (TEXT)
    created_at, updated_at (TIMESTAMPTZ)
  ```
- [ ] Migración Alembic
- [ ] Constraint único en `serial_number` (nunca vender el mismo serial dos veces)
- [ ] Endpoints:
  - `GET /api/v1/products/{id}/serials` — lista seriales del producto (solo admin)
  - `POST /api/v1/products/{id}/serials` — registrar serial (solo OWNER)
  - `GET /api/v1/products/{id}/serials/{serial_id}` — detalle
  - `PUT /api/v1/products/{id}/serials/{serial_id}` — actualizar estado (con auditoría)

**Definición de terminado:**
- [ ] No se puede crear dos seriales con el mismo `serial_number`
- [ ] Cambio de estado queda en AuditLog

---

#### #F02-08 — Ofertas de productos (ProductOffer)
- **Tipo:** `[BE]` `[DB]`
- **Prioridad:** 🟠 ALTO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F02-05

**Tareas:**
- [ ] Crear modelo `ProductOffer`:
  ```
  ProductOffer:
    id (UUID, PK)
    product_id (UUID, FK → Product)
    normal_price (NUMERIC(14,2))
    offer_price (NUMERIC(14,2))
    start_at (TIMESTAMPTZ)
    end_at (TIMESTAMPTZ)
    active (BOOLEAN, default True)
    created_by (UUID, FK → User)
    created_at (TIMESTAMPTZ)
  ```
- [ ] Constraint: `offer_price < normal_price` y `offer_price > 0`
- [ ] Migración
- [ ] Lógica en `ProductService.get_current_price(product_id)`:
  - Si existe `ProductOffer` activa con `start_at <= NOW() <= end_at` → retornar `offer_price`
  - Si no → retornar `sale_price`
- [ ] Endpoints:
  - `POST /api/v1/products/{id}/offers` — crear oferta (solo OWNER)
  - `GET /api/v1/products/{id}/offers` — listar ofertas
  - `DELETE /api/v1/products/{id}/offers/{offer_id}` — desactivar

---

#### #F02-09 — CRUD completo de productos
- **Tipo:** `[BE]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F02-05, #F02-06, #F02-07, #F02-08

**Tareas:**
- [ ] Repositorio con queries para: lista paginada, búsqueda por nombre/SKU/barcode, detalle
- [ ] Servicio `ProductService`:
  - `create_product(data, created_by)` — genera SKU, crea producto y atributos
  - `update_product(id, data, updated_by)` — auditaría si cambia precio o costo
  - `deactivate_product(id, deactivated_by)` — no elimina, solo `active=False`
  - `publish_product(id, user)` — cambia `published=True`
  - `get_current_price(id)` — considera ofertas vigentes y tipo de cambio
- [ ] Endpoints:
  - `GET /api/v1/products` — lista con filtros y paginación (público para tienda)
  - `POST /api/v1/products` — crear (solo OWNER)
  - `GET /api/v1/products/{id}` — detalle (público si published)
  - `GET /api/v1/products/sku/{sku}` — buscar por SKU (admin)
  - `PUT /api/v1/products/{id}` — actualizar (solo OWNER)
  - `POST /api/v1/products/{id}/publish` — publicar (solo OWNER)
  - `POST /api/v1/products/{id}/unpublish` — despublicar (solo OWNER)
  - `DELETE /api/v1/products/{id}` — desactivar (solo OWNER, verifica dependencias)
  - `POST /api/v1/products/{id}/attributes` — asignar atributos (solo OWNER)

**Reglas de auditoría para productos:**
- Cambio de `cost_price` → AuditLog con `old_values` y `new_values`
- Cambio de `sale_price` → AuditLog con `old_values` y `new_values`
- Creación de producto → AuditLog
- Desactivación → AuditLog

**Definición de terminado:**
- [ ] OWNER puede crear producto con SKU automático
- [ ] SALES intenta modificar costo → 403
- [ ] Cambio de precio genera AuditLog con valores anterior y nuevo
- [ ] Producto con ventas activas no puede eliminarse → 409

---

### ALMACENAMIENTO DE ARCHIVOS

---

#### #F02-10 — Módulo de archivos (FileObject + MinIO)
- **Tipo:** `[BE]` `[DB]` `[INFRA]`
- **Prioridad:** 🟠 ALTO
- **Estado:** ⬜ Pendiente
- **Depende de:** FASE-01 completa

**Tareas:**
- [ ] Crear modelo `FileObject`:
  ```
  FileObject:
    id (UUID, PK)
    storage_key (VARCHAR)     — path en S3: "products/uuid.jpg"
    bucket (VARCHAR)
    original_name (VARCHAR)
    mime_type (VARCHAR)
    size (BIGINT)
    checksum (VARCHAR)        — SHA-256
    metadata (JSONB)
    uploaded_by (UUID, FK → User)
    created_at (TIMESTAMPTZ)
  ```
- [ ] Migración
- [ ] Crear `apps/api/app/modules/files/infrastructure/storage.py`:
  - `StorageProvider` (ABC): `upload`, `get_url`, `delete`
  - `MinIOStorageProvider` implementa la interfaz usando `boto3`
- [ ] Servicio `FileService`:
  - `upload_file(file, user)` — valida MIME, calcula checksum, sube a S3, guarda FileObject
  - `get_url(file_id)` — retorna URL firmada con TTL
  - `delete_file(file_id, user)` — marca como eliminado (soft delete)
- [ ] Validaciones obligatorias:
  - MIME type verificado del contenido real (no solo la extensión)
  - Tipos permitidos: `image/jpeg`, `image/png`, `image/webp`, `application/pdf`
  - Tamaño máximo: 10MB (configurable en settings)
- [ ] Endpoint: `POST /api/v1/files/upload` — multipart/form-data
- [ ] Endpoint: `GET /api/v1/files/{id}/url` — obtener URL firmada

**Definición de terminado:**
- [ ] Upload de imagen JPG → FileObject creado, archivo en MinIO
- [ ] Upload de .exe → rechazado aunque tenga extensión .jpg (valida MIME real)
- [ ] URL firmada expira después del TTL configurado

---

#### #F02-11 — Imágenes de productos
- **Tipo:** `[BE]` `[DB]`
- **Prioridad:** 🟠 ALTO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F02-09, #F02-10

**Tareas:**
- [ ] Crear modelo `ProductImage`:
  ```
  ProductImage:
    id (UUID, PK)
    product_id (UUID, FK → Product)
    file_id (UUID, FK → FileObject)
    order (INTEGER)           — orden de visualización
    is_primary (BOOLEAN)      — imagen principal
    created_at (TIMESTAMPTZ)
  ```
- [ ] Migración
- [ ] Endpoints:
  - `POST /api/v1/products/{id}/images` — subir imagen (solo OWNER)
  - `GET /api/v1/products/{id}/images` — listar imágenes
  - `PUT /api/v1/products/{id}/images/{image_id}/primary` — marcar como principal
  - `DELETE /api/v1/products/{id}/images/{image_id}` — eliminar imagen

---

### SEEDS DE PRODUCTOS

---

#### #F02-12 — Seeds de productos ficticios
- **Tipo:** `[BE]` `[DB]`
- **Prioridad:** 🟡 MEDIO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F02-09

**Tareas:**
- [ ] Crear seeder de productos ficticios (datos completamente inventados):
  - 5 laptops con diferentes atributos (RAM, SSD, CPU, marca)
  - 3 computadoras de escritorio
  - 3 impresoras
  - 5 accesorios varios
  - 3 cámaras de seguridad
  - 2 televisores
- [ ] Seed de marcas: HP, Lenovo, Samsung, Canon, Epson, Hikvision, LG
- [ ] Seed de categorías con jerarquía: Electrodomésticos > Televisores, Cómputo > Laptops > Laptops HP, etc.
- [ ] Algunos productos con seriales registrados
- [ ] Algunos productos con ofertas activas

---

### FRONTEND

---

#### #F02-13 — Lista y búsqueda de productos (admin)
- **Tipo:** `[FE]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F02-09

**Tareas:**
- [ ] Crear `apps/web/app/admin/productos/page.tsx`
- [ ] Tabla con: imagen, SKU, nombre, marca, categoría, precio, stock, estado
- [ ] Filtros: categoría, marca, estado (activo/inactivo), publicado/no publicado
- [ ] Búsqueda por nombre, SKU o código de barras (debounce 300ms)
- [ ] Paginación server-side
- [ ] Acciones: ver, editar, desactivar, publicar/despublicar
- [ ] Botón "Nuevo producto" (solo visible para OWNER)
- [ ] Badge de stock bajo (rojo si stock < stock_minimum)

---

#### #F02-14 — Formulario de creación/edición de producto
- **Tipo:** `[FE]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F02-13

**Tareas:**
- [ ] Crear `apps/web/app/admin/productos/nuevo/page.tsx`
- [ ] Crear `apps/web/app/admin/productos/[id]/editar/page.tsx`
- [ ] Formulario con React Hook Form + Zod:
  - Información básica (nombre, descripción corta, descripción completa)
  - Categoría (selector con árbol)
  - Marca (selector)
  - Precios (costo, precio venta, moneda, regla de precio)
  - Atributos dinámicos (agregar/quitar pares atributo-valor)
  - Stock mínimo
  - Si es serializado: checkbox
  - Upload de imágenes (múltiple, arrastrar y soltar)
- [ ] Campos de costo solo visibles y editables por OWNER
- [ ] Validación Zod en frontend (complementaria, no reemplaza backend)

---

#### #F02-15 — Detalle de producto (admin)
- **Tipo:** `[FE]`
- **Prioridad:** 🟡 MEDIO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F02-13

**Tareas:**
- [ ] Crear `apps/web/app/admin/productos/[id]/page.tsx`
- [ ] Mostrar: información completa, imágenes, atributos, seriales, historial de precios, ofertas activas, stock actual
- [ ] Tab de seriales con estados visuales (disponible, reservado, vendido, etc.)
- [ ] Tab de ofertas con fechas y precios

---

#### #F02-16 — Gestión de categorías y marcas (admin)
- **Tipo:** `[FE]`
- **Prioridad:** 🟡 MEDIO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F02-03

**Tareas:**
- [ ] `apps/web/app/admin/categorias/page.tsx` — árbol de categorías con drag-and-drop para reordenar
- [ ] `apps/web/app/admin/marcas/page.tsx` — lista de marcas con logo
- [ ] Formularios de creación/edición para ambas

---

#### #F02-17 — Tienda pública (web)
- **Tipo:** `[FE]`
- **Prioridad:** 🟡 MEDIO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F02-09

**Tareas:**
- [ ] Crear `apps/web/app/(public)/tienda/page.tsx` — catálogo público
- [ ] Solo muestra productos con `published=True` y `active=True`
- [ ] Filtros: categoría, marca, precio, disponibilidad
- [ ] Tarjeta de producto: imagen, nombre, precio (con badge de oferta si aplica), stock
- [ ] Crear `apps/web/app/(public)/tienda/[slug]/page.tsx` — detalle de producto público
- [ ] Botón "Agregar al carrito" (implementar carrito básico en SessionStorage, no requiere cuenta)
- [ ] Botón "Comprar por WhatsApp" — genera link `wa.me` con detalle del producto

---

#### #F02-18 — Carrito de compras básico
- **Tipo:** `[FE]`
- **Prioridad:** 🟡 MEDIO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F02-17

**Descripción:**
Carrito real con persistencia en SessionStorage para usuarios anónimos. Sin pago online todavía.

**Tareas:**
- [ ] Crear `apps/web/features/cart/` con estado global (Zustand o Context)
- [ ] Agregar, quitar y actualizar cantidad en carrito
- [ ] Página de carrito: `apps/web/app/(public)/carrito/page.tsx`
- [ ] Resumen con subtotal, aplicar tipo de cambio para visualización
- [ ] Botón "Finalizar compra por WhatsApp" → link `wa.me` con lista de productos y cantidades
- [ ] Arquitectura preparada para futura integración de pasarelas (Culqi, Izipay, Yape/Plin)

---

### TESTS

---

#### #F02-19 — Tests de productos
- **Tipo:** `[TEST]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F02-09

**Tareas:**
- [ ] `test_create_product_generates_unique_sku` — SKU generado correctamente
- [ ] `test_sku_unique_under_concurrency` — 10 requests simultáneos generan 10 SKUs únicos
- [ ] `test_owner_can_change_price` → 200 + AuditLog creado
- [ ] `test_sales_cannot_change_cost` → 403
- [ ] `test_sales_cannot_change_sale_price` → 403
- [ ] `test_product_offer_active_within_dates` — precio retornado es el de oferta
- [ ] `test_product_offer_inactive_outside_dates` — precio retornado es el normal
- [ ] `test_cannot_duplicate_serial_number` → 409
- [ ] `test_deactivate_product_with_active_sales` → 409
- [ ] `test_published_product_visible_in_public_api` → aparece en tienda

---

#### #F02-20 — Tests de archivos
- **Tipo:** `[TEST]`
- **Prioridad:** 🟠 ALTO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F02-10

**Tareas:**
- [ ] `test_upload_valid_jpeg` → FileObject creado, archivo en MinIO
- [ ] `test_upload_invalid_mime_disguised_as_jpg` → 400 rechazado
- [ ] `test_upload_exceeds_size_limit` → 413
- [ ] `test_get_signed_url` → URL válida generada
- [ ] `test_checksum_matches` — checksum del archivo subido coincide con el guardado

---

#### #F02-21 — Tests de tipo de cambio
- **Tipo:** `[TEST]`
- **Prioridad:** 🟠 ALTO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F02-01

**Tareas:**
- [ ] `test_get_current_exchange_rate` — retorna tasa vigente
- [ ] `test_exchange_rate_uses_decimal_not_float` — el tipo `rate` es `Decimal`
- [ ] `test_conversion_calculation_precision` — conversión sin pérdida de precisión
- [ ] `test_exchange_rate_idempotent_update` — actualizar dos veces el mismo día no duplica

---

### DOCUMENTACIÓN

---

#### #F02-22 — Documentar catálogo en docs/
- **Tipo:** `[DOCS]`
- **Prioridad:** 🟡 MEDIO
- **Estado:** ⬜ Pendiente

**Tareas:**
- [ ] Documentar el sistema de atributos dinámicos en `docs/database.md`
- [ ] Documentar las reglas de precio (FIXED_PEN, USD_CONVERTED, etc.) en `docs/business-rules.md`
- [ ] Documentar el generador de SKU y los prefijos por categoría

---

#### #F02-23 — Gestión de atributos en frontend (admin)
- **Tipo:** `[FE]`
- **Prioridad:** 🟡 MEDIO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F02-04

**Tareas:**
- [ ] `apps/web/app/admin/productos/atributos/page.tsx` — lista de atributos del sistema
- [ ] Formulario para crear nuevo atributo con valores predefinidos
- [ ] Solo OWNER puede crear atributos

---

#### #F02-24 — Verificación final de FASE 02
- **Tipo:** `[INFRA]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** Todos los anteriores

**Checklist de salida de fase:**
- [ ] CRUD de productos completo con permisos correctos
- [ ] SKU generado automáticamente sin duplicados
- [ ] Atributos dinámicos funcionando (RAM, SSD, CPU, etc.)
- [ ] Ofertas activadas automáticamente por fecha
- [ ] Upload de imágenes a MinIO funcionando
- [ ] MIME type validado en servidor
- [ ] Tipo de cambio disponible y actualizado diariamente
- [ ] Tienda pública muestra solo productos publicados
- [ ] Carrito funciona con botón de WhatsApp
- [ ] Cambio de precio/costo registrado en AuditLog
- [ ] Serial duplicado rechazado con 409
- [ ] CI verde
- [ ] PR mergeado a `develop`

---

*Referencia: [REQUIREMENTS.md](../REQUIREMENTS.md) §8 Productos, §6 Tipo de Cambio, §28 Archivos*
*Fase anterior: [FASE 01](FASE-01-auth.md) | Siguiente fase: [FASE 03](FASE-03-inventario-compras.md)*
