# Reglas de Negocio — Precios y SKU

## Reglas de precio de productos

Toda operación de dinero usa `Decimal`; nunca `float`. Precios almacenados en `NUMERIC(14,2)`.

| Regla | Descripción |
|---|---|
| `FIXED_PEN` | Precio fijo en soles (PEN). Se muestra tal cual. |
| `FIXED_USD` | Precio fijo en dólares (USD). Se muestra tal cual (los dólares se convierten a PEN en el precio vigente de tienda). |
| `USD_CONVERTED` | El precio se convierte de USD a PEN con el tipo de cambio vigente al consultar. |
| `COST_USD_MARGIN` | Costo en USD + margen configurado (reservado; se completa en fases de ventas/márgenes). |
| `MANUAL` | Precio fijado manualmente sin cálculo automático. |

### Precio vigente (`get_current_price`)

El orden efectivo implementado es:

1. Si el producto tiene una `ProductOffer` activa con `start_at <= NOW() <= end_at` → se usa el `offer_price`.
2. Si no, se usa `sale_price`.
3. Se muestra en PEN (soles) si:
   - `price_rule == "USD_CONVERTED"`, o
   - `currency == "USD"`.
   La conversión usa la tasa USD→PEN vigente y redondea a 2 decimales (`Decimal("0.01")`).

Ofertas: una oferta es válida solo si está `active=True` y la fecha actual está dentro de `[start_at, end_at]`. Crear oferta exige `offer_price < normal_price` y `end_at > start_at`.

## Generador de SKU

Formato: `{PREFIJO}-{secuencia:05d}` → `LAP-00001`.

- Tabla auxiliar `sku_sequences` (`prefix` VARCHAR PK, `last_value` INT).
- El SKU se genera **dentro de la misma transacción** que crea el producto:
  - `SELECT last_value ... WHERE prefix = :prefix FOR UPDATE`
  - Incremento en 1 y commit con el producto.
- Esto garantiza unicidad bajo concurrencia (test: 100 creates simultáneos → 100 SKUs únicos).
- El SKU nunca se modifica después de creado.

### Prefijos por categoría

Los prefijos son configurables por slug de categoría en `SKU_PREFIX_BY_CATEGORY_SLUG` (settings). Si la categoría no tiene prefijo mapeado, se usa `SKU_DEFAULT_PREFIX` (`PRD`).

Prefijos de semilla (cargados por `seed_sku_prefixes`):

| Prefijo | Uso típico |
|---|---|
| `LAP` | Laptops |
| `IMP` | Impresoras |
| `CAM` | Cámaras |
| `ACC` | Accesorios |
| `ELE` | Electrodomésticos |
| `SRV` | Servicios |
| `SBL` | Sublimación |
| `MON` | Monitores |
| `CEL` | Celulares |
| `TAB` | Tablets |
| `RED` | Redes |
| `ALM` | Alarmas / seguridad |

---
*Referencia: [database.md](database.md), [REQUIREMENTS.md](REQUIREMENTS.md)*