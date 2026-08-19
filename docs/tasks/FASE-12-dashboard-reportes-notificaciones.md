# FASE 12 — Dashboard, Reportes y Notificaciones

**Rama:** `feature/fase-12-dashboard`
**Objetivo:** Dashboards por rol con KPIs en tiempo real, reportes exportables en PDF/Excel, búsqueda global, calendario unificado y notificaciones completas.
**Prerrequisito:** FASE 11 completada y mergeada a `develop`.
**Criterio de salida:** Dashboard OWNER muestra todos los KPIs. Reportes exportables a PDF y Excel. Búsqueda global encuentra cualquier entidad por código o nombre.

---

## Progreso

| Completados | Total | Porcentaje |
|---|---|---|
| 0 | 24 | 0% |

---

## Issues

### DASHBOARD OWNER

---

#### #F12-01 — Endpoints de KPIs para dashboard OWNER
- **Tipo:** `[BE]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** FASE-11 completa

**Tareas:**
- [ ] Crear `apps/api/app/modules/dashboard/application/service.py`:
  - `get_owner_dashboard(date_range)` — agrega datos de todos los módulos:
    ```
    ventas_hoy: total del día (monto + cantidad)
    ventas_mes: total del mes actual
    ganancia_estimada_mes: SUM(sale_price - cost_price) * qty vendido
    caja_balance: balance actual de todas las cajas abiertas
    creditos_activos: COUNT donde status=ACTIVE
    creditos_vencidos: COUNT donde status=OVERDUE/DEFAULTED
    mora_total: SUM de mora pendiente de cobro
    stock_bajo: COUNT productos con available <= stock_minimum
    stock_agotado: COUNT productos con available = 0
    reparaciones_en_proceso: COUNT status IN (IN_REPAIR, TESTING)
    reparaciones_listas: COUNT status = READY
    instalaciones_hoy: COUNT scheduled_date = hoy
    cotizaciones_pendientes: COUNT status IN (SENT, VIEWED)
    garantias_por_vencer: COUNT vence en 7 días
    alertas_activas: COUNT notificaciones URGENT no leídas
    ```
- [ ] Queries optimizadas (no N+1): una query por sección o join optimizado
- [ ] Caché en Redis con TTL 2 minutos para el dashboard
- [ ] Invalidar caché al registrar venta, pago, apertura de reparación
- [ ] Endpoint: `GET /api/v1/dashboard/owner`

---

#### #F12-02 — Endpoints de KPIs para dashboard SALES
- **Tipo:** `[BE]`
- **Prioridad:** 🟠 ALTO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F12-01

**Tareas:**
- [ ] `get_sales_dashboard(user_id, date_range)` — datos filtrados por el vendedor:
  ```
  ventas_del_dia: solo las del usuario actual
  cotizaciones_pendientes: las suyas
  pedidos_pendientes: sus deliveries
  caja_estado: si tiene sesión abierta y balance
  pagos_de_cuotas_hoy: cuotas con due_date = hoy en sus clientes
  autorizaciones_pendientes: descuentos suyos esperando aprobación
  ```
- [ ] Endpoint: `GET /api/v1/dashboard/sales`

---

#### #F12-03 — Endpoints de KPIs para dashboard TECHNICIAN
- **Tipo:** `[BE]`
- **Prioridad:** 🟠 ALTO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F12-01

**Tareas:**
- [ ] `get_technician_dashboard(user_id)`:
  ```
  reparaciones_asignadas: por estado (RECEIVED, DIAGNOSING, IN_REPAIR, TESTING, READY)
  mantenimientos_hoy: scheduled_at = hoy
  instalaciones_hoy: scheduled_date = hoy
  materiales_aprobados_pendientes: APPROVED sin CONSUMED
  equipos_listos: status = READY (para notificar al cliente)
  ```
- [ ] Endpoint: `GET /api/v1/dashboard/technician`

---

#### #F12-04 — Frontend dashboards
- **Tipo:** `[FE]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F12-01, #F12-02, #F12-03

**Tareas:**
- [ ] `apps/web/app/admin/dashboard/owner/page.tsx`:
  - Cards con KPIs principales (ventas hoy, mes, ganancia)
  - Gráfico de ventas últimos 7 días (línea)
  - Cards de alertas (stock bajo, caja pendiente, mora)
  - Tabla de reparaciones listas para entregar
  - Lista de cuotas vencidas top 5
- [ ] `apps/web/app/admin/dashboard/sales/page.tsx`:
  - Cards simples de ventas del día
  - Lista de cotizaciones enviadas sin respuesta
  - Estado de su caja
- [ ] `apps/web/app/admin/dashboard/technician/page.tsx`:
  - Lista de órdenes asignadas por estado
  - Agenda del día (instalaciones + mantenimientos)
  - Equipos listos para entrega
- [ ] Router automático: al entrar a `/admin/dashboard` → redirige según rol
- [ ] TanStack Query con `refetchInterval: 120000` (2 minutos) para KPIs

---

### REPORTES

---

#### #F12-05 — Motor de reportes backend
- **Tipo:** `[BE]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F12-01

**Descripción:**
Todos los reportes comparten la misma arquitectura: query con filtros → datos → exportar en formato solicitado.

**Tareas:**
- [ ] Crear `apps/api/app/modules/reports/` con estructura:
  ```
  reports/
    application/
      service.py          — orquesta cada reporte
      generators/
        sales_report.py
        cash_report.py
        inventory_report.py
        kardex_report.py
        purchases_report.py
        credits_report.py
        mora_report.py
        repairs_report.py
        installations_report.py
        warranties_report.py
        customers_report.py
    infrastructure/
      pdf_exporter.py     — usa WeasyPrint o ReportLab
      excel_exporter.py   — usa openpyxl
  ```
- [ ] Instalar `openpyxl` para Excel y `weasyprint` o `reportlab` para PDF
- [ ] Cada generador recibe filtros → retorna `ReportData(headers, rows, summary)`
- [ ] El exportador convierte `ReportData` al formato solicitado
- [ ] Para reportes grandes: generación asíncrona via Celery + descarga por URL firmada

---

#### #F12-06 — Implementar reportes principales
- **Tipo:** `[BE]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F12-05

**Tareas (un endpoint por reporte):**
- [ ] `GET /api/v1/reports/sales` — ventas con filtros: fecha, tipo, estado, vendedor
- [ ] `GET /api/v1/reports/cash` — movimientos de caja por sesión/fecha/caja
- [ ] `GET /api/v1/reports/inventory` — stock actual por producto/categoría
- [ ] `GET /api/v1/reports/kardex/{product_id}` — historial de movimientos
- [ ] `GET /api/v1/reports/purchases` — compras por proveedor/fecha/estado
- [ ] `GET /api/v1/reports/credits` — créditos por estado/cliente
- [ ] `GET /api/v1/reports/mora` — morosidad: clientes con cuotas vencidas
- [ ] `GET /api/v1/reports/repairs` — reparaciones por técnico/estado/fecha
- [ ] `GET /api/v1/reports/installations` — instalaciones por técnico/estado
- [ ] `GET /api/v1/reports/warranties` — garantías activas/próximas a vencer
- [ ] `GET /api/v1/reports/customers` — clientes activos/morosos/frecuentes
- [ ] Todos aceptan parámetros: `format=json|pdf|excel`, `date_from`, `date_to`
- [ ] Acceso controlado: OWNER ve todos; SALES y TECHNICIAN ven solo los suyos

---

#### #F12-07 — Frontend de reportes
- **Tipo:** `[FE]`
- **Prioridad:** 🟠 ALTO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F12-06

