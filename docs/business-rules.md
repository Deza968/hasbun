# Reglas de Negocio

## FASE 02 — Catálogo de Productos

### Reglas de precio (`price_rule`)

Cada producto define cómo se calculó su `sale_price`:

| Regla | Significado |
|---|---|
| `FIXED_PEN` | Precio fijo en soles. La más usada. |
| `FIXED_USD` | Precio fijo en dólares. |
| `USD_CONVERTED` | Precio de venta convertido de USD a PEN usando el tipo de cambio vigente. |
| `COST_USD_MARGIN` | Precio derivado del costo en USD más un margen, convertido a PEN. |
| `MANUAL` | Precio ajustado manualmente; no se recalcula automáticamente. |

**Precio vigente (`current_price`):** el precio de venta, salvo que exista una `ProductOffer` activa con `start_at <= NOW() <= end_at`, en cuyo caso se usa `offer_price`. La oferta se evalúa por fechas, no se desactiva manualmente para el cálculo (el endpoint `DELETE` de oferta existe para baja manual).

### Generador de SKU

- Formato: `{PREFIJO}-{valor:05d}` → `LAP-00001`.
- Prefijos por categoría (configurables en `app/modules/products/application/service.py`):

| Prefijo | Categorías (coincidencia por nombre/slug) |
|---|---|
| `LAP` | Laptops, Computadoras |
| `IMP` | Impresoras |
| `CAM` | Cámaras |
| `ACC` | Accesorios |
| `ELE` | Electrodomésticos, Televisores |
| `SRV` | Servicios |
| `SBL` | Sublimación |
| `MON` | Monitores |
| `CEL` | Celulares |
| `TAB` | Tablets |
| `RED` | Redes, Routers |
| `ALM` | Almacenamiento |
| `PRO` | Fallback (sin categoría conocida) |

- Transaccional: usa `SELECT ... FOR UPDATE` sobre `sku_sequences` para evitar duplicados bajo concurrencia.
- El SKU **nunca se modifica** después de creado.

### Unidades serializadas

- Solo un producto con `is_serialized=True` acepta `serialized_units`.
- `serial_number` e `imei` son únicos: nunca se vende dos veces el mismo serial.
- Estados: `AVAILABLE` → `RESERVED` → `PARTIALLY_PAID` → `SOLD` (también `DELIVERED_ON_CREDIT`, `IN_REPAIR`, `RETURNED`, `DAMAGED`). El cambio de estado queda en AuditLog.

### Auditoría de precios

- Cambio de `cost_price` o `sale_price` → `AuditLog` con `old_values` y `new_values`.
- Evento adicional `PRODUCT_PRICE_CHANGED` registra el cambio de precio explícitamente.
- Creación, desactivación, publicación y baja de productos quedan en `AuditLog`.

### Categorías y marcas

- Eliminación de categoría/marca con productos activos → `409 CONFLICT`.
- Categorías forman un árbol jerárquico (`parent_id` auto-referencia); `GET /categories` lo devuelve anidado.
- La tienda pública solo muestra productos `active=True AND published=True` y no expone `cost_price`.