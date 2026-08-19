# REQUERIMIENTOS DEL SISTEMA — INVERSIONES HASBUN
## Sistema Empresarial ERP + POS + E-Commerce + Servicios

**Versión:** 1.0.0
**Fecha:** 2026-08-17
**Estado:** En definición
**Ubicación:** Sicuani, Canchis, Cusco, Perú

---

## ÍNDICE

1. [Descripción del Negocio](#1-descripción-del-negocio)
2. [Alcance del Sistema](#2-alcance-del-sistema)
3. [Stack Tecnológico](#3-stack-tecnológico)
4. [Arquitectura](#4-arquitectura)
5. [Principios de Diseño](#5-principios-de-diseño)
6. [Moneda y Tipo de Cambio](#6-moneda-y-tipo-de-cambio)
7. [Gestión de Usuarios y Permisos](#7-gestión-de-usuarios-y-permisos)
8. [Módulo de Productos](#8-módulo-de-productos)
9. [Módulo de Inventario](#9-módulo-de-inventario)
10. [Módulo de Compras y Proveedores](#10-módulo-de-compras-y-proveedores)
11. [Módulo de Ventas](#11-módulo-de-ventas)
12. [Módulo de Caja](#12-módulo-de-caja)
13. [Módulo de Créditos y Cuotas](#13-módulo-de-créditos-y-cuotas)
14. [Módulo de Cotizaciones](#14-módulo-de-cotizaciones)
15. [Módulo de Reparaciones](#15-módulo-de-reparaciones)
16. [Módulo de Mantenimientos](#16-módulo-de-mantenimientos)
17. [Módulo de Instalaciones](#17-módulo-de-instalaciones)
18. [Módulo de Garantías](#18-módulo-de-garantías)
19. [Módulo de Delivery y Envíos](#19-módulo-de-delivery-y-envíos)
20. [Módulo de Sublimación y Personalización](#20-módulo-de-sublimación-y-personalización)
21. [Módulo de Desarrollo de Software](#21-módulo-de-desarrollo-de-software)
22. [Módulo de Clientes (CRM)](#22-módulo-de-clientes-crm)
23. [Módulo de WhatsApp](#23-módulo-de-whatsapp)
24. [Módulo de Notificaciones](#24-módulo-de-notificaciones)
25. [Módulo de Reportes](#25-módulo-de-reportes)
26. [Módulo de Auditoría](#26-módulo-de-auditoría)
27. [Módulo de Dashboard](#27-módulo-de-dashboard)
28. [Módulo de Archivos](#28-módulo-de-archivos)
29. [Módulo de Configuración](#29-módulo-de-configuración)
30. [Web Pública y Tienda](#30-web-pública-y-tienda)
31. [Portal del Cliente](#31-portal-del-cliente)
32. [Seguridad](#32-seguridad)
33. [API REST](#33-api-rest)
34. [Transacciones y Consistencia](#34-transacciones-y-consistencia)
35. [Estrategia de Testing](#35-estrategia-de-testing)
36. [Estrategia de Backups](#36-estrategia-de-backups)
37. [Estrategia de Despliegue](#37-estrategia-de-despliegue)
38. [Riesgos Técnicos](#38-riesgos-técnicos)
39. [Riesgos de Negocio](#39-riesgos-de-negocio)
40. [Fases de Implementación](#40-fases-de-implementación)
41. [Criterio de Terminado](#41-criterio-de-terminado)
42. [Reglas Absolutas del Sistema](#42-reglas-absolutas-del-sistema)

---

## 1. DESCRIPCIÓN DEL NEGOCIO

**Razón social:** Inversiones Hasbun
**Rubro:** Tecnología, electrodomésticos, servicios técnicos y personalización
**Ubicación principal:** Sicuani, Canchis, Cusco, Perú

### 1.1 Líneas de negocio

| # | Línea | Descripción |
|---|---|---|
| 1 | Venta de electrodomésticos | Refrigeradoras, lavadoras, televisores, etc. |
| 2 | Venta de computadoras y laptops | Equipos de escritorio, portátiles |
| 3 | Venta de impresoras | Impresoras de inyección, láser, multifuncionales |
| 4 | Venta de accesorios | Teclados, mouse, cables, cartuchos, etc. |
| 5 | Venta de cámaras y accesorios | CCTV, IP, DVR, NVR, cables, fuentes |
| 6 | Reparación de laptops | Diagnóstico, cambio de piezas, formateo |
| 7 | Reparación de computadoras | Hardware y software |
| 8 | Reparación de impresoras | Mecánica, cabezales, placas |
| 9 | Mantenimiento preventivo/correctivo | Limpieza, optimización, actualizaciones |
| 10 | Instalación de cámaras | CCTV, configuración DVR/NVR, cableado |
| 11 | Sublimación | Tazas, polos, telas, productos personalizados |
| 12 | Productos personalizados | Diseño e impresión a pedido |
| 13 | Desarrollo de software | Sistemas, páginas web, aplicaciones |
| 14 | Delivery local | Entrega en Sicuani y alrededores |
| 15 | Envíos de equipos | Envío/recepción por courier para reparaciones |
| 16 | Cotizaciones | Presupuestos formales para clientes |
| 17 | Garantías | Gestión de garantías de productos y reparaciones |

### 1.2 Modalidades de pago

- Venta al contado
- Venta con pago parcial (inicial + saldo)
- Venta a crédito con cuotas
- Cuotas con meses de gracia (interés libre configurable)
- Cuotas con financiamiento (tasa configurable)
- Pago parcial de cuota
- Pago adelantado de cuotas

---

## 2. ALCANCE DEL SISTEMA

El sistema contempla los siguientes módulos funcionales:

| # | Módulo | Tipo |
|---|---|---|
| 1 | Web pública | Frontend público |
| 2 | Tienda online | Frontend público |
| 3 | Cuenta del cliente | Portal privado |
| 4 | Panel administrativo | Frontend privado |
| 5 | POS (Punto de Venta) | Frontend privado |
| 6 | Caja | Backend + Frontend |
| 7 | Inventario | Backend + Frontend |
| 8 | Compras | Backend + Frontend |
| 9 | Proveedores | Backend + Frontend |
| 10 | Créditos | Backend + Frontend |
| 11 | Cuotas | Backend + Frontend |
| 12 | Morosidad | Backend + Frontend |
| 13 | Reparaciones | Backend + Frontend |
| 14 | Mantenimientos | Backend + Frontend |
| 15 | Instalaciones | Backend + Frontend |
| 16 | Cotizaciones | Backend + Frontend |
| 17 | Garantías | Backend + Frontend |
| 18 | Delivery / Envíos | Backend + Frontend |
| 19 | WhatsApp | Backend (servicio) |
| 20 | Sublimación y personalización | Backend + Frontend |
| 21 | Proyectos de software | Backend + Frontend |
| 22 | CRM (Clientes) | Backend + Frontend |
| 23 | Reportes | Backend + Frontend |
| 24 | Auditoría | Backend + Frontend |
| 25 | Notificaciones | Backend + Frontend |
| 26 | Configuración global | Backend + Frontend |
| 27 | Gestión de usuarios y permisos | Backend + Frontend |
| 28 | Dashboard por rol | Frontend |
| 29 | Calendario general | Frontend |
| 30 | Búsqueda global | Backend + Frontend |

### 2.1 Fuera de alcance inicial (preparado para futuro)

- Integración SUNAT / facturación electrónica
- Pasarelas de pago online (Culqi, Izipay, Yape, Plin)
- Editor gráfico para diseños de sublimación
- App móvil nativa (se prioriza web responsive)
- Multi-tienda / multi-sucursal

---

## 3. STACK TECNOLÓGICO

### 3.1 Frontend

| Tecnología | Rol | Versión mínima |
|---|---|---|
| Next.js | Framework React con App Router | 14+ |
| TypeScript | Tipado estático | 5+ |
| Tailwind CSS | Utilidades CSS | 3+ |
| shadcn/ui | Componentes UI accesibles | latest |
| TanStack Query | Estado del servidor, caché, sincronización | 5+ |
| React Hook Form | Gestión de formularios | 7+ |
| Zod | Validación de esquemas (frontend + compartido) | 3+ |

### 3.2 Backend

| Tecnología | Rol | Versión mínima |
|---|---|---|
| Python | Lenguaje principal | 3.12+ |
| FastAPI | Framework HTTP async | 0.110+ |
| Pydantic v2 | Validación y serialización | 2+ |
| SQLAlchemy 2 | ORM async | 2+ |
| asyncpg | Driver PostgreSQL async | latest |
| Alembic | Migraciones de base de datos | latest |

### 3.3 Infraestructura

| Tecnología | Rol |
|---|---|
| PostgreSQL | Base de datos principal |
| Redis | Caché + broker de mensajes |
| Celery | Procesamiento asíncrono y tareas programadas |
| MinIO (dev) / S3-compatible (prod) | Almacenamiento de archivos |
| Docker + Docker Compose | Contenedores y entorno local |
| Nginx | Reverse proxy |

### 3.4 Reglas del stack

- **Dinero:** Siempre `NUMERIC(14,2)` en PostgreSQL. Siempre `Decimal` en Python. Nunca `float`.
- **Porcentajes:** `NUMERIC(5,4)` para tasas (ej: `0.0300` = 3%).
- **IDs:** UUID v4 para todas las entidades principales.
- **Timestamps:** Siempre con timezone. Almacenar en UTC.
- **Autenticación:** Cookies HttpOnly Secure. Sin tokens en localStorage.
- **Secretos:** Solo en variables de entorno. Nunca en código.

---

## 4. ARQUITECTURA

### 4.1 Estructura de carpetas

```
hasbun/
├── .github/workflows/          # CI/CD pipelines
├── apps/
│   ├── api/                    # Backend FastAPI
│   │   ├── alembic/            # Migraciones
│   │   ├── app/
│   │   │   ├── core/           # Config, seguridad, excepciones, logging
│   │   │   ├── database/       # Sesión, base, mixins
│   │   │   └── modules/        # Módulos de negocio
│   │   │       ├── auth/
│   │   │       ├── users/
│   │   │       ├── roles/
│   │   │       ├── permissions/
│   │   │       ├── customers/
│   │   │       ├── products/
│   │   │       ├── categories/
│   │   │       ├── brands/
│   │   │       ├── inventory/
│   │   │       ├── purchases/
│   │   │       ├── suppliers/
│   │   │       ├── sales/
│   │   │       ├── pos/
│   │   │       ├── cash/
│   │   │       ├── credits/
│   │   │       ├── installments/
│   │   │       ├── quotes/
│   │   │       ├── repairs/
│   │   │       ├── maintenance/
│   │   │       ├── installations/
│   │   │       ├── warranties/
│   │   │       ├── deliveries/
│   │   │       ├── shipping/
│   │   │       ├── sublimation/
│   │   │       ├── software_projects/
│   │   │       ├── notifications/
│   │   │       ├── whatsapp/
│   │   │       ├── exchange_rates/
│   │   │       ├── reports/
│   │   │       ├── audit/
│   │   │       ├── files/
│   │   │       ├── dashboard/
│   │   │       └── settings/
│   │   └── tests/
│   ├── worker/                 # Celery worker + beat
│   └── web/                    # Frontend Next.js
│       ├── app/
│       │   ├── (public)/       # Web pública y tienda
│       │   ├── (auth)/         # Login y registro
│       │   ├── admin/          # Panel administrativo
│       │   └── customer/       # Portal del cliente
│       ├── components/
│       ├── features/
│       ├── lib/
│       ├── hooks/
│       ├── services/
│       └── types/
├── infra/                      # Docker, Nginx, Postgres, Redis, Storage
├── docs/                       # Documentación técnica y de negocio
└── tests/                      # E2E y pruebas de carga
```

### 4.2 Estructura interna de cada módulo backend

```
modules/{modulo}/
├── domain/
│   ├── models.py       # Modelos SQLAlchemy
│   ├── entities.py     # Objetos de dominio puros (sin ORM)
│   └── exceptions.py   # Excepciones específicas del dominio
├── application/
│   ├── service.py      # Casos de uso (lógica de negocio)
│   ├── schemas.py      # Pydantic schemas (request/response)
│   └── commands.py     # Objetos de comando
├── infrastructure/
│   └── repository.py   # Acceso a datos (SQL)
└── api/
    └── router.py       # Endpoints delgados (solo HTTP → service)
```

### 4.3 Capas de separación obligatoria

```
DOMAIN       → modelos, entidades, reglas de negocio puras
APPLICATION  → casos de uso, orquestación, validación de negocio
INFRASTRUCTURE → repositorios, acceso a BD, servicios externos
API          → HTTP: parsing, autenticación, respuesta
```

**Regla:** Los routers FastAPI no contienen lógica de negocio.
**Regla:** Los componentes React no contienen lógica financiera.

---

## 5. PRINCIPIOS DE DISEÑO

| # | Principio | Descripción |
|---|---|---|
| 1 | Integridad financiera primero | Toda operación de dinero es atómica. Sin transacción = sin operación. |
| 2 | Sin simplificaciones en caja | La caja real tiene estados, sesiones, diferencias y auditoría. |
| 3 | Sin simplificaciones en inventario | El stock es la suma de movimientos, no un campo editable. |
| 4 | Sin simplificaciones en créditos | Los créditos tienen reglas, estados, límites y autorización. |
| 5 | Backend es la fuente de verdad | Todo permiso, regla y validación crítica vive en el backend. |
| 6 | Nunca borrar información financiera | Solo estados: CANCELLED, RETURNED, REVERSED. |
| 7 | Auditoría obligatoria | Toda modificación sensible registra quién, qué, cuándo, antes, después. |
| 8 | Idempotencia en operaciones críticas | Pagos, ventas y mensajes WhatsApp soportan idempotency keys. |
| 9 | Consistencia sobre rendimiento | Si hay conflicto entre velocidad e integridad, gana integridad. |
| 10 | Separación de roles estricta | Un vendedor no puede ver cajas ajenas. Un técnico no ve costos. |

---

## 6. MONEDA Y TIPO DE CAMBIO

### 6.1 Monedas soportadas

| Moneda | Símbolo | Rol |
|---|---|---|
| PEN (Sol peruano) | S/ | Moneda principal |
| USD (Dólar americano) | $ | Moneda secundaria |

### 6.2 Reglas de moneda

- Toda operación registra: `currency`, `exchange_rate`, `exchange_rate_source`, `exchange_rate_timestamp`
- El tipo de cambio se **congela** al momento de la operación. Nunca se recalcula históricamente.
- La interfaz puede mostrar montos en PEN o USD para visualización. Nunca altera el valor registrado.
- Los precios tienen reglas configurables:

| Regla | Descripción |
|---|---|
| `FIXED_PEN` | Precio fijo en soles, no se convierte |
| `FIXED_USD` | Precio fijo en dólares, no se convierte |
| `USD_CONVERTED` | Precio en USD convertido a PEN con tipo de cambio del día |
| `COST_USD_MARGIN` | Costo en USD + margen de ganancia configurado |
| `MANUAL` | Precio ingresado manualmente por OWNER |

### 6.3 Módulo ExchangeRate

**Tabla `exchange_rates`:**

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | UUID | PK |
| `currency_from` | VARCHAR(3) | Ej: USD |
| `currency_to` | VARCHAR(3) | Ej: PEN |
| `rate` | NUMERIC(10,4) | Tipo de cambio |
| `source` | VARCHAR(50) | mock / sunat / bcp / manual |
| `effective_at` | TIMESTAMPTZ | Desde cuándo aplica |
| `created_at` | TIMESTAMPTZ | Registro |

**Interfaz `ExchangeRateProvider`:**
- Implementación inicial: `MockExchangeRateProvider`
- Implementación futura: `ExternalExchangeRateProvider` (SUNAT, BCP, etc.)
- Actualización automática: 1 vez por día vía tarea Celery
- Nunca modificar precios negociados silenciosamente
- Registrar historial de cambios de precio con razón

---

## 7. GESTIÓN DE USUARIOS Y PERMISOS

### 7.1 Roles base

| Rol | Código | Descripción |
|---|---|---|
| Dueña / Administradora | `OWNER` | Acceso total sin restricciones |
| Vendedor | `SALES` | Ventas, POS, clientes, cotizaciones |
| Técnico | `TECHNICIAN` | Reparaciones, mantenimientos, instalaciones |
| Desarrollador de software | `SOFTWARE_DEVELOPER` | Proyectos, publicaciones web |
| Cliente | `CUSTOMER` | Portal propio, compras, garantías |

### 7.2 Modelo de datos de permisos

```
User                  → datos personales, credenciales
Role                  → nombre, descripción
Permission            → codename, descripción, módulo
UserRole              → user_id + role_id
RolePermission        → role_id + permission_id
UserPermissionOverride → user_id + permission_id + granted (bool)
```

El sistema usa **RBAC + overrides personalizados**. La dueña puede conceder o revocar permisos específicos a usuarios individuales sin cambiar su rol.

### 7.3 Permisos del rol OWNER

Acceso completo a: productos, categorías, marcas, inventario, compras, proveedores, ventas, POS, cajas, créditos, cuotas, clientes, reparaciones, mantenimientos, instalaciones, cotizaciones, garantías, delivery, proyectos, publicaciones, reportes, usuarios, permisos, auditoría, configuración.

### 7.4 Permisos del rol SALES

**Puede:**
- Crear y gestionar ventas
- Operar POS
- Gestionar clientes
- Ver productos (no modificar costo)
- Crear cotizaciones
- Gestionar pedidos
- Operar su propia caja

**No puede:**
- Modificar costos de productos
- Administrar usuarios o permisos
- Eliminar productos
- Modificar configuración crítica
- Aprobar sus propias autorizaciones de descuento
- Ver cajas de otros usuarios

**Puede solicitar:**
- Autorización de descuento (requiere aprobación OWNER)
- Cancelación de venta (requiere aprobación OWNER)

### 7.5 Permisos del rol TECHNICIAN

**Puede:**
- Gestionar reparaciones asignadas
- Gestionar mantenimientos asignados
- Gestionar instalaciones asignadas
- Ver clientes relacionados a sus órdenes
- Registrar diagnósticos, tareas y evidencias
- Subir fotografías de evidencia
- Redactar informes técnicos
- Solicitar repuestos de inventario (NO consumir directamente)

**No puede:**
- Administrar usuarios
- Modificar configuración del sistema
- Ver información financiera sensible (costos, márgenes)
- Modificar precios de venta
- Modificar costos
- Aprobar sus propias solicitudes financieras

### 7.6 Permisos del rol SOFTWARE_DEVELOPER

**Puede:**
- Administrar proyectos de software
- Registrar trabajos realizados
- Publicar y editar publicaciones web
- Gestionar imágenes de proyectos
- Administrar casos de éxito de clientes

**No puede:**
- Modificar caja, inventario, créditos
- Administrar usuarios
- Modificar configuración financiera

### 7.7 Permisos del rol CUSTOMER

**Puede:**
- Gestionar su perfil personal
- Ver sus propias compras
- Ver sus cuotas y estado de pagos
- Ver sus reparaciones y estado
- Ver sus cotizaciones y garantías
- Ver sus pedidos y envíos
- Consultar estado de reparación por código
- Enviar solicitudes (cotización, reparación)
- Iniciar compra vía WhatsApp

**No puede:**
- Ver información de otros clientes
- Acceder al panel administrativo
- Ver información financiera del negocio

---

## 8. MÓDULO DE PRODUCTOS

### 8.1 Entidad Product

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | UUID | PK |
| `sku` | VARCHAR | Código único auto-generado (ej: LAP-00001) |
| `barcode` | VARCHAR | Código de barras (opcional) |
| `name` | VARCHAR | Nombre del producto |
| `slug` | VARCHAR | URL amigable única |
| `description` | TEXT | Descripción completa |
| `short_description` | TEXT | Descripción corta para tarjetas |
| `brand_id` | UUID | FK → Brand |
| `category_id` | UUID | FK → Category |
| `cost_price` | NUMERIC(14,2) | Costo de compra |
| `sale_price` | NUMERIC(14,2) | Precio de venta base |
| `currency` | VARCHAR(3) | PEN o USD |
| `price_rule` | ENUM | FIXED_PEN / FIXED_USD / USD_CONVERTED / COST_USD_MARGIN / MANUAL |
| `active` | BOOLEAN | Activo en el sistema |
| `published` | BOOLEAN | Visible en tienda pública |
| `stock_minimum` | INTEGER | Alerta de stock bajo |
| `is_serialized` | BOOLEAN | Tiene número de serie único |
| `created_at` | TIMESTAMPTZ | |
| `updated_at` | TIMESTAMPTZ | |

### 8.2 Generación de SKU

- El SKU se genera automáticamente al crear el producto
- Formato: `{PREFIJO}-{SECUENCIA_5_DIGITOS}`
- Prefijos por categoría: `LAP`, `IMP`, `CAM`, `ACC`, `ELE`, `SRV`, `SBL`, etc.
- La generación es **transaccional** para evitar duplicados bajo concurrencia
- El SKU nunca se modifica después de creado

### 8.3 Sistema de atributos dinámicos

No se crean columnas por atributo. Se usan tres tablas:

```
Attribute         → id, name, data_type (text/number/boolean/list)
AttributeValue    → id, attribute_id, value
ProductAttributeValue → product_id, attribute_value_id
```

Ejemplos de atributos: RAM, SSD, CPU, Pantalla, Color, Capacidad, Resolución, Modelo, Voltaje, Tipo de cámara, Megapíxeles.

### 8.4 Unidades serializadas

Para productos electrónicos de alto valor:

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | UUID | PK |
| `product_id` | UUID | FK → Product |
| `serial_number` | VARCHAR | Número de serie (unique) |
| `imei` | VARCHAR | IMEI principal (opcional) |
| `imei2` | VARCHAR | IMEI secundario (opcional) |
| `mac_address` | VARCHAR | Dirección MAC (opcional) |
| `status` | ENUM | AVAILABLE / RESERVED / PARTIALLY_PAID / DELIVERED_ON_CREDIT / SOLD / IN_REPAIR / RETURNED / DAMAGED |

**Regla:** No se puede vender dos veces el mismo número de serie. Constraint único en BD.

### 8.5 Ofertas de productos

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | UUID | PK |
| `product_id` | UUID | FK → Product |
| `normal_price` | NUMERIC(14,2) | Precio sin oferta |
| `offer_price` | NUMERIC(14,2) | Precio con oferta |
| `start_at` | TIMESTAMPTZ | Inicio de la oferta |
| `end_at` | TIMESTAMPTZ | Fin de la oferta |
| `active` | BOOLEAN | Activación manual adicional |

El precio de oferta se activa automáticamente según fecha. El sistema evalúa en tiempo real si aplica la oferta.

### 8.6 Categorías y marcas

- **Category:** id, name, slug, parent_id (categorías anidadas), active
- **Brand:** id, name, slug, logo_file_id, active

### 8.7 Reglas de negocio — Productos

- Solo OWNER puede crear, editar o eliminar productos
- Solo OWNER puede modificar `cost_price`
- Cualquier cambio de precio genera entrada en auditoría con valor anterior y posterior
- Un producto no puede eliminarse si tiene ventas, movimientos de inventario o reparaciones activas. Se desactiva (`active = false`)
- El `slug` es único y se genera del nombre del producto

---

## 9. MÓDULO DE INVENTARIO

### 9.1 Principio fundamental

> El stock nunca es un campo editable. El stock es la **suma de movimientos**.

```
stock_disponible = SUM(quantity) WHERE product_id = X AND movement_type IN (entrada) 
                 - SUM(quantity) WHERE product_id = X AND movement_type IN (salida)
```

### 9.2 Entidad InventoryMovement

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | UUID | PK |
| `product_id` | UUID | FK → Product |
| `serialized_unit_id` | UUID | FK → SerializedUnit (si aplica) |
| `quantity` | NUMERIC(14,3) | Positivo o negativo según tipo |
| `movement_type` | ENUM | Ver tabla siguiente |
| `reference_type` | VARCHAR | sale / purchase / repair / adjustment / etc. |
| `reference_id` | UUID | ID del documento origen |
| `warehouse` | VARCHAR | Ubicación / almacén |
| `unit_cost` | NUMERIC(14,2) | Costo unitario al momento del movimiento |
| `notes` | TEXT | Observaciones |
| `created_by` | UUID | FK → User |
| `created_at` | TIMESTAMPTZ | |

### 9.3 Tipos de movimiento

| Tipo | Dirección | Descripción |
|---|---|---|
| `PURCHASE` | + | Ingreso por compra a proveedor |
| `SALE` | - | Salida por venta contado |
| `RESERVATION` | - virtual | Reserva por pago inicial |
| `RELEASE_RESERVATION` | + virtual | Liberación de reserva cancelada |
| `PARTIAL_PAYMENT_HOLD` | - virtual | Retenido por pago parcial |
| `CREDIT_DELIVERY` | - | Entrega física antes de pago total |
| `SALE_COMPLETED` | - | Venta finalizada (crédito completado) |
| `RETURN` | + | Devolución al inventario |
| `ADJUSTMENT_IN` | + | Ajuste de entrada (requiere autorización) |
| `ADJUSTMENT_OUT` | - | Ajuste de salida (requiere autorización) |
| `REPAIR_USAGE` | - | Repuesto consumido en reparación |
| `REPAIR_RETURN` | + | Repuesto no usado regresa al inventario |
| `DAMAGED` | - | Producto dañado dado de baja |
| `TRANSFER` | +/- | Transferencia entre almacenes |

### 9.4 Estados físico-financieros del stock

| Estado | Descripción |
|---|---|
| `AVAILABLE` | Disponible para venta inmediata |
| `RESERVED` | Reservado por pago inicial (no disponible) |
| `PARTIALLY_PAID` | Con pago parcial registrado |
| `DELIVERED_ON_CREDIT` | Entregado físicamente, crédito pendiente |
| `SOLD` | Vendido y completamente pagado |
| `IN_REPAIR` | En proceso de reparación |
| `RETURNED` | Devuelto al inventario |
| `DAMAGED` | Dado de baja por daño |

**Ejemplo de dashboard de inventario:**
```
Laptop HP 15s:
  Disponible:          5 unidades
  Reservada:           1 unidad
  Pagada parcialmente: 1 unidad
  Entregada a crédito: 1 unidad
  Vendida:             2 unidades
```

### 9.5 Reglas de negocio — Inventario

- El stock no puede quedar en negativo. Constraint en BD + validación en servicio.
- Todo movimiento de inventario debe estar asociado a un documento origen (venta, compra, reparación, etc.)
- Los ajustes manuales requieren autorización de OWNER y generan entrada en auditoría
- El kardex es la lista ordenada cronológicamente de movimientos de un producto
- La concurrencia se maneja con `SELECT ... FOR UPDATE` en operaciones de venta simultánea

---

## 10. MÓDULO DE COMPRAS Y PROVEEDORES

### 10.1 Entidad Supplier (Proveedor)

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | UUID | PK |
| `razon_social` | VARCHAR | Nombre legal |
| `ruc` | VARCHAR | RUC (único) |
| `nombre_comercial` | VARCHAR | Nombre comercial |
| `contacto_nombre` | VARCHAR | Nombre del contacto |
| `telefono` | VARCHAR | Teléfono de contacto |
| `email` | VARCHAR | Email |
| `direccion` | TEXT | Dirección |
| `ciudad` | VARCHAR | Ciudad |
| `active` | BOOLEAN | Activo |
| `notes` | TEXT | Observaciones |
| `created_at` | TIMESTAMPTZ | |

### 10.2 Entidad Purchase (Orden de Compra)

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | UUID | PK |
| `code` | VARCHAR | Código OC-YYYY-XXXXX |
| `supplier_id` | UUID | FK → Supplier |
| `status` | ENUM | DRAFT / ORDERED / RECEIVED / PARTIAL / CANCELLED |
| `total` | NUMERIC(14,2) | Total de la compra |
| `currency` | VARCHAR(3) | PEN o USD |
| `exchange_rate` | NUMERIC(10,4) | TC al momento |
| `invoice_number` | VARCHAR | Número de factura del proveedor |
| `received_at` | TIMESTAMPTZ | Fecha de recepción |
| `notes` | TEXT | |
| `created_by` | UUID | FK → User |
| `created_at` | TIMESTAMPTZ | |

### 10.3 Entidad PurchaseItem

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | UUID | PK |
| `purchase_id` | UUID | FK → Purchase |
| `product_id` | UUID | FK → Product |
| `quantity` | NUMERIC(14,3) | Cantidad comprada |
| `unit_cost` | NUMERIC(14,2) | Costo unitario |
| `subtotal` | NUMERIC(14,2) | quantity × unit_cost |
| `received_quantity` | NUMERIC(14,3) | Cantidad efectivamente recibida |

### 10.4 Flujo de compra

```
1. OWNER crea Purchase (DRAFT) con items
2. Se confirma el pedido (ORDERED)
3. Al recibir mercadería:
   a. Se registran cantidades recibidas
   b. [TRANSACCIÓN ATÓMICA]:
      - Purchase.status = RECEIVED (o PARTIAL si es parcial)
      - InventoryMovement (PURCHASE) por cada item
      - Actualizar cost_price del producto (si corresponde)
      - AuditLog
```

### 10.5 Reglas de negocio — Compras

- Solo OWNER puede crear compras
- Una compra recibida genera movimientos de inventario automáticamente
- No se puede eliminar una compra recibida, solo cancelar con justificación
- El costo del producto puede actualizarse con el costo de la última compra (configurable)
- Las compras en USD registran el tipo de cambio del momento

---

## 11. MÓDULO DE VENTAS

### 11.1 Tipos de venta

| Tipo | Código | Descripción |
|---|---|---|
| Contado | `CASH` | Pago completo inmediato |
| Pago parcial | `PARTIAL` | Inicial + saldo diferido |
| Crédito con cuotas | `CREDIT` | Financiamiento con cuotas |

### 11.2 Entidad Sale

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | UUID | PK |
| `code` | VARCHAR | VTA-YYYY-XXXXX |
| `customer_id` | UUID | FK → Customer |
| `sale_type` | ENUM | CASH / PARTIAL / CREDIT |
| `status` | ENUM | Ver tabla de estados |
| `subtotal` | NUMERIC(14,2) | Sin descuentos |
| `discount_amount` | NUMERIC(14,2) | Descuento total |
| `total` | NUMERIC(14,2) | Total a pagar |
| `currency` | VARCHAR(3) | PEN o USD |
| `exchange_rate` | NUMERIC(10,4) | TC congelado |
| `exchange_rate_source` | VARCHAR | Fuente del TC |
| `exchange_rate_timestamp` | TIMESTAMPTZ | Momento del TC |
| `discount_authorization_id` | UUID | FK → DiscountAuthorization |
| `idempotency_key` | VARCHAR | Clave única de idempotencia |
| `notes` | TEXT | Observaciones |
| `created_by` | UUID | FK → User |
| `created_at` | TIMESTAMPTZ | |
| `updated_at` | TIMESTAMPTZ | |

### 11.3 Estados de venta

| Estado | Descripción |
|---|---|
| `DRAFT` | Borrador, aún no confirmada |
| `PENDING_PAYMENT` | Confirmada, esperando pago |
| `PARTIALLY_PAID` | Con pago inicial registrado |
| `PAID` | Completamente pagada |
| `CANCELLED` | Cancelada (no se borra) |
| `RETURNED` | Con devolución total |
| `COMPLETED` | Entregada y finalizada |

### 11.4 Entidad SaleItem

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | UUID | PK |
| `sale_id` | UUID | FK → Sale |
| `product_id` | UUID | FK → Product |
| `serialized_unit_id` | UUID | FK → SerializedUnit (si aplica) |
| `quantity` | NUMERIC(14,3) | |
| `unit_price` | NUMERIC(14,2) | Precio al momento de la venta |
| `unit_cost` | NUMERIC(14,2) | Costo al momento (para margen) |
| `discount_amount` | NUMERIC(14,2) | Descuento por ítem |
| `subtotal` | NUMERIC(14,2) | |

### 11.5 Entidad SalePayment

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | UUID | PK |
| `sale_id` | UUID | FK → Sale |
| `method` | ENUM | CASH / YAPE / PLIN / CARD / BANK_TRANSFER / OTHER |
| `method_detail` | VARCHAR | Detalle si method = OTHER |
| `amount` | NUMERIC(14,2) | |
| `reference` | VARCHAR | Nro. operación, voucher |
| `idempotency_key` | VARCHAR | |
| `paid_at` | TIMESTAMPTZ | |
| `registered_by` | UUID | FK → User |

### 11.6 Flujo de venta al contado

```
1. Operador selecciona productos en POS
2. Sistema verifica stock (SELECT FOR UPDATE)
3. Sistema calcula total con TC vigente
4. Si hay descuento: verifica DiscountAuthorization
5. Crea Sale (DRAFT)
6. Registra SalePayment
[TRANSACCIÓN ATÓMICA]:
   - Sale.status = PAID
   - SaleItem × N
   - CashMovement (INCOME) en caja activa
   - InventoryMovement (SALE) × N
   - Si serializado: SerializedUnit.status = SOLD
   - AuditLog
7. Tarea asíncrona: WhatsApp de confirmación al cliente
```

### 11.7 Flujo de venta a crédito

```
1. Operador selecciona productos
2. Sistema verifica:
   a. Límite de crédito del cliente
   b. Morosidad activa (bloqueo automático)
   c. Créditos activos (si > 0, requiere OWNER)
3. OWNER autoriza CreditAuthorization
4. Se define: monto inicial, cuotas, meses gracia, tasa
5. Operador registra pago inicial
[TRANSACCIÓN ATÓMICA]:
   - Sale creada
   - CreditAgreement creado
   - CreditInstallment × N generadas
   - CashMovement (inicial)
   - InventoryMovement (RESERVATION)
   - AuditLog
6. WhatsApp: cuotas y calendario de pagos
```

### 11.8 Descuentos

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | UUID | PK |
| `sale_id` | UUID | FK → Sale |
| `type` | ENUM | PERCENTAGE / FIXED_AMOUNT |
| `percentage` | NUMERIC(5,4) | Si type = PERCENTAGE |
| `fixed_amount` | NUMERIC(14,2) | Si type = FIXED_AMOUNT |
| `reason` | TEXT | Motivo obligatorio |
| `requested_by` | UUID | FK → User |
| `approved_by` | UUID | FK → User (OWNER) |
| `status` | ENUM | PENDING / APPROVED / REJECTED |
| `created_at` | TIMESTAMPTZ | |

**Reglas de descuento:**
- OWNER aplica directamente sin autorización previa
- SALES solicita y espera aprobación de OWNER
- Descuento negativo: NUNCA permitido (constraint en BD)
- Todo descuento queda auditado con antes/después del precio

### 11.9 Devoluciones

**Motivos válidos:**
- `WITHIN_24_HOURS`: dentro de las 24 horas de la compra
- `WARRANTY`: por garantía del producto
- `CREDIT_CANCELLATION`: cancelación de crédito
- `OTHER_AUTHORIZED`: otro motivo con autorización de OWNER

**Proceso:**
```
1. Se crea Return + ReturnItem
2. Se evalúa condición del producto
3. [TRANSACCIÓN ATÓMICA]:
   - Return registrado
   - Sale.status actualizado
   - InventoryMovement (RETURN)
   - CashAdjustment (si hay reembolso)
   - AuditLog
4. NUNCA se elimina la venta original
```

---

## 12. MÓDULO DE CAJA

### 12.1 Modelo de caja

```
CashRegister   → caja física asignada a un usuario
CashSession    → apertura/cierre de caja en un turno
CashMovement   → cada transacción dentro de la sesión
CashTransfer   → transferencia entre dos cajas
CashClosureRequest → solicitud de cierre con diferencia
```

### 12.2 Entidad CashRegister

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | UUID | PK |
| `name` | VARCHAR | Nombre de la caja (ej: "Caja 1 - Ventas") |
| `user_id` | UUID | FK → User (propietario asignado) |
| `is_general` | BOOLEAN | True solo para la caja general del OWNER |
| `active` | BOOLEAN | |
| `created_at` | TIMESTAMPTZ | |

### 12.3 Entidad CashSession

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | UUID | PK |
| `register_id` | UUID | FK → CashRegister |
| `user_id` | UUID | FK → User (quien abre) |
| `status` | ENUM | OPEN / PENDING_CLOSURE / CLOSED |
| `opening_amount` | NUMERIC(14,2) | Monto de apertura |
| `expected_cash` | NUMERIC(14,2) | Calculado por el sistema |
| `counted_cash` | NUMERIC(14,2) | Ingresado por el usuario al cierre |
| `difference` | NUMERIC(14,2) | counted_cash - expected_cash |
| `opened_at` | TIMESTAMPTZ | |
| `closed_at` | TIMESTAMPTZ | |
| `opened_by` | UUID | FK → User |
| `closed_by` | UUID | FK → User |

**Regla:** Un usuario solo puede tener **UNA** sesión abierta a la vez.

### 12.4 Entidad CashMovement

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | UUID | PK |
| `session_id` | UUID | FK → CashSession |
| `type` | ENUM | Ver tipos |
| `amount` | NUMERIC(14,2) | Siempre positivo |
| `direction` | ENUM | IN / OUT |
| `reference_type` | VARCHAR | sale / credit_payment / repair / etc. |
| `reference_id` | UUID | ID del documento origen |
| `reason` | TEXT | Descripción del movimiento |
| `authorized_by` | UUID | FK → User (si requiere autorización) |
| `idempotency_key` | VARCHAR | |
| `created_by` | UUID | FK → User |
| `created_at` | TIMESTAMPTZ | |

**Tipos de movimiento de caja:**

| Tipo | Dir. | Descripción |
|---|---|---|
| `SALE_INCOME` | IN | Cobro de venta |
| `CREDIT_PAYMENT` | IN | Cobro de cuota |
| `REPAIR_PAYMENT` | IN | Cobro de reparación |
| `INSTALLATION_PAYMENT` | IN | Cobro de instalación |
| `QUOTE_PAYMENT` | IN | Cobro de cotización convertida |
| `TRANSFER_IN` | IN | Recepción de transferencia |
| `OTHER_INCOME` | IN | Ingreso manual autorizado |
| `EXPENSE` | OUT | Egreso autorizado |
| `TRANSFER_OUT` | OUT | Envío de transferencia |
| `OPENING` | IN | Apertura de caja |

### 12.5 Flujo de cierre de caja

```
1. Cajero solicita cierre
2. Sistema calcula expected_cash:
   expected = opening_amount + SUM(IN movements) - SUM(OUT movements)
3. Cajero ingresa counted_cash (conteo físico)
4. difference = counted_cash - expected_cash

Si difference == 0:
   → Cierre inmediato permitido
   → CashSession.status = CLOSED
   → AuditLog

Si difference != 0:
   → CashSession.status = PENDING_CLOSURE
   → Crear CashClosureRequest
   → Notificación a OWNER (sistema interno + WhatsApp)
   
   OWNER decide:
   
   APPROVE (motivo obligatorio):
     → CashSession.status = CLOSED
     → CashClosureRequest.status = APPROVED
     → AuditLog con diferencia y motivo
   
   REJECT:
     → Cajero debe reabrir y recontar
     → CashClosureRequest.status = REJECTED
```

### 12.6 Transferencias entre cajas

```
[TRANSACCIÓN ATÓMICA]:
  - CashMovement(TRANSFER_OUT) en caja origen
  - CashMovement(TRANSFER_IN) en caja destino
  - CashTransfer registrado
  - AuditLog
Si falla cualquier parte: ROLLBACK total
```

### 12.7 Ingresos y egresos manuales

- Requieren: `amount`, `reason`, `authorized_by`
- Solo OWNER autoriza egresos y otros ingresos manuales
- Todo queda en auditoría

### 12.8 Visibilidad de cajas

| Rol | Ve su caja | Ve otras cajas | Ve caja general |
|---|---|---|---|
| OWNER | ✅ | ✅ | ✅ |
| SALES | ✅ | ❌ | ❌ |
| TECHNICIAN | ❌ | ❌ | ❌ |

---

## 13. MÓDULO DE CRÉDITOS Y CUOTAS

### 13.1 Entidad CreditAgreement

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | UUID | PK |
| `code` | VARCHAR | CRD-YYYY-XXXXX |
| `customer_id` | UUID | FK → Customer |
| `sale_id` | UUID | FK → Sale |
| `status` | ENUM | Ver estados |
| `total_amount` | NUMERIC(14,2) | Precio total del bien |
| `initial_payment` | NUMERIC(14,2) | Inicial pagada |
| `financed_amount` | NUMERIC(14,2) | total - initial |
| `number_of_installments` | INTEGER | Número de cuotas |
| `installment_amount` | NUMERIC(14,2) | Monto por cuota |
| `interest_rate` | NUMERIC(5,4) | Tasa mensual (ej: 0.0300) |
| `interest_free_months` | INTEGER | Meses sin interés |
| `currency` | VARCHAR(3) | |
| `exchange_rate` | NUMERIC(10,4) | TC congelado |
| `authorized_by` | UUID | FK → User (OWNER) |
| `authorization_id` | UUID | FK → CreditAuthorization |
| `first_due_date` | DATE | Fecha primera cuota |
| `created_by` | UUID | FK → User |
| `created_at` | TIMESTAMPTZ | |

### 13.2 Estados del crédito

| Estado | Descripción |
|---|---|
| `PENDING_APPROVAL` | Esperando autorización del OWNER |
| `APPROVED` | Autorizado, pendiente de inicio |
| `ACTIVE` | Con cuotas en curso |
| `PAID` | Completamente saldado |
| `OVERDUE` | Con cuotas vencidas |
| `DEFAULTED` | En mora significativa |
| `CANCELLED` | Cancelado con justificación |
| `RESTRUCTURED` | Reprogramado |

### 13.3 Entidad CreditInstallment

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | UUID | PK |
| `agreement_id` | UUID | FK → CreditAgreement |
| `number` | INTEGER | Número de cuota (1, 2, 3...) |
| `amount` | NUMERIC(14,2) | Monto original de la cuota |
| `due_date` | DATE | Fecha de vencimiento |
| `paid_amount` | NUMERIC(14,2) | Lo pagado hasta ahora |
| `remaining_amount` | NUMERIC(14,2) | Saldo pendiente |
| `status` | ENUM | PENDING / PARTIALLY_PAID / PAID / OVERDUE / RESTRUCTURED / CANCELLED |
| `mora_amount` | NUMERIC(14,2) | Mora acumulada |
| `original_due_date` | DATE | Fecha original (antes de reprogramación) |
| `restructured_at` | TIMESTAMPTZ | |
| `restructured_by` | UUID | FK → User |

### 13.4 Entidad CreditPayment

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | UUID | PK |
| `installment_id` | UUID | FK → CreditInstallment |
| `agreement_id` | UUID | FK → CreditAgreement |
| `amount` | NUMERIC(14,2) | Monto del pago |
| `method` | ENUM | CASH / YAPE / PLIN / CARD / BANK_TRANSFER / OTHER |
| `reference` | VARCHAR | Nro. operación |
| `idempotency_key` | VARCHAR | Prevenir doble cobro |
| `paid_at` | TIMESTAMPTZ | |
| `registered_by` | UUID | FK → User |

### 13.5 Mora

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | UUID | PK |
| `installment_id` | UUID | FK → CreditInstallment |
| `agreement_id` | UUID | FK → CreditAgreement |
| `principal_vencido` | NUMERIC(14,2) | Saldo base sobre el que se calcula |
| `rate` | NUMERIC(5,4) | Tasa aplicada (default 3%) |
| `mora_amount` | NUMERIC(14,2) | Monto de mora generado |
| `period` | VARCHAR | YYYY-MM |
| `applied_at` | TIMESTAMPTZ | |
| `generated_by` | VARCHAR | system / manual |

**Reglas de mora:**
- Tasa por defecto: 3% mensual sobre saldo vencido
- La tasa es configurable en la configuración del sistema
- Aplicación: mensual por tarea automática (Celery)
- **NO se capitaliza mora sobre mora**
- La tarea es idempotente (verifica si ya existe mora para ese período antes de crear)

### 13.6 Reglas de negocio — Créditos

| Regla | Descripción |
|---|---|
| Inicial obligatoria | Siempre debe existir pago inicial. Excepción: cliente frecuente + autorización OWNER |
| Verificación pre-aprobación | Verificar límite, créditos activos, morosidad, historial, capacidad configurada |
| Cliente moroso bloqueado | Si tiene deudas vencidas, NO puede tomar nuevo crédito. Solo OWNER puede desbloquear |
| Límite de crédito | Si operación supera `credit_limit`, alerta y bloqueo hasta autorización |
| Múltiples créditos activos | Permitido solo con autorización explícita de OWNER |
| Pago parcial de cuota | Permitido. Registra exactamente cuánto se pagó y cuánto queda |
| Pago adelantado | Permitido. Sistema registra qué cuotas se afectaron. No altera historial |
| Historial inmutable | Los pagos registrados nunca se modifican ni borran |

### 13.7 Meses de gracia (interés libre)

```
Ejemplo: 4 cuotas, 2 meses de gracia, tasa 3% después

Cuota 1 (mes 1): S/500 → sin interés
Cuota 2 (mes 2): S/500 → sin interés
Cuota 3 (mes 3): S/500 + interés sobre saldo
Cuota 4 (mes 4): S/500 + interés sobre saldo
```

### 13.8 Entrega antes de terminar de pagar

```
Estado: DELIVERED_ON_CREDIT
  - El producto deja el inventario físicamente
  - InventoryMovement(CREDIT_DELIVERY)
  - SerializedUnit.status = DELIVERED_ON_CREDIT
  
  No se clasifica como SOLD hasta:
  - Todas las cuotas pagadas
  
  Al completar todas las cuotas:
  - SerializedUnit.status → SOLD
  - InventoryMovement(SALE_COMPLETED)
```

### 13.9 Reprogramación de cuotas

Solo OWNER puede reprogramar. Se registra:

| Campo | Descripción |
|---|---|
| `old_due_date` | Fecha original |
| `new_due_date` | Nueva fecha |
| `reason` | Motivo obligatorio |
| `authorized_by` | OWNER |
| `created_at` | Timestamp del cambio |

### 13.10 Reservas

Una reserva es el bloqueo del producto por el pago de la inicial antes de la entrega.

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | UUID | PK |
| `product_id` | UUID | FK → Product |
| `serialized_unit_id` | UUID | FK → SerializedUnit |
| `customer_id` | UUID | FK → Customer |
| `sale_id` | UUID | FK → Sale |
| `status` | ENUM | ACTIVE / EXPIRED / CANCELLED / CONVERTED_TO_SALE / CONVERTED_TO_CREDIT |
| `expires_at` | TIMESTAMPTZ | Vencimiento de la reserva |
| `initial_amount` | NUMERIC(14,2) | Monto de la inicial |

---

## 14. MÓDULO DE COTIZACIONES

### 14.1 Entidad Quote

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | UUID | PK |
| `code` | VARCHAR | COT-YYYY-XXXXX |
| `customer_id` | UUID | FK → Customer |
| `status` | ENUM | Ver estados |
| `subtotal` | NUMERIC(14,2) | |
| `discount_amount` | NUMERIC(14,2) | |
| `total` | NUMERIC(14,2) | |
| `currency` | VARCHAR(3) | |
| `exchange_rate` | NUMERIC(10,4) | |
| `valid_until` | DATE | Fecha de vencimiento |
| `notes` | TEXT | |
| `converted_to_sale_id` | UUID | FK → Sale (si se convierte) |
| `created_by` | UUID | FK → User |
| `created_at` | TIMESTAMPTZ | |
| `updated_at` | TIMESTAMPTZ | |

### 14.2 Estados de cotización

| Estado | Descripción |
|---|---|
| `DRAFT` | Borrador, no enviada |
| `SENT` | Enviada al cliente |
| `VIEWED` | El cliente la vio |
| `ACCEPTED` | El cliente aceptó |
| `REJECTED` | El cliente rechazó |
| `EXPIRED` | Venció sin respuesta |
| `CONVERTED` | Convertida en venta |

### 14.3 Reglas de negocio — Cotizaciones

- SALES y OWNER pueden crear cotizaciones
- Una cotización aceptada puede convertirse en venta sin reingresar productos
- La conversión es atómica: Quote.status = CONVERTED + Sale creada
- Los precios de la cotización se congelan al momento de la creación
- Si los precios cambian después, la cotización no se actualiza automáticamente
- Una cotización expirada no puede convertirse en venta sin reactivación

---

## 15. MÓDULO DE REPARACIONES

### 15.1 Código de reparación

Formato: `REP-YYYY-XXXXX` (ej: REP-2026-00025)
La búsqueda global debe encontrar una reparación por su código exacto.

### 15.2 Entidad RepairOrder

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | UUID | PK |
| `code` | VARCHAR | REP-YYYY-XXXXX (único) |
| `customer_id` | UUID | FK → Customer |
| `status` | ENUM | Ver estados |
| `received_at` | TIMESTAMPTZ | |
| `delivered_at` | TIMESTAMPTZ | |
| `technician_id` | UUID | FK → User |
| `authorized_limit` | NUMERIC(14,2) | Tope autorizado por cliente |
| `total_cost` | NUMERIC(14,2) | Costo final de la reparación |
| `notes` | TEXT | |
| `created_by` | UUID | FK → User |

### 15.3 Estados de reparación

| Estado | Descripción |
|---|---|
| `RECEIVED` | Recibido, pendiente de diagnóstico |
| `DIAGNOSING` | En diagnóstico técnico |
| `QUOTED` | Cotización enviada al cliente |
| `WAITING_CUSTOMER` | Esperando respuesta del cliente |
| `AUTHORIZED` | Cliente autorizó la reparación |
| `IN_REPAIR` | En proceso de reparación |
| `TESTING` | Probando después de la reparación |
| `READY` | Listo para entrega |
| `DELIVERED` | Entregado al cliente |
| `REJECTED` | Cliente rechazó cotización |
| `CANCELLED_BY_CUSTOMER` | Cancelado por el cliente |
| `NOT_REPAIRABLE` | No tiene reparación posible |
| `ABANDONED` | Abandonado (no recogido) |

### 15.4 Entidad RepairDevice

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | UUID | PK |
| `repair_id` | UUID | FK → RepairOrder |
| `type` | VARCHAR | laptop / computadora / impresora / otro |
| `brand` | VARCHAR | Marca |
| `model` | VARCHAR | Modelo |
| `serial_number` | VARCHAR | Número de serie |
| `imei` | VARCHAR | IMEI (si aplica) |
| `imei2` | VARCHAR | |
| `accessories` | TEXT | Accesorios entregados (lista) |
| `physical_condition` | TEXT | Condición física al recibir |
| `reported_problem` | TEXT | Problema reportado por el cliente |
| `observations` | TEXT | Observaciones del técnico al recibir |

### 15.5 Credenciales de acceso al equipo

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | UUID | PK |
| `repair_id` | UUID | FK → RepairOrder |
| `method` | ENUM | PASSWORD / PIN / PATTERN / WINDOWS_PASSWORD / BIOS_PASSWORD / OTHER |
| `value_encrypted` | TEXT | Valor cifrado con AES |
| `other_description` | VARCHAR | Si method = OTHER |
| `accessed_at` | TIMESTAMPTZ | Último acceso registrado |
| `accessed_by` | UUID | FK → User |

**Reglas de credenciales:**
- Nunca se muestran automáticamente
- Solo técnico asignado y OWNER pueden ver
- Cada visualización queda registrada en auditoría
- Se eliminan lógicamente al entregar el equipo (no se guardan después de DELIVERED)

### 15.6 Diagnóstico y cotización

**RepairDiagnosis:**
- El diagnóstico es parte del proceso, no tiene precio independiente
- Si el cliente acepta la reparación, el diagnóstico está incluido
- Si el cliente rechaza, no se cobra diagnóstico (salvo configuración especial de OWNER)

**RepairQuote:**
| Campo | Tipo | Descripción |
|---|---|---|
| `id` | UUID | PK |
| `repair_id` | UUID | FK → RepairOrder |
| `parts_cost` | NUMERIC(14,2) | Costo de repuestos |
| `labor_cost` | NUMERIC(14,2) | Costo de mano de obra |
| `total` | NUMERIC(14,2) | |
| `authorized_limit` | NUMERIC(14,2) | Tope propuesto por técnico |
| `status` | ENUM | PENDING / ACCEPTED / REJECTED |
| `sent_via_whatsapp` | BOOLEAN | |
| `customer_response_at` | TIMESTAMPTZ | |

### 15.7 Tope de reparación

```
Técnico propone: authorized_limit = S/300

Si costo actual <= S/300:
  → El técnico puede continuar

Si costo actual > S/300:
  → PAUSE (IN_REPAIR → WAITING_CUSTOMER)
  → Crear nueva solicitud de autorización
  → Notificar cliente por WhatsApp
  → Cliente debe aprobar nuevo límite
```

### 15.8 Repuestos usados en reparación

**RepairPartUsage:**
| Campo | Tipo | Descripción |
|---|---|---|
| `id` | UUID | PK |
| `repair_id` | UUID | FK → RepairOrder |
| `product_id` | UUID | FK → Product |
| `quantity` | NUMERIC(14,3) | |
| `unit_cost` | NUMERIC(14,2) | |
| `status` | ENUM | RESERVED / USED / RETURNED / DAMAGED |
| `reserved_at` | TIMESTAMPTZ | |
| `used_at` | TIMESTAMPTZ | |

**Reglas de repuestos:**
- El técnico no consume stock directamente. El flujo es:
  1. Técnico solicita repuesto → RESERVED (InventoryMovement: RESERVATION)
  2. Al usar en reparación → USED (InventoryMovement: REPAIR_USAGE)
  3. Si no se usa → RETURNED (InventoryMovement: REPAIR_RETURN)
- Los repuestos no utilizados regresan automáticamente al inventario al cancelar

### 15.9 Cancelación

```
Si cliente cancela (CANCELLED_BY_CUSTOMER):
  
  Si NO hay costos cobrables:
    → No se cobra diagnóstico
    → Repuestos reservados → RETURNED al inventario
  
  Si HAY repuestos usados:
    → Se registran y cobran según autorización original
    → Repuestos no utilizados → RETURNED al inventario
```

### 15.10 Garantía de reparación

Al pasar a estado `DELIVERED`:
- Se crea automáticamente un `RepairWarranty`
- Se genera una `Warranty` asociada al cliente y a la reparación
- Duración configurable (default: 30 días para reparaciones)

---

## 16. MÓDULO DE MANTENIMIENTOS

### 16.1 Tipos de mantenimiento

| Tipo | Descripción |
|---|---|
| `PREVENTIVE` | Mantenimiento preventivo programado |
| `CORRECTIVE` | Corrección de fallo |
| `CLEANING` | Limpieza interna/externa |
| `OPTIMIZATION` | Optimización de software/hardware |
| `PRINTER_MAINTENANCE` | Mantenimiento específico de impresora |
| `COMPUTER_MAINTENANCE` | Mantenimiento de computadora |
| `LAPTOP_MAINTENANCE` | Mantenimiento de laptop |

### 16.2 Entidad MaintenanceOrder

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | UUID | PK |
| `code` | VARCHAR | MNT-YYYY-XXXXX |
| `customer_id` | UUID | FK → Customer |
| `type` | ENUM | Tipos de mantenimiento |
| `status` | ENUM | PENDING / IN_PROGRESS / COMPLETED / CANCELLED |
| `device_type` | VARCHAR | Tipo de equipo |
| `device_brand` | VARCHAR | |
| `device_model` | VARCHAR | |
| `technician_id` | UUID | FK → User |
| `scheduled_at` | TIMESTAMPTZ | Fecha programada |
| `completed_at` | TIMESTAMPTZ | |
| `cost` | NUMERIC(14,2) | |
| `description` | TEXT | Trabajo realizado |
| `notes` | TEXT | |
| `created_by` | UUID | FK → User |

### 16.3 Consumo de inventario en mantenimientos

- Los mantenimientos pueden consumir productos del inventario (ej: pasta térmica, limpiadores)
- El mismo flujo de solicitud → aprobación → consumo que en reparaciones
- Todo consumo genera InventoryMovement(REPAIR_USAGE)

---

## 17. MÓDULO DE INSTALACIONES

### 17.1 Entidad InstallationOrder

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | UUID | PK |
| `code` | VARCHAR | INST-YYYY-XXXXX |
| `customer_id` | UUID | FK → Customer |
| `type` | VARCHAR | CCTV / RED / OTRO |
| `status` | ENUM | Ver estados |
| `address` | TEXT | Dirección de instalación |
| `coordinates_lat` | DECIMAL | Latitud (opcional) |
| `coordinates_lng` | DECIMAL | Longitud (opcional) |
| `technician_id` | UUID | FK → User |
| `total_cost` | NUMERIC(14,2) | |
| `notes` | TEXT | |
| `created_by` | UUID | FK → User |

### 17.2 Estados de instalación

| Estado | Descripción |
|---|---|
| `QUOTED` | Cotización enviada |
| `ACCEPTED` | Cliente aceptó |
| `SCHEDULED` | Programada con fecha y hora |
| `IN_PROGRESS` | En ejecución |
| `WAITING_MATERIAL` | Esperando materiales adicionales |
| `COMPLETED` | Instalación completada |
| `CANCELLED` | Cancelada |

### 17.3 Datos específicos para cámaras (CCTV)

| Campo | Descripción |
|---|---|
| `camera_count` | Cantidad de cámaras |
| `camera_type` | Tipo (analógica, IP, PTZ, etc.) |
| `dvr_nvr` | Modelo del DVR/NVR |
| `storage_capacity` | Capacidad del disco |
| `cable_type` | Tipo de cableado |
| `materials_detail` | Detalle de materiales |

### 17.4 Material adicional en instalaciones

```
Técnico solicita material adicional durante la instalación:

1. Técnico registra solicitud de material
2. AVISO automático al cliente (WhatsApp)
3. AVISO automático al OWNER (notificación interna)
4. OWNER aprueba la solicitud
5. Material se despacha del inventario
6. InventoryMovement registrado
7. Técnico confirma recepción y uso

El técnico NO puede tomar material sin aprobación.
```

### 17.5 Finalización de instalación

Para marcar como COMPLETED se requiere obligatoriamente:

- [ ] Descripción del trabajo realizado
- [ ] Lista de materiales utilizados
- [ ] Mínimo 1 fotografía de evidencia
- [ ] Observaciones finales
- [ ] Documento firmado/escaneado (almacenado en S3)

### 17.6 Entidades de instalación

- **InstallationItem:** producto_id, quantity (equipos instalados)
- **InstallationMaterial:** product_id, quantity, status (REQUESTED/APPROVED/CONSUMED)
- **InstallationSchedule:** technician_id, scheduled_date, scheduled_time, confirmed
- **InstallationEvidence:** file_id, description, type (BEFORE/DURING/AFTER)

---

## 18. MÓDULO DE GARANTÍAS

### 18.1 Entidad Warranty

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | UUID | PK |
| `code` | VARCHAR | GAR-YYYYMMDD-XXXXX |
| `customer_id` | UUID | FK → Customer |
| `source_type` | ENUM | PRODUCT / REPAIR / INSTALLATION |
| `source_id` | UUID | ID del origen (venta, reparación, instalación) |
| `product_id` | UUID | FK → Product (si aplica) |
| `start_date` | DATE | |
| `end_date` | DATE | |
| `duration_days` | INTEGER | Duración en días |
| `status` | ENUM | ACTIVE / EXPIRED / CLAIMED / VOID |
| `notes` | TEXT | |
| `created_at` | TIMESTAMPTZ | |

### 18.2 Aplicación de garantías

| Origen | Cuándo se crea | Duración default |
|---|---|---|
| Venta de producto | Al completar la venta (PAID/COMPLETED) | Configurable por producto |
| Reparación | Al pasar a DELIVERED | 30 días (configurable) |
| Instalación | Al marcar COMPLETED | 90 días (configurable) |

### 18.3 Búsqueda de garantías

El cliente puede buscar su garantía por:
- Código de garantía (`GAR-...`)
- Número de documento (DNI/RUC)
- Nombre del cliente
- Número de serie del producto
- Código de reparación

### 18.4 Alertas de garantía

Tarea Celery (diaria):
- Garantías que vencen en 7 días → notificación al OWNER
- Garantías que vencen en 30 días → notificación al OWNER
- WhatsApp al cliente cuando queden 7 días

---

## 19. MÓDULO DE DELIVERY Y ENVÍOS

### 19.1 Delivery local

**DeliveryOrder:**

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | UUID | PK |
| `code` | VARCHAR | DEL-YYYY-XXXXX |
| `reference_type` | VARCHAR | sale / repair / other |
| `reference_id` | UUID | |
| `customer_id` | UUID | FK → Customer |
| `status` | ENUM | Ver estados |
| `delivery_address` | TEXT | |
| `delivery_zone` | VARCHAR | Zona de entrega |
| `cost` | NUMERIC(14,2) | Costo de delivery |
| `cost_type` | ENUM | FIXED / ZONE / DISTANCE / COURIER |
| `carrier_name` | VARCHAR | Repartidor o empresa |
| `scheduled_at` | TIMESTAMPTZ | Fecha programada |
| `delivered_at` | TIMESTAMPTZ | |
| `notes` | TEXT | |

**Estados de delivery:**

| Estado | Descripción |
|---|---|
| `PENDING` | Pendiente de confirmación |
| `CONFIRMED` | Confirmado |
| `PREPARING` | Preparando el paquete |
| `READY` | Listo para salir |
| `IN_DELIVERY` | En camino |
| `DELIVERED` | Entregado |
| `CANCELLED` | Cancelado |

### 19.2 Envíos por courier (reparaciones remotas)

**Shipment:**

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | UUID | PK |
| `code` | VARCHAR | ENV-YYYY-XXXXX |
| `repair_id` | UUID | FK → RepairOrder (si aplica) |
| `customer_id` | UUID | FK → Customer |
| `direction` | ENUM | TO_HASBUN / FROM_HASBUN |
| `carrier` | VARCHAR | Empresa de courier |
| `tracking_number` | VARCHAR | Número de seguimiento |
| `origin_address` | TEXT | |
| `destination_address` | TEXT | |
| `cost` | NUMERIC(14,2) | |
| `status` | ENUM | Ver estados |
| `sent_at` | TIMESTAMPTZ | |
| `received_at` | TIMESTAMPTZ | |
| `evidence_file_id` | UUID | FK → FileObject |

**Estados de envío:**

| Estado | Descripción |
|---|---|
| `PENDING` | Pendiente de despacho |
| `SHIPPED` | Despachado |
| `IN_TRANSIT` | En tránsito |
| `RECEIVED` | Recibido en destino |
| `RETURN_SHIPPED` | En retorno |
| `DELIVERED` | Entregado al destinatario final |
| `LOST` | Extraviado |
| `CANCELLED` | Cancelado |

---

## 20. MÓDULO DE SUBLIMACIÓN Y PERSONALIZACIÓN

### 20.1 Entidad CustomizationOrder

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | UUID | PK |
| `code` | VARCHAR | SUB-YYYY-XXXXX |
| `customer_id` | UUID | FK → Customer |
| `status` | ENUM | Ver estados |
| `total` | NUMERIC(14,2) | |
| `notes` | TEXT | |
| `created_by` | UUID | FK → User |
| `created_at` | TIMESTAMPTZ | |

**Estados:**
`DRAFT` → `QUOTED` → `ACCEPTED` → `IN_PRODUCTION` → `READY` → `DELIVERED` → `CANCELLED`

### 20.2 Flujo de personalización

```
1. Cliente sube diseño (DesignFile → S3)
2. Cliente elige producto (taza, polo, etc.)
3. Solicita personalización
4. Sistema genera cotización
5. Cliente acepta/rechaza
6. Si acepta: producción → entrega
```

### 20.3 Entidades de sublimación

- **CustomizationItem:** order_id, product_id, quantity, customization_notes
- **DesignFile:** order_id, file_id, version, is_approved
- **ProductionStatus:** order_id, stage, updated_by, timestamp, notes

### 20.4 Consideraciones

- Inicialmente no se implementa editor gráfico complejo
- La arquitectura debe soportar integrarlo posteriormente
- Los archivos de diseño se almacenan en S3 con checksum para verificación
- Cada versión de diseño se registra (historial)

---

## 21. MÓDULO DE DESARROLLO DE SOFTWARE

### 21.1 Entidad SoftwareProject

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | UUID | PK |
| `name` | VARCHAR | Nombre del proyecto |
| `slug` | VARCHAR | URL amigable |
| `description` | TEXT | Descripción completa |
| `short_description` | TEXT | Descripción corta para tarjetas |
| `status` | ENUM | DRAFT / PUBLISHED / ARCHIVED |
| `client_name` | VARCHAR | Nombre del cliente (puede ser anónimo) |
| `project_url` | VARCHAR | URL del proyecto (si es público) |
| `year_completed` | INTEGER | Año de finalización |
| `featured` | BOOLEAN | Destacado en portada |
| `created_by` | UUID | FK → User |
| `published_at` | TIMESTAMPTZ | |
| `created_at` | TIMESTAMPTZ | |

### 21.2 Entidades relacionadas

- **ProjectImage:** project_id, file_id, order, caption
- **ProjectTechnology:** project_id, tech_name, tech_category (frontend/backend/db/etc.)
- **ClientSuccessStory:** project_id, client_name, testimonial, client_avatar_file_id, published

### 21.3 Reglas de negocio

- Solo `SOFTWARE_DEVELOPER` y `OWNER` pueden crear/editar proyectos
- Solo `SOFTWARE_DEVELOPER` y `OWNER` pueden publicar (cambiar a PUBLISHED)
- Los proyectos PUBLISHED son visibles en la web pública
- Los proyectos DRAFT no son visibles públicamente

---

## 22. MÓDULO DE CLIENTES (CRM)

### 22.1 Entidad Customer

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | UUID | PK |
| `user_id` | UUID | FK → User (si tiene cuenta) |
| `type` | ENUM | PERSON / COMPANY |
| `first_name` | VARCHAR | |
| `last_name` | VARCHAR | |
| `razon_social` | VARCHAR | Si type = COMPANY |
| `dni` | VARCHAR | DNI (único si se ingresa) |
| `ruc` | VARCHAR | RUC (único si se ingresa) |
| `phone` | VARCHAR | Teléfono principal |
| `phone_whatsapp` | VARCHAR | Número WhatsApp (puede ser diferente) |
| `email` | VARCHAR | |
| `address` | TEXT | Dirección principal |
| `district` | VARCHAR | Distrito |
| `city` | VARCHAR | Ciudad |
| `credit_limit` | NUMERIC(14,2) | Límite de crédito asignado |
| `is_blocked` | BOOLEAN | Bloqueado para crédito |
| `block_reason` | TEXT | Motivo del bloqueo |
| `is_frequent` | BOOLEAN | Cliente frecuente (beneficios especiales) |
| `notes` | TEXT | Notas internas |
| `active` | BOOLEAN | |
| `created_at` | TIMESTAMPTZ | |
| `updated_at` | TIMESTAMPTZ | |

### 22.2 Vista centralizada del cliente

Desde el perfil de un cliente, el sistema debe mostrar:

- Datos personales
- Historial de compras (Sale[])
- Créditos activos y cerrados (CreditAgreement[])
- Cuotas pendientes (CreditInstallment[])
- Pagos realizados (CreditPayment[])
- Reparaciones (RepairOrder[])
- Mantenimientos (MaintenanceOrder[])
- Instalaciones (InstallationOrder[])
- Cotizaciones (Quote[])
- Garantías activas y vencidas (Warranty[])
- Pedidos y delivery (DeliveryOrder[])
- Envíos (Shipment[])

### 22.3 Carrito de compras

```
CartItem:
  - customer_id (o session_id para anónimos)
  - product_id
  - quantity
  - added_at

Flujo tienda online:
  PRODUCTO → CARRITO → RESUMEN → COMPRAR POR WHATSAPP

No hay pago online todavía.
La arquitectura debe permitir agregar pasarelas en el futuro:
  - Culqi
  - Izipay
  - Yape/Plin API
  - Otros
```

---

## 23. MÓDULO DE WHATSAPP

### 23.1 Arquitectura del proveedor

```
WhatsAppProvider (interfaz)
  ├── MockWhatsAppProvider        (desarrollo y testing)
  └── ExternalWhatsAppProvider    (producción: Twilio, Meta API, etc.)
```

La aplicación nunca depende directamente de un proveedor externo. Se programa contra la interfaz.

### 23.2 Entidades de WhatsApp

**WhatsAppTemplate:**

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | UUID | PK |
| `name` | VARCHAR | Identificador interno |
| `event_type` | ENUM | Ver eventos |
| `body` | TEXT | Plantilla con variables `{variable}` |
| `variables` | JSONB | Listado de variables esperadas |
| `active` | BOOLEAN | |

**WhatsAppMessage:**

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | UUID | PK |
| `recipient` | VARCHAR | Número destino |
| `template_id` | UUID | FK → WhatsAppTemplate |
| `payload` | JSONB | Variables reemplazadas |
| `status` | ENUM | PENDING / SENT / DELIVERED / FAILED |
| `idempotency_key` | VARCHAR | Prevenir duplicados |
| `provider_message_id` | VARCHAR | ID del proveedor |
| `sent_at` | TIMESTAMPTZ | |
| `error` | TEXT | Detalle del error si falló |

**WhatsAppDeliveryLog:** registro de cada intento de envío con estado y timestamp.

### 23.3 Eventos que disparan WhatsApp

| Evento | Destinatario | Descripción |
|---|---|---|
| `NEW_SALE` | Cliente | Confirmación de compra |
| `PAYMENT_RECEIVED` | Cliente | Pago recibido |
| `INSTALLMENT_UPCOMING` | Cliente | Cuota próxima a vencer (3 días antes) |
| `INSTALLMENT_OVERDUE` | Cliente | Cuota vencida |
| `MORA_CREATED` | Cliente + OWNER | Mora generada |
| `REPAIR_CREATED` | Cliente | Orden de reparación recibida |
| `REPAIR_READY` | Cliente | Equipo listo para recoger |
| `QUOTE_CREATED` | Cliente | Cotización enviada |
| `QUOTE_ACCEPTED` | OWNER + SALES | Cliente aceptó cotización |
| `INSTALLATION_CREATED` | Cliente | Instalación programada |
| `INSTALLATION_UPCOMING` | Cliente | Recordatorio 1 día antes |
| `STOCK_LOW` | OWNER | Producto con stock bajo |
| `STOCK_OUT` | OWNER | Producto agotado |
| `WARRANTY_EXPIRING` | Cliente + OWNER | Garantía próxima a vencer |
| `SALE_COMPLETED` | Cliente | Crédito completamente pagado |

### 23.4 Reglas de WhatsApp

- Los envíos son asíncronos (via Celery)
- Si el proveedor falla: reintentar con backoff exponencial (1min, 5min, 15min)
- Máximo 3 intentos antes de marcar como FAILED
- Los mensajes FAILED generan notificación interna para el OWNER
- La idempotency_key previene el reenvío accidental del mismo mensaje
- Nunca exponer tokens del proveedor en el frontend

---

## 24. MÓDULO DE NOTIFICACIONES

### 24.1 Entidad Notification

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | UUID | PK |
| `user_id` | UUID | FK → User destinatario |
| `type` | VARCHAR | Tipo de notificación |
| `title` | VARCHAR | Título corto |
| `message` | TEXT | Mensaje completo |
| `read` | BOOLEAN | Leída o no |
| `priority` | ENUM | LOW / MEDIUM / HIGH / URGENT |
| `related_type` | VARCHAR | sale / repair / credit / etc. |
| `related_id` | UUID | ID del elemento relacionado |
| `created_at` | TIMESTAMPTZ | |

### 24.2 Distribución por rol

| Notificación | OWNER | SALES | TECHNICIAN |
|---|---|---|---|
| Venta nueva | ✅ | ✅ (propia) | ❌ |
| Cuota vencida | ✅ | ✅ | ❌ |
| Solicitud de descuento | ✅ | ❌ | ❌ |
| Cierre de caja pendiente | ✅ | ❌ | ❌ |
| Reparación lista | ✅ | ✅ | ✅ (asignada) |
| Stock bajo | ✅ | ❌ | ❌ |
| Instalación programada | ✅ | ❌ | ✅ (asignada) |
| Material solicitado | ✅ | ❌ | ✅ (propia) |
| Nuevo crédito solicitado | ✅ | ❌ | ❌ |

---

## 25. MÓDULO DE REPORTES

### 25.1 Reportes disponibles

| Reporte | Descripción | Filtros |
|---|---|---|
| Ventas | Todas las ventas en un período | Fecha, tipo, estado, vendedor |
| Caja | Movimientos de caja | Caja, sesión, fecha, tipo |
| Inventario | Stock actual por producto | Categoría, marca, estado |
| Kardex | Historial de movimientos de un producto | Producto, fecha, tipo |
| Compras | Órdenes de compra | Proveedor, estado, fecha |
| Proveedores | Resumen por proveedor | |
| Créditos | Créditos activos, pagados, morosos | Estado, cliente, fecha |
| Morosidad | Cuotas vencidas y mora | Cliente, período |
| Reparaciones | Órdenes de reparación | Estado, técnico, fecha |
| Instalaciones | Órdenes de instalación | Estado, técnico, fecha |
| Garantías | Garantías activas y próximas a vencer | Estado, tipo, fecha |
| Clientes | Reporte de clientes | Activo, moroso, frecuente |
| Ganancias | Ventas - Costos estimados | Período |

### 25.2 Formatos de exportación

- **PDF:** para reportes formales (usando plantilla HTML → PDF)
- **Excel/CSV:** para análisis en hojas de cálculo

### 25.3 Acceso a reportes

- OWNER: acceso a todos los reportes
- SALES: solo reporte de sus propias ventas y cotizaciones
- TECHNICIAN: solo reporte de sus reparaciones e instalaciones
- CUSTOMER: no accede a reportes del sistema

---

## 26. MÓDULO DE AUDITORÍA

### 26.1 Entidad AuditLog

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | UUID | PK |
| `user_id` | UUID | FK → User (quien ejecutó) |
| `action` | VARCHAR | Código de la acción (ej: MODIFY_PRICE) |
| `module` | VARCHAR | Módulo donde ocurrió |
| `entity_type` | VARCHAR | Tipo de entidad afectada |
| `entity_id` | UUID | ID de la entidad afectada |
| `old_values` | JSONB | Estado anterior (completo) |
| `new_values` | JSONB | Estado nuevo (completo) |
| `authorization_id` | UUID | FK a la autorización si aplica |
| `ip_address` | VARCHAR | IP del cliente |
| `user_agent` | TEXT | User-Agent del navegador |
| `request_id` | UUID | ID único del request HTTP |
| `timestamp` | TIMESTAMPTZ | |

### 26.2 Acciones auditadas obligatoriamente

| Acción | Módulo | Datos guardados |
|---|---|---|
| `CREATE_SALE` | Ventas | Todos los ítems y pagos |
| `CANCEL_SALE` | Ventas | Razón y autorización |
| `MODIFY_PRICE` | Productos | Precio anterior y nuevo |
| `APPLY_DISCOUNT` | Ventas | Porcentaje, monto, aprobador |
| `CREATE_CREDIT` | Créditos | Términos completos del crédito |
| `APPROVE_CREDIT` | Créditos | Quién aprobó |
| `REJECT_CREDIT` | Créditos | Motivo del rechazo |
| `APPLY_MORA` | Créditos | Cuota, tasa, monto |
| `RESTRUCTURE_CREDIT` | Créditos | Fechas anteriores y nuevas |
| `CLOSE_CASH_SESSION` | Caja | Montos esperados y contados |
| `APPROVE_CLOSURE` | Caja | Diferencia y motivo |
| `TRANSFER_CASH` | Caja | Origen, destino, monto |
| `ADJUST_INVENTORY` | Inventario | Antes y después |
| `CHANGE_PERMISSION` | Usuarios | Permiso, usuario, concedido/revocado |
| `DELIVER_REPAIR` | Reparaciones | Estado final y cobro |
| `ACCESS_CREDENTIALS` | Reparaciones | Quién accedió y cuándo |
| `CREATE_RETURN` | Ventas | Motivo y productos |

### 26.3 Reglas de auditoría

- Los registros de auditoría son **inmutables**. No se pueden modificar ni eliminar.
- Solo OWNER puede ver el módulo de auditoría
- La auditoría implementa tres capas:
  1. Middleware HTTP: captura request_id, IP, user_agent
  2. Servicio de aplicación: `audit_service.log(...)` explícito en operaciones críticas
  3. Triggers PostgreSQL: en tablas extremadamente sensibles como `cash_sessions` y `credit_agreements`
- Nunca se registran: contraseñas, tokens, claves de cifrado

---

## 27. MÓDULO DE DASHBOARD

### 27.1 Dashboard OWNER

| Sección | Información mostrada |
|---|---|
| Resumen del día | Ventas del día, ingresos en caja, ganancia estimada |
| Créditos | Activos, vencidos, por cobrar esta semana |
| Morosidad | Clientes morosos, monto total en mora |
| Inventario | Productos con stock bajo, productos agotados |
| Reparaciones | Recibidas hoy, listas para entregar, en proceso |
| Instalaciones | Programadas hoy, pendientes |
| Cotizaciones | Enviadas, aceptadas, por vencer |
| Garantías | Por vencer en 7 días, reclamadas |
| Alertas | Todas las alertas activas (stock, mora, caja, etc.) |

### 27.2 Dashboard SALES

| Sección | Información mostrada |
|---|---|
| Ventas del día | Monto y cantidad |
| Cotizaciones | Pendientes y aceptadas |
| Pedidos | Pendientes de entrega |
| Clientes | Atendidos hoy |
| Caja | Estado de su caja actual |
| Pagos pendientes | Cuotas a cobrar hoy |
| Autorizaciones | Descuentos y créditos esperando aprobación |

### 27.3 Dashboard TECHNICIAN

| Sección | Información mostrada |
|---|---|
| Reparaciones | Asignadas, en proceso, listas |
| Tareas del día | Lista de tareas pendientes |
| Mantenimientos | Programados hoy |
| Instalaciones | Programadas hoy |
| Equipos pendientes | Recibidos sin diagnóstico |
| Equipos listos | Listos para entregar |
| Materiales | Solicitudes aprobadas pendientes de uso |

### 27.4 Dashboard SOFTWARE_DEVELOPER

| Sección | Información mostrada |
|---|---|
| Proyectos | Publicados, en borrador |
| Publicaciones | Recientes y pendientes de revisión |
| Clientes satisfechos | Testimonios publicados |

### 27.5 Calendario general

El calendario muestra en una sola vista:
- Instalaciones programadas
- Mantenimientos programados
- Reparaciones (fecha estimada de entrega)
- Entregas de delivery
- Vencimientos de cuotas
- Tareas del equipo

Filtros: por usuario (técnico), por tipo de evento, por semana/mes.

---

## 28. MÓDULO DE ARCHIVOS

### 28.1 Entidad FileObject

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | UUID | PK |
| `storage_key` | VARCHAR | Ruta en S3/MinIO |
| `bucket` | VARCHAR | Nombre del bucket |
| `original_name` | VARCHAR | Nombre original del archivo |
| `mime_type` | VARCHAR | Tipo MIME verificado |
| `size` | BIGINT | Tamaño en bytes |
| `checksum` | VARCHAR | SHA-256 del archivo |
| `metadata` | JSONB | Metadatos adicionales |
| `uploaded_by` | UUID | FK → User |
| `created_at` | TIMESTAMPTZ | |

### 28.2 Reglas de archivos

- La extensión del archivo no es suficiente: se valida el MIME type real
- Tamaño máximo configurable (default: 10MB por archivo)
- Imágenes se comprimen en el cliente antes de subir (si > 2MB)
- Tipos permitidos: `image/jpeg`, `image/png`, `image/webp`, `application/pdf`, `text/plain`
- Los archivos se almacenan con nombres UUID en S3 (nunca con nombre original)
- El checksum SHA-256 se calcula antes de almacenar para verificación de integridad
- Los archivos se referencian desde otras entidades via `file_id`

---

## 29. MÓDULO DE CONFIGURACIÓN

### 29.1 Configuraciones del sistema

| Clave | Descripción | Default |
|---|---|---|
| `mora_rate` | Tasa mensual de mora | 0.0300 (3%) |
| `credit_initial_required` | Exige inicial en créditos | true |
| `credit_min_initial_percent` | Mínimo % de inicial | 0.20 (20%) |
| `repair_warranty_days` | Días de garantía por reparación | 30 |
| `installation_warranty_days` | Días de garantía por instalación | 90 |
| `interest_free_months_default` | Meses de gracia por default | 0 |
| `max_cash_difference_auto_close` | Diferencia máxima para auto-cierre | 0.00 |
| `stock_low_threshold` | % stock mínimo para alerta | 0.20 |
| `whatsapp_enabled` | WhatsApp activo | true |
| `currency_display_default` | Moneda de visualización default | PEN |
| `exchange_rate_update_hour` | Hora de actualización diaria de TC | 08:00 |

Solo OWNER puede modificar la configuración del sistema. Todo cambio queda auditado.

---

## 30. WEB PÚBLICA Y TIENDA

### 30.1 Páginas de la web pública

| Ruta | Descripción |
|---|---|
| `/` | Página de inicio con presentación del negocio |
| `/tienda` | Catálogo de productos publicados |
| `/tienda/{slug}` | Detalle de producto |
| `/proyectos` | Portafolio de proyectos de software |
| `/proyectos/{slug}` | Detalle de proyecto |
| `/servicios` | Descripción de todos los servicios |
| `/contacto` | Formulario de contacto y datos del negocio |

### 30.2 Tienda online

- Solo muestra productos con `published = true` y `active = true`
- Precio de oferta se muestra cuando hay `ProductOffer` vigente
- Filtros: categoría, marca, precio, disponibilidad
- Ordenamiento: precio, nombre, reciente
- Paginación server-side
- El carrito persiste en sesión (no requiere cuenta)
- Al finalizar compra: **redirige a WhatsApp** con detalle del pedido

### 30.3 Búsqueda global

La búsqueda global del panel admin debe encontrar en tiempo real:

| Entidad | Campos buscados |
|---|---|
| Clientes | Nombre, DNI, RUC, teléfono, email |
| Productos | Nombre, SKU, código de barras |
| Ventas | Código (VTA-...) |
| Reparaciones | Código (REP-...), nombre del cliente |
| Cotizaciones | Código (COT-...), nombre del cliente |
| Créditos | Código (CRD-...), nombre del cliente |
| Garantías | Código (GAR-...) |
| Instalaciones | Código (INST-...) |

---

## 31. PORTAL DEL CLIENTE

### 31.1 Acceso

El cliente puede registrarse y tener cuenta propia. Al iniciar sesión, puede ver:

- Su perfil y datos de contacto
- Sus órdenes de compra
- Sus cuotas pendientes y pagadas
- Sus reparaciones (estado en tiempo real)
- Sus cotizaciones
- Sus garantías vigentes
- Sus pedidos y delivery

### 31.2 Consulta de reparación sin cuenta

- El cliente puede consultar el estado de su reparación ingresando:
  - Código de reparación (REP-YYYY-XXXXX)
  - DNI o teléfono de verificación

---

## 32. SEGURIDAD

### 32.1 Autenticación

| Mecanismo | Descripción |
|---|---|
| Cookies HttpOnly Secure | Tokens de sesión. No accesibles desde JavaScript |
| SameSite=Lax o Strict | Protección contra CSRF |
| CSRF token | Token adicional en formularios críticos |
| Rate limiting | Máximo intentos de login por IP y por usuario |
| Password hashing | bcrypt con salt. Nunca texto plano |
| Session expiration | Sesiones con tiempo de vida configurable |

### 32.2 Autorización

| Mecanismo | Descripción |
|---|---|
| RBAC | Roles base con permisos predefinidos |
| Permission overrides | Permisos individuales por usuario |
| Backend enforcement | Todo permiso validado en backend. Frontend solo filtra UI |
| Principle of least privilege | Cada rol tiene solo los permisos que necesita |

### 32.3 Datos sensibles

| Dato | Tratamiento |
|---|---|
| Contraseñas de usuarios | bcrypt. Nunca se almacenan en texto plano |
| Credenciales de equipos | AES-256 cifrado. Acceso auditado |
| Tokens de API (WhatsApp) | Solo en variables de entorno. Nunca en código |
| Secretos de base de datos | Solo en `.env`. Nunca en repositorio |
| Datos financieros | Solo en backend. Nunca en localStorage |

### 32.4 Comunicación

- HTTPS obligatorio en producción
- HTTP redirige automáticamente a HTTPS
- Headers de seguridad: `X-Frame-Options`, `X-Content-Type-Options`, `Strict-Transport-Security`
- CORS configurado para orígenes específicos

### 32.5 Logs y observabilidad

- Logs estructurados (JSON) con campos: `request_id`, `user_id`, `module`, `action`, `duration`
- Nunca se registran en logs: passwords, tokens, credenciales de equipos, datos financieros completos
- Endpoints de health: `GET /health` (liveness), `GET /ready` (readiness)

### 32.6 Preparación para SUNAT (futuro)

- Crear interfaz `InvoiceProvider` y `ElectronicDocumentProvider`
- Las ventas no dependen directamente de SUNAT
- El módulo de facturación se conectará posteriormente sin modificar el core de ventas

---

## 33. API REST

### 33.1 Versionado

Toda la API usa el prefijo `/api/v1/`.

### 33.2 Endpoints principales

```
/api/v1/auth
/api/v1/users
/api/v1/roles
/api/v1/permissions
/api/v1/customers
/api/v1/products
/api/v1/categories
/api/v1/brands
/api/v1/attributes
/api/v1/inventory
/api/v1/purchases
/api/v1/suppliers
/api/v1/sales
/api/v1/pos
/api/v1/cash
/api/v1/credits
/api/v1/installments
/api/v1/quotes
/api/v1/repairs
/api/v1/maintenance
/api/v1/installations
/api/v1/warranties
/api/v1/deliveries
/api/v1/shipments
/api/v1/sublimation
/api/v1/software-projects
/api/v1/notifications
/api/v1/whatsapp
/api/v1/exchange-rates
/api/v1/reports
/api/v1/audit
/api/v1/dashboard
/api/v1/files
/api/v1/settings
/api/v1/search
/api/v1/health
/api/v1/ready
```

### 33.3 Formato de respuesta de error

```json
{
  "error": {
    "code": "INSUFFICIENT_STOCK",
    "message": "No hay suficiente stock disponible para el producto solicitado",
    "details": {
      "product_id": "uuid-del-producto",
      "requested": 3,
      "available": 1
    },
    "request_id": "req-uuid-aqui"
  }
}
```

**Reglas:**
- Nunca devolver stack traces al cliente en producción
- Siempre incluir `request_id` para trazabilidad
- Los errores de validación incluyen el campo específico que falló
- Los errores de autorización son genéricos (no revelan si existe o no el recurso)

### 33.4 Idempotency

Las operaciones críticas aceptan el header `Idempotency-Key`:
- `POST /api/v1/sales`
- `POST /api/v1/sales/{id}/payments`
- `POST /api/v1/credits/{id}/payments`
- `POST /api/v1/cash/movements`

Si la misma `Idempotency-Key` se recibe dos veces, se retorna el resultado de la primera operación sin ejecutar de nuevo.

---

## 34. TRANSACCIONES Y CONSISTENCIA

### 34.1 Patrón de transacción

```python
async with db.begin() as transaction:
    try:
        # operación 1
        # operación 2
        # ...
        await audit_service.log(...)
        await transaction.commit()
    except Exception:
        await transaction.rollback()
        raise
```

### 34.2 Operaciones atómicas obligatorias

| Operación | Tablas involucradas en la misma transacción |
|---|---|
| Venta al contado | Sale + SaleItem + SalePayment + CashMovement + InventoryMovement + AuditLog |
| Venta a crédito | Sale + SaleItem + CreditAgreement + CreditInstallment[] + CashMovement(inicial) + InventoryMovement + AuditLog |
| Pago de cuota | CreditPayment + CreditInstallment(update) + CashMovement + AuditLog |
| Cierre de caja aprobado | CashSession(update) + CashClosureRequest(update) + AuditLog |
| Transferencia de caja | CashMovement(OUT) + CashMovement(IN) + CashTransfer + AuditLog |
| Recepción de compra | Purchase(update) + InventoryMovement[] + AuditLog |
| Cancelación de reparación | RepairOrder(update) + InventoryMovement(REPAIR_RETURN)[] + AuditLog |
| Devolución de venta | Return + ReturnItem + InventoryMovement + CashAdjustment + Sale(update) + AuditLog |

### 34.3 Control de concurrencia

| Recurso protegido | Mecanismo |
|---|---|
| Stock de producto | `SELECT ... FOR UPDATE` en InventoryMovement |
| Unidad serializada | `SELECT ... FOR UPDATE` en SerializedUnit |
| Sesión de caja activa | Unique constraint (user + status=OPEN) |
| Generación de SKU | Lock en tabla de secuencias |
| Números de documento | Unique constraint + secuencia con lock |
| Pagos duplicados | Unique constraint en idempotency_key |

### 34.4 Tipos de datos financieros

| Dato | Tipo en PostgreSQL | Tipo en Python |
|---|---|---|
| Montos de dinero | `NUMERIC(14,2)` | `Decimal` |
| Tasas e intereses | `NUMERIC(5,4)` | `Decimal` |
| Cantidades de stock | `NUMERIC(14,3)` | `Decimal` |
| Porcentajes de descuento | `NUMERIC(5,4)` | `Decimal` |

**NUNCA** usar `float` o `FLOAT` para dinero.

---

## 35. ESTRATEGIA DE TESTING

### 35.1 Pirámide de tests

```
              ┌─────┐
              │ E2E │  20 flujos críticos (Playwright)
             ┌┴─────┴┐
             │ Integr │  pytest + httpx + DB real en Docker
            ┌┴────────┴┐
            │ Unitarios │  pytest — dominio y servicios aislados
           └────────────┘
```

### 35.2 Casos de prueba obligatorios

Los siguientes casos deben tener tests automatizados. Un módulo no se considera terminado sin ellos.

#### Tests financieros

| # | Caso | Validación esperada |
|---|---|---|
| 1 | Venta al contado completa | Sale=PAID, CashMovement creado, InventoryMovement creado |
| 2 | Venta con descuento no autorizado | Error 403, venta no creada |
| 3 | Venta a crédito con inicial | CreditAgreement creado, cuotas generadas correctamente |
| 4 | Venta a crédito sin inicial a cliente normal | Error, inicial requerida |
| 5 | Pago parcial de cuota | installment.status=PARTIALLY_PAID, paid_amount correcto |
| 6 | Pago adelantado de múltiples cuotas | Cada cuota afectada registrada individualmente |
| 7 | Mora en cuota vencida | CreditMora creado, monto = 3% de saldo vencido |
| 8 | Mora no se aplica dos veces al mismo período | Idempotencia verificada |
| 9 | Doble cobro (mismo idempotency_key) | Segundo request retorna resultado del primero sin duplicar |
| 10 | Cierre de caja sin diferencia | Cierre inmediato permitido |
| 11 | Cierre de caja con diferencia | CashClosureRequest creado, cierre bloqueado |
| 12 | Transferencia entre cajas | CashMovement(OUT) + CashMovement(IN) en misma transacción |
| 13 | Transferencia falla a mitad | ROLLBACK total, ninguna caja afectada |

#### Tests de inventario

| # | Caso | Validación esperada |
|---|---|---|
| 14 | Venta reduce stock correctamente | InventoryMovement creado, stock calculado correcto |
| 15 | Venta con stock insuficiente | Error 400, venta no creada |
| 16 | Stock no puede ser negativo | Constraint en BD activo |
| 17 | Doble venta del mismo serial | Segundo intento bloqueado por unique constraint |
| 18 | Concurrencia: 2 requests al mismo serial simultáneo | Solo 1 venta exitosa, la otra error |
| 19 | Ajuste de inventario sin autorización | Error 403 |
| 20 | Devolución restaura stock | InventoryMovement(RETURN) creado, stock aumenta |

#### Tests de permisos

| # | Caso | Respuesta esperada |
|---|---|---|
| 21 | SALES intenta modificar costo de producto | 403 Forbidden |
| 22 | SALES intenta ver caja ajena | 403 Forbidden |
| 23 | TECHNICIAN intenta aprobar crédito | 403 Forbidden |
| 24 | TECHNICIAN intenta ver costo de producto | 403 Forbidden |
| 25 | CUSTOMER intenta acceder al panel admin | 403 Forbidden |
| 26 | SALES aplica descuento sin autorización | 403 Forbidden |
| 27 | Request sin autenticación a endpoint protegido | 401 Unauthorized |

#### Tests de reparaciones

| # | Caso | Validación esperada |
|---|---|---|
| 28 | Flujo completo de reparación | Todos los estados transicionados correctamente |
| 29 | Cancelación sin repuestos usados | Sin cargo, repuestos devueltos al inventario |
| 30 | Cancelación con repuestos usados | Cargo aplicado, solo los no usados devueltos |
| 31 | Costo supera authorized_limit | Estado PAUSED, notificación enviada |
| 32 | Entrega sin cobro previo | Error, CashMovement requerido |

### 35.3 Herramientas de testing

| Capa | Herramienta |
|---|---|
| Unit + Integration (backend) | pytest + pytest-asyncio |
| HTTP testing (backend) | httpx AsyncClient |
| Base de datos de tests | PostgreSQL real en Docker (no mocks) |
| Frontend components | Jest + Testing Library |
| E2E | Playwright |
| Cobertura | pytest-cov (mínimo 80% en módulos financieros) |

### 35.4 CI obligatorio

En cada Pull Request:
1. `ruff` (lint Python)
2. `mypy` (type checking Python)
3. `pytest` (tests backend)
4. `eslint` (lint TypeScript)
5. `tsc --noEmit` (type checking frontend)

El merge se bloquea si falla cualquier paso.

---

## 36. ESTRATEGIA DE BACKUPS

### 36.1 Niveles de backup

#### Nivel 1 — PostgreSQL

| Tipo | Frecuencia | Retención | Destino |
|---|---|---|---|
| Full dump (`pg_dump`) | Diario (2 AM) | 30 días | S3 bucket `backups/daily/` |
| Dump semanal | Domingo | 12 semanas | S3 bucket `backups/weekly/` |
| Dump mensual | Día 1 de cada mes | 12 meses | S3 bucket `backups/monthly/` |
| WAL archiving | Continuo | 7 días | S3 bucket `backups/wal/` |

El WAL archiving permite recuperación a cualquier punto en el tiempo (PITR).

#### Nivel 2 — Storage (archivos)

| Tipo | Frecuencia | Retención | Destino |
|---|---|---|---|
| Sincronización de bucket | Diario (3 AM) | Misma política | S3 bucket secundario |

#### Nivel 3 — Verificación de backups

| Tarea | Frecuencia | Proceso |
|---|---|---|
| Prueba de restauración | Semanal | Restaurar en contenedor temporal, ejecutar queries de integridad |
| Reporte de verificación | Semanal | Registrar resultado en log de backups |

**Regla:** Un backup no verificado no es un backup válido.

### 36.2 Proceso de restauración

```
1. Detener el servicio API (modo mantenimiento)
2. Crear snapshot de la BD actual antes de restaurar
3. Ejecutar pg_restore del dump elegido
4. Si se usa PITR: aplicar WALs hasta el punto deseado
5. Verificar integridad: contar registros clave, verificar última transacción
6. Reiniciar servicio
7. Registrar la restauración en el log de operaciones
```

---

## 37. ESTRATEGIA DE DESPLIEGUE

### 37.1 Entorno de desarrollo local

```yaml
# docker-compose.yml incluye:
services:
  postgres:     # PostgreSQL 16
  redis:        # Redis 7
  minio:        # S3-compatible local (puerto 9000 API, 9001 console)
  api:          # FastAPI en puerto 8000
  worker:       # Celery worker
  worker-beat:  # Celery beat (tareas programadas)
  flower:       # Monitor Celery en puerto 5555
  web:          # Next.js en puerto 3000
  nginx:        # Reverse proxy en puerto 80
```

### 37.2 Entorno de producción (inicial)

Para la operación en Sicuani se recomienda:

- **Servidor:** VPS o servidor físico propio con Linux (Ubuntu 22.04+)
- **Orquestación:** Docker Compose (suficiente para la escala inicial)
- **Reverse proxy:** Nginx con SSL via Let's Encrypt (Certbot)
- **Dominio:** configurar registro DNS apuntando al servidor
- **Backups:** S3-compatible (AWS S3, Cloudflare R2, o Backblaze B2)

### 37.3 CI/CD con GitHub Actions

```
Rama feature/* → PR → CI (lint + tests) → Review
PR aprobado → merge a develop → Deploy staging (si existe)
Release → merge a main → Build imágenes → Deploy producción
```

Nunca hacer push directo a `main`.

### 37.4 Variables de entorno

El archivo `.env.example` documenta todas las variables requeridas:

```
# Base de datos
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/hasbun

# Redis
REDIS_URL=redis://localhost:6379/0

# Seguridad
SECRET_KEY=...
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Storage
S3_ENDPOINT=...
S3_ACCESS_KEY=...
S3_SECRET_KEY=...
S3_BUCKET_NAME=hasbun-files

# WhatsApp
WHATSAPP_PROVIDER=mock
WHATSAPP_TOKEN=...
WHATSAPP_PHONE_ID=...

# Tipo de cambio
EXCHANGE_RATE_PROVIDER=mock
```

Nunca commitear `.env` al repositorio. Solo `.env.example` con valores de ejemplo.

---

## 38. RIESGOS TÉCNICOS

| # | Riesgo | Probabilidad | Impacto | Mitigación implementada |
|---|---|---|---|---|
| 1 | **Concurrencia en stock:** dos ventas del mismo serializado simultáneamente | Media | Crítico | `SELECT ... FOR UPDATE` en `SerializedUnit`. Unique constraint en `serial_number`. Test de concurrencia obligatorio. |
| 2 | **Pérdida de consistencia venta-caja-inventario:** falla a mitad de una venta | Baja | Crítico | Toda venta en una sola transacción atómica. ROLLBACK automático si cualquier parte falla. |
| 3 | **Doble cobro por doble click:** usuario hace clic dos veces en "Pagar" | Media | Alto | `idempotency_key` único en `SalePayment` y `CreditPayment`. El frontend desactiva el botón tras el primer clic. |
| 4 | **Cálculo de mora incorrecto:** mora mal calculada o aplicada dos veces | Media | Alto | Tests financieros automatizados de mora. Tarea Celery idempotente (verifica período antes de crear). |
| 5 | **Uso de floats para dinero:** errores de redondeo en cálculos | Baja (con disciplina) | Crítico | `NUMERIC(14,2)` en toda columna monetaria de PostgreSQL. `Decimal` en Python. Code review obliga este estándar. |
| 6 | **Credenciales de equipos expuestas:** contraseñas de laptops en texto plano | Baja | Alto | AES-256 para cifrar. Nunca se muestran automáticamente. Cada visualización queda en AuditLog. Se eliminan al entregar. |
| 7 | **Migración de BD en producción falla:** Alembic rompe el esquema en producción | Baja | Crítico | Backup obligatorio antes de cada migración. Migraciones backward-compatible. Probar en staging antes de producción. |
| 8 | **WhatsApp provider caído:** mensajes importantes no se envían | Media | Medio | Cola en Redis. Retry con backoff exponencial (1min → 5min → 15min). Máximo 3 intentos. FAILED genera notificación interna. |
| 9 | **Conexión lenta en Sicuani:** internet inestable afecta la operación del POS | Alta | Medio | Timeouts generosos. Caché agresivo con TanStack Query. Modo offline parcial en POS (registrar localmente, sincronizar al reconectar). Imágenes comprimidas. |
| 10 | **Foto grande bloquea subida en campo:** técnico sube foto de 10MB desde el celular | Media | Medio | Compresión client-side antes del upload (máx. 2MB para imágenes). Indicador de progreso. Subida asíncrona que no bloquea el formulario. |

---

## 39. RIESGOS DE NEGOCIO

| # | Riesgo | Impacto | Mitigación implementada |
|---|---|---|---|
| 1 | **Cliente moroso recibe nuevo crédito por descuido** | Alto | El sistema bloquea automáticamente cualquier nuevo crédito a clientes con cuotas vencidas. Solo OWNER puede desbloquear con razón registrada y auditada. |
| 2 | **Técnico entrega equipo sin cobrar** | Alto | El flujo de reparación exige un `CashMovement` registrado antes de poder cambiar el estado a `DELIVERED`. El botón de entrega está bloqueado hasta que exista el pago. |
| 3 | **Vendedor aplica descuento no autorizado** | Medio | Los descuentos requieren `DiscountAuthorization`. SALES solo puede solicitar; OWNER aprueba. El sistema valida la autorización en el backend antes de aplicar el descuento. |
| 4 | **Cierre de caja con diferencia sin revisión** | Alto | Si `difference != 0`, se crea `CashClosureRequest` y la sesión queda en `PENDING_CLOSURE`. OWNER recibe notificación. El cajero no puede cerrar hasta que OWNER apruebe con motivo. |
| 5 | **Pérdida de datos por fallo de hardware** | Crítico | Backup diario automatizado a S3. WAL archiving continuo para PITR. Verificación semanal de backup con restauración de prueba. |
| 6 | **Mal manejo de tipo de cambio en ventas históricas** | Alto | El `exchange_rate` se congela en la venta al momento de crearla. Nunca se recalcula con el tipo de cambio actual. Los reportes históricos usan el TC registrado. |
| 7 | **Reparación entregada sin garantía emitida** | Medio | Al transicionar a `DELIVERED`, el sistema crea automáticamente un `RepairWarranty` y una `Warranty`. No es opcional. |
| 8 | **Stock negativo silencioso:** inventario muestra negativo sin alerta | Crítico | Constraint `CHECK (quantity >= 0)` en la vista de stock calculado. El servicio de ventas verifica stock antes de confirmar. Alerta de stock bajo cuando cae al umbral configurado. |
| 9 | **Dos personas venden el mismo serializado simultáneamente** | Alto | `SELECT ... FOR UPDATE` en `SerializedUnit` bloquea la fila. Unique constraint en `(serial_number, status=SOLD)`. Solo la primera transacción que adquiere el lock procede. |

---

## 40. FASES DE IMPLEMENTACIÓN

### FASE 0 — Fundación y Arquitectura

**Objetivo:** Base técnica sólida y reproducible. Todo el equipo puede arrancar el proyecto localmente.

| Tarea | Descripción |
|---|---|
| Repositorio Git | Monorepo en GitHub/GitLab con ramas protegidas |
| Estructura de carpetas | Directorios completos según arquitectura definida |
| docker-compose.yml | PostgreSQL, Redis, MinIO, API, Worker, Web, Nginx |
| pyproject.toml | Dependencias Python (FastAPI, SQLAlchemy, Alembic, etc.) |
| package.json | Dependencias Frontend (Next.js, shadcn/ui, etc.) |
| Config vía pydantic-settings | Variables de entorno tipadas |
| .env.example | Todas las variables documentadas |
| SQLAlchemy base + sesión async | Conexión PostgreSQL configurada |
| Alembic configurado | Sin migraciones aún, solo la infraestructura |
| Health checks | `GET /health` y `GET /ready` |
| Logging estructurado | JSON con request_id, user_id, module |
| CI básico | GitHub Actions: lint + type check en cada PR |
| README.md | Instrucciones de arranque local |

**Criterio de completado:** `docker-compose up` levanta todos los servicios, `/health` responde 200, CI pasa.

---

### FASE 1 — Autenticación, Usuarios y Permisos

**Objetivo:** Sistema de identidad completo. Ninguna operación posterior es posible sin este módulo.

| Tarea | Descripción |
|---|---|
| Modelos | User, Role, Permission, UserRole, RolePermission, UserPermissionOverride |
| Migración Alembic | Primera migración real |
| Auth: login | Cookie HttpOnly con token de sesión |
| Auth: logout | Invalidar sesión |
| Auth: refresh | Renovar sesión activa |
| Middleware autenticación | Extrae usuario de cookie en cada request |
| Dependency de permisos | `require_permission("ventas.crear")` reutilizable |
| Seeds | OWNER, SALES, TECHNICIAN, SOFTWARE_DEVELOPER, CUSTOMER (ficticios) |
| Módulo audit básico | AuditLog con middleware de captura |
| Tests | Login OK, Login fallido, Logout, Permiso denegado (403), Sin auth (401) |
| Frontend | Páginas de login/logout, protección de rutas admin |

**Criterio de completado:** Login funciona, cookies seguras, 403 en endpoints protegidos sin permiso, audit registra acciones.

---

### FASE 2 — Catálogo de Productos

**Objetivo:** Gestión completa de productos, categorías, marcas y tipo de cambio.

| Tarea | Descripción |
|---|---|
| Modelos | Brand, Category, Product, ProductAttributeValue, Attribute, AttributeValue, SerializedUnit, ProductOffer |
| ExchangeRate | Módulo completo con MockExchangeRateProvider |
| Generador SKU | Transaccional, sin duplicados |
| Upload de archivos | FileObject + integración MinIO |
| CRUD productos | Con permisos correctos por rol |
| Tests | Creación, SKU único, atributos, oferta vigente, permiso de edición |
| Frontend | Listado, detalle, formulario de producto, gestión de categorías |

---

### FASE 3 — Inventario y Compras

**Objetivo:** Inventario real basado en movimientos. Compras a proveedores.

| Tarea | Descripción |
|---|---|
| Modelos | InventoryMovement, Supplier, Purchase, PurchaseItem |
| Stock calculado | Vista/función que suma movimientos |
| Kardex | Endpoint de historial por producto |
| Flujo de compra | Creación → Recepción → InventoryMovements |
| Tests | Stock correcto, stock negativo bloqueado, concurrencia |

---

### FASE 4 — Caja, POS y Ventas

**Objetivo:** Operación financiera diaria completa.

| Tarea | Descripción |
|---|---|
| Modelos | CashRegister, CashSession, CashMovement, CashTransfer, CashClosureRequest, Sale, SaleItem, SalePayment, DiscountAuthorization |
| POS | Interfaz de venta rápida |
| Flujo venta contado | Transacción atómica completa |
| Cierre de caja | Con CashClosureRequest y aprobación de OWNER |
| Transferencias | Entre cajas, atómico |
| Tests financieros | 13 casos críticos de caja + venta |

---

### FASE 5 — Créditos, Cuotas y Mora

**Objetivo:** Sistema financiero de crédito completo.

| Tarea | Descripción |
|---|---|
| Modelos | CreditAgreement, CreditInstallment, CreditPayment, CreditMora, CreditAuthorization, Reservation |
| Flujo de crédito | Con todas las reglas de negocio |
| Tarea Celery mora | Diaria, idempotente, 3% sobre saldo vencido |
| Verificaciones | Límite, morosidad, historial, múltiples créditos |
| Entrega antes de pago total | DELIVERED_ON_CREDIT → SOLD |
| Tests | Todos los casos de crédito definidos en §35.2 |

---

### FASE 6 — Cotizaciones y WhatsApp

| Tarea | Descripción |
|---|---|
| Quote + QuoteItem | CRUD + conversión a venta |
| WhatsAppProvider | Mock completo con templates |
| Eventos WhatsApp | Todos los definidos en §23.3 |
| Notificaciones internas | Sistema básico por rol |

---

### FASE 7 — Reparaciones

| Tarea | Descripción |
|---|---|
| Todos los modelos | RepairOrder, Device, Diagnosis, Quote, Parts, Evidence, Credentials, Warranty |
| Flujo completo | Todos los estados y transiciones |
| Credenciales cifradas | AES-256 + acceso auditado |
| Repuestos | Flujo reserva → uso → devolución |
| Tests | 5 casos críticos de reparación |

---

### FASE 8 — Mantenimientos, Instalaciones y Envíos

| Tarea | Descripción |
|---|---|
| MaintenanceOrder | CRUD + consumo inventario |
| InstallationOrder | Flujo completo con evidencia obligatoria |
| Shipment | Tracking de envíos de reparaciones |
| DeliveryOrder | Delivery local |

---

### FASE 9 — Garantías y Devoluciones

| Tarea | Descripción |
|---|---|
| Warranty | Creación automática + búsqueda + alertas |
| Return | Flujo de devolución con todos los motivos |
| Tarea alertas garantía | Celery: 7 días y 30 días antes de vencimiento |

---

### FASE 10 — Sublimación y Personalización

| Tarea | Descripción |
|---|---|
| CustomizationOrder | Flujo completo |
| DesignFile | Upload + versionado |
| ProductionStatus | Seguimiento de producción |

---

### FASE 11 — Proyectos de Software

| Tarea | Descripción |
|---|---|
| SoftwareProject | CRUD + publicación |
| Web pública | Portafolio visible |
| Casos de éxito | ClientSuccessStory |

---

### FASE 12 — Dashboard, Reportes y Notificaciones

| Tarea | Descripción |
|---|---|
| Dashboard OWNER | Todos los KPIs definidos |
| Dashboard SALES | Vista de ventas |
| Dashboard TECHNICIAN | Vista técnica |
| Reportes | Todos los definidos en §25 con PDF/Excel |
| Calendario | Vista unificada de eventos |
| Búsqueda global | Todas las entidades |

---

### FASE 13 — Producción y Hardening

| Tarea | Descripción |
|---|---|
| Seguridad | Audit completo, rate limiting, headers |
| Backups automatizados | pg_dump + WAL + verificación semanal |
| Monitoreo | Health checks, alertas de errores |
| Optimización | Índices, queries lentas, caché |
| Documentación | Toda la documentación técnica actualizada |
| Deploy producción | Servidor en Sicuani con SSL |

---

## 41. CRITERIO DE TERMINADO

Una funcionalidad está terminada **únicamente** cuando cumple **todos** los siguientes puntos:

| # | Criterio | Descripción |
|---|---|---|
| 1 | Backend implementado | Modelos, repositorio, servicio y router creados y funcionando |
| 2 | Frontend implementado | UI con todos los estados: carga, vacío, error, datos |
| 3 | Base de datos implementada | Tablas, columnas y tipos correctos en PostgreSQL |
| 4 | Migración Alembic creada | Ningún cambio de esquema directo en producción |
| 5 | Permisos implementados | Cada endpoint tiene su guard de permiso. 403 si no corresponde |
| 6 | Validaciones backend | Pydantic valida entrada. Nunca solo confiar en frontend |
| 7 | Auditoría implementada | Toda operación crítica registra en AuditLog |
| 8 | Transacciones implementadas | Operaciones multi-tabla son atómicas con ROLLBACK |
| 9 | Tests implementados | Unit + Integration mínimos. Casos críticos cubiertos |
| 10 | Documentación actualizada | OpenAPI/Swagger actualizado, business-rules.md si aplica |
| 11 | Manejo de errores | Errores retornan formato estándar con código y request_id |
| 12 | Estados correctamente definidos | Todos los estados posibles modelados y documentados |

---

## 42. REGLAS ABSOLUTAS DEL SISTEMA

Las siguientes reglas no tienen excepciones técnicas. Cualquier código que las viole debe ser rechazado en code review.

### 42.1 Reglas de datos

```
1. Nunca usar float/FLOAT para dinero.
   → Siempre NUMERIC(14,2) en PostgreSQL y Decimal en Python.

2. Nunca borrar registros financieros.
   → Cancelar, revertir o anular con estado. Auditar.

3. Nunca modificar el tipo de cambio histórico de una operación.
   → El TC se congela al crear la operación. Se guarda en la fila.

4. Nunca permitir stock negativo.
   → Constraint en BD + validación en servicio.

5. Nunca vender el mismo número de serie dos veces.
   → Unique constraint + row lock.
```

### 42.2 Reglas de seguridad

```
6. Nunca guardar contraseñas en texto plano.
   → bcrypt con salt siempre.

7. Nunca guardar credenciales de equipos en texto plano.
   → AES-256 obligatorio.

8. Nunca confiar solo en permisos del frontend.
   → Cada endpoint valida permisos en backend.

9. Nunca exponer stack traces al cliente.
   → Solo en desarrollo. En producción: mensaje genérico + request_id.

10. Nunca almacenar tokens sensibles en localStorage.
    → Cookies HttpOnly Secure siempre.

11. Nunca hardcodear secretos en el código.
    → Variables de entorno. .env en .gitignore.
```

### 42.3 Reglas de arquitectura

```
12. Nunca poner lógica financiera en componentes React.
    → Solo en servicios de backend.

13. Nunca poner lógica de negocio en routers FastAPI.
    → Los routers son delgados: autenticación → servicio → respuesta.

14. Nunca simular la base de datos con estructuras en memoria
    cuando existe PostgreSQL.
    → Tests usan BD real en Docker.

15. Toda operación multi-tabla debe ejecutarse en una transacción.
    → async with session.begin()

16. Todo cambio de esquema debe pasar por Alembic.
    → Nunca ALTER TABLE directo en producción.
```

### 42.4 Reglas de negocio

```
17. Un usuario solo puede tener UNA caja abierta a la vez.

18. El cierre de caja con diferencia requiere aprobación del OWNER.

19. Un cliente moroso no puede recibir nuevo crédito sin OWNER.

20. Un descuento mayor a cero aplicado por SALES requiere
    DiscountAuthorization aprobada por OWNER.

21. Una reparación no puede pasar a DELIVERED sin CashMovement
    de cobro registrado.

22. Una venta a crédito requiere pago inicial, excepto cliente
    frecuente + autorización OWNER.

23. La mora no se capitaliza sobre mora anterior.

24. Una cotización convertida a venta no permite reingresar
    los productos manualmente.

25. Los repuestos no utilizados en una reparación cancelada
    deben volver automáticamente al inventario.
```

---

## APÉNDICE A — Glosario

| Término | Significado en el sistema |
|---|---|
| OWNER | Rol de la dueña del negocio. Acceso total. |
| SALES | Rol de vendedor. Opera ventas y POS. |
| TECHNICIAN | Rol técnico. Opera reparaciones e instalaciones. |
| SW_DEV | Rol de desarrollador de software. Gestiona proyectos. |
| TC | Tipo de cambio (tasa USD → PEN) |
| PEN | Sol peruano (moneda principal) |
| POS | Punto de Venta (Point of Sale) |
| PITR | Point-in-Time Recovery (recuperación a punto exacto) |
| CRD | Prefijo de crédito (CRD-YYYY-XXXXX) |
| REP | Prefijo de reparación (REP-YYYY-XXXXX) |
| VTA | Prefijo de venta (VTA-YYYY-XXXXX) |
| COT | Prefijo de cotización (COT-YYYY-XXXXX) |
| INST | Prefijo de instalación (INST-YYYY-XXXXX) |
| GAR | Prefijo de garantía (GAR-YYYYMMDD-XXXXX) |
| MNT | Prefijo de mantenimiento (MNT-YYYY-XXXXX) |
| SUB | Prefijo de sublimación (SUB-YYYY-XXXXX) |
| DEL | Prefijo de delivery (DEL-YYYY-XXXXX) |
| ENV | Prefijo de envío (ENV-YYYY-XXXXX) |
| WAL | Write-Ahead Log (registro previo de escritura en PostgreSQL) |
| RBAC | Role-Based Access Control (control de acceso por roles) |
| AES | Advanced Encryption Standard (cifrado de credenciales) |

---

## APÉNDICE B — Convenciones de Código

### Commits (Conventional Commits)

```
feat(auth): add JWT cookie-based authentication
fix(inventory): prevent negative stock on concurrent sale
chore(docker): add minio service to compose
test(credits): add mora calculation tests
docs(api): document /api/v1/sales endpoints
refactor(cash): extract closure logic to service layer
```

### Ramas Git

```
main           → producción estable (protegida, solo PR)
develop        → integración continua (protegida, solo PR)
feature/fase-0-base
feature/fase-1-auth
feature/fase-2-catalogo
bugfix/descripcion-corta
hotfix/descripcion-urgente
```

### Nombres de archivos

- Backend: `snake_case.py`
- Frontend: `PascalCase.tsx` para componentes, `camelCase.ts` para utils
- Migraciones: `YYYY_MM_DD_HHMM_descripcion.py`

---

*Documento generado el 2026-08-17. Versión 1.0.0.*
*Actualizar este documento ante cualquier cambio de requerimientos.*
*Este documento es la fuente de verdad para decisiones de diseño.*