**Tareas:**
- [ ] `apps/web/app/admin/reportes/page.tsx` — índice de reportes disponibles
- [ ] Vista genérica de reporte `apps/web/app/admin/reportes/[type]/page.tsx`:
  - Panel de filtros (fecha desde/hasta, filtros específicos del reporte)
  - Tabla de resultados con paginación
  - Fila de totales/resumen al pie
  - Botón "Exportar PDF" → descarga directa
  - Botón "Exportar Excel" → descarga directa
  - Botón "Exportar CSV" → descarga directa
- [ ] Spinner de carga mientras se genera el reporte
- [ ] Para reportes grandes: indicador de "generando..." con polling hasta que esté listo

---

### BÚSQUEDA GLOBAL

---

#### #F12-08 — Motor de búsqueda global backend
- **Tipo:** `[BE]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** FASE-11 completa

**Descripción:**
Una sola búsqueda que encuentra cualquier entidad del sistema por código exacto o nombre aproximado.

**Tareas:**
- [ ] Crear `apps/api/app/modules/dashboard/application/search_service.py`:
  - `global_search(query: str, user: User) -> SearchResults`
  - Para cada categoría, hacer query en paralelo (asyncio.gather)
  - Filtrar resultados según permisos del usuario
- [ ] Entidades indexadas:
  ```
  customers    → nombre, DNI, RUC, teléfono
  products     → nombre, SKU, código de barras
  sales        → código VTA-...
  credits      → código CRD-...
  repairs      → código REP-..., nombre del cliente
  quotes       → código COT-...
  warranties   → código GAR-...
  installations → código INST-...
  deliveries   → código DEL-...
  shipments    → número de tracking
  ```
- [ ] Búsqueda exacta por código (REP-2026-00025 → encuentra esa reparación directamente)
- [ ] Búsqueda parcial por nombre (con ILIKE en PostgreSQL)
- [ ] Endpoint: `GET /api/v1/search?q=REP-2026-00025`
- [ ] Respuesta paginada por categoría (máx. 5 resultados por tipo)
- [ ] Caché en Redis: TTL 30 segundos para queries frecuentes

---

#### #F12-09 — Frontend de búsqueda global
- **Tipo:** `[FE]`
- **Prioridad:** 🟠 ALTO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F12-08

**Tareas:**
- [ ] Barra de búsqueda global en el header del panel admin (siempre visible)
- [ ] Keyboard shortcut: `Ctrl+K` / `Cmd+K` abre la búsqueda (Command Palette style)
- [ ] Debounce 300ms antes de enviar la query
- [ ] Resultados agrupados por tipo con íconos
- [ ] Click en resultado → navega al detalle
- [ ] Búsqueda exacta por código: resultado único directo sin agrupar

---

### CALENDARIO UNIFICADO

---

#### #F12-10 — Endpoint de calendario unificado
- **Tipo:** `[BE]`
- **Prioridad:** 🟠 ALTO
- **Estado:** ⬜ Pendiente
- **Depende de:** FASE-11 completa

**Tareas:**
- [ ] Endpoint `GET /api/v1/calendar/events?from=DATE&to=DATE&user_id=UUID`:
  - Instalaciones programadas (InstallationSchedule)
  - Mantenimientos programados (MaintenanceOrder.scheduled_at)
  - Reparaciones con fecha estimada (RepairOrder.estimated_ready_at)
  - Entregas de delivery (DeliveryOrder.scheduled_at)
  - Cuotas con vencimiento (CreditInstallment.due_date)
- [ ] Respuesta uniforme: `[{id, type, title, date, time, color, url, assigned_to}]`
- [ ] Filtrar por `user_id` para vista del técnico (solo sus eventos)
- [ ] Filtrar por tipo de evento

---

#### #F12-11 — Frontend de calendario completo
- **Tipo:** `[FE]`
- **Prioridad:** 🟠 ALTO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F12-10

**Tareas:**
- [ ] `apps/web/app/admin/calendario/page.tsx` — vista completa con librería de calendario
- [ ] Instalar `@fullcalendar/react` o equivalente
- [ ] Vista mensual, semanal y diaria
- [ ] Colores por tipo de evento: azul=instalación, verde=mantenimiento, naranja=reparación, rojo=cuota vencida
- [ ] Filtros: por técnico, por tipo de evento
- [ ] Click en evento → mini popup con botón de ir al detalle

---

### NOTIFICACIONES COMPLETAS

---

#### #F12-12 — Completar sistema de notificaciones internas
- **Tipo:** `[BE]`
- **Prioridad:** 🟠 ALTO
- **Estado:** ⬜ Pendiente
- **Depende de:** FASE-06 (sistema base ya implementado)

**Tareas:**
- [ ] Verificar que todos los eventos generan Notifications en sus módulos respectivos:
  - Solicitud de descuento → OWNER
  - Cierre de caja pendiente → OWNER
  - Material adicional solicitado → OWNER
  - Cuota vencida → OWNER + SALES asignado
  - Garantía por vencer → OWNER
  - Stock bajo → OWNER
  - Reparación lista → OWNER + SALES (quien ingresó)
- [ ] Prioridades correctas (URGENT para caja, mora; HIGH para reparación lista; MEDIUM para stock bajo)
- [ ] Crear endpoint: `GET /api/v1/notifications/stats` → contadores por prioridad

---

#### #F12-13 — Comprobante de venta (impresión / compartir)
- **Tipo:** `[BE]` `[FE]`
- **Prioridad:** 🟠 ALTO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F12-06

**Tareas:**
- [ ] Endpoint: `GET /api/v1/sales/{id}/receipt` — retorna HTML o PDF del comprobante
- [ ] Comprobante incluye: datos del negocio, cliente, ítems, pagos, total, fecha
- [ ] Preparar para SUNAT (estructura compatible, sin integrar todavía)
- [ ] Frontend POS: botón "Imprimir comprobante" (abre ventana de impresión)
- [ ] Botón "Compartir por WhatsApp" → enlace al comprobante o resumen en texto

---

### TESTS

---

#### #F12-14 — Tests de dashboard
- **Tipo:** `[TEST]`
- **Prioridad:** 🟠 ALTO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F12-01

**Tareas:**
- [ ] `test_owner_dashboard_returns_all_sections`
- [ ] `test_sales_dashboard_filtered_by_user` — solo datos del vendedor
- [ ] `test_technician_dashboard_filtered_by_user`
- [ ] `test_sales_cannot_access_owner_dashboard` → 403
- [ ] `test_dashboard_cache_invalidated_on_new_sale`

---

#### #F12-15 — Tests de reportes
- **Tipo:** `[TEST]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F12-06

**Tareas:**
- [ ] `test_sales_report_returns_correct_totals`
- [ ] `test_mora_report_includes_all_overdue`
- [ ] `test_inventory_report_stock_matches_movements`
- [ ] `test_report_export_pdf_returns_file`
- [ ] `test_report_export_excel_returns_file`
- [ ] `test_sales_cannot_see_full_reports` → 403 para reportes de OWNER

---

#### #F12-16 — Tests de búsqueda global
- **Tipo:** `[TEST]`
- **Prioridad:** 🟠 ALTO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F12-08

**Tareas:**
- [ ] `test_search_by_exact_repair_code` → retorna esa reparación
- [ ] `test_search_by_customer_name` → retorna clientes con ese nombre
- [ ] `test_search_respects_permissions` — SALES no ve datos de OWNER
- [ ] `test_search_performance` — query con debounce no hace N queries en paralelo

---

#### #F12-17 — Reporte de ganancias (ventas - costos)
- **Tipo:** `[BE]`
- **Prioridad:** 🟠 ALTO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F12-06

**Tareas:**
- [ ] Endpoint `GET /api/v1/reports/profit`:
  - Por período: SUM((unit_price - unit_cost) * quantity) para todas las ventas PAID/COMPLETED
  - Agrupado por: día, semana, mes, categoría, producto
  - Solo OWNER puede ver costos → solo OWNER puede ver este reporte
- [ ] Frontend: gráfico de barras de ganancia mensual en dashboard OWNER

---

#### #F12-18 — Tarea Celery: reporte diario automático para OWNER
- **Tipo:** `[TASK]`
- **Prioridad:** 🟡 MEDIO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F12-06

**Tareas:**
- [ ] Tarea `generate_daily_summary()`:
  - Ejecutar a las 11 PM
  - Calcular: ventas del día, cobros de cuotas, nuevas reparaciones, stock bajo
  - Crear Notification de tipo DAILY_SUMMARY para OWNER
  - Opcionalmente: enviar resumen por WhatsApp

---

### DOCUMENTACIÓN Y VERIFICACIÓN

---

#### #F12-19 — Documentar API de reportes
- **Tipo:** `[DOCS]`
- **Prioridad:** 🟡 MEDIO
- **Estado:** ⬜ Pendiente

**Tareas:**
- [ ] Documentar todos los endpoints de reportes en Swagger
- [ ] Documentar los formatos de exportación disponibles
- [ ] Documentar los filtros disponibles por reporte

---

#### #F12-20 — Optimizar queries de dashboard con índices
- **Tipo:** `[DB]`
- **Prioridad:** 🟠 ALTO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F12-01

**Tareas:**
- [ ] Revisar queries del dashboard con `EXPLAIN ANALYZE`
- [ ] Crear índices específicos para queries de dashboard:
  - `(status, created_at)` en sales
  - `(status, due_date)` en credit_installments
  - `(status, received_at)` en repair_orders
- [ ] Migración Alembic para los nuevos índices
- [ ] Verificar que el dashboard OWNER carga en < 500ms con seed completo

---

#### #F12-21 — Completar comprobante y PDF para reparaciones
- **Tipo:** `[BE]` `[FE]`
- **Prioridad:** 🟡 MEDIO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F12-06

**Tareas:**
- [ ] Endpoint `GET /api/v1/repairs/{id}/receipt` — orden de trabajo en PDF
- [ ] Incluye: datos del cliente, equipo, trabajo realizado, garantía, costo
- [ ] Botón en frontend para imprimir/descargar

---

#### #F12-22 — Widget de notificaciones en tiempo real
- **Tipo:** `[FE]`
- **Prioridad:** 🟡 MEDIO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F12-12

**Tareas:**
- [ ] Polling cada 30 segundos para contador de notificaciones no leídas
- [ ] Badge numérico en header con animación cuando hay nuevas
- [ ] Dropdown con las últimas 5 notificaciones
- [ ] Link "Ver todas" → `/admin/notificaciones`
- [ ] Preparar estructura para WebSocket (documentar punto de extensión)

---

#### #F12-23 — Tests de calendario
- **Tipo:** `[TEST]`
- **Prioridad:** 🟡 MEDIO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F12-10

**Tareas:**
- [ ] `test_calendar_returns_all_event_types`
- [ ] `test_calendar_filtered_by_technician`
- [ ] `test_calendar_date_range_filter`

---

#### #F12-24 — Verificación final de FASE 12
- **Tipo:** `[INFRA]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** Todos los anteriores

**Checklist de salida de fase:**
- [ ] Dashboard OWNER muestra todos los KPIs con datos correctos
- [ ] Dashboard SALES y TECHNICIAN muestran solo sus datos
- [ ] Todos los reportes exportan PDF y Excel correctamente
- [ ] Búsqueda global encuentra por código exacto (REP-..., VTA-..., etc.)
- [ ] Búsqueda respeta permisos por rol
- [ ] Calendario muestra todos los tipos de eventos
- [ ] Notificaciones llegan al rol correcto
- [ ] Dashboard carga en < 500ms
- [ ] CI verde
- [ ] PR mergeado a `develop`

---

*Referencia: [REQUIREMENTS.md](../REQUIREMENTS.md) §27 Dashboard, §25 Reportes, §24 Notificaciones*
*Fase anterior: [FASE 11](FASE-11-software-proyectos.md) | Siguiente fase: [FASE 13](FASE-13-produccion-hardening.md)*
