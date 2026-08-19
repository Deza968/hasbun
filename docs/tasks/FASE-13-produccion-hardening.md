# FASE 13 — Producción y Hardening

**Rama:** `feature/fase-13-produccion`
**Objetivo:** Preparar el sistema para producción real en Sicuani. Seguridad completa, backups automáticos verificados, monitoreo, optimización de rendimiento y documentación final.
**Prerrequisito:** FASE 12 completada y mergeada a `develop`.
**Criterio de salida:** Sistema desplegado en servidor de producción con SSL, backups automáticos verificados, todas las alertas de seguridad resueltas, documentación completa.

---

## Progreso

| Completados | Total | Porcentaje |
|---|---|---|
| 0 | 20 | 0% |

---

## Issues

### SEGURIDAD

---

#### #F13-01 — Auditoría de seguridad completa
- **Tipo:** `[SEC]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** FASE-12 completa

**Tareas:**
- [ ] Revisar todos los endpoints: ¿alguno sin autenticación que debería tenerla?
- [ ] Revisar todos los endpoints: ¿alguno con permisos incorrectos?
- [ ] Verificar que ningún endpoint devuelve datos de otros usuarios (data isolation)
- [ ] Verificar que contraseñas nunca aparecen en logs ni en respuestas de API
- [ ] Verificar que credenciales de equipos están cifradas en todas las rutas de código
- [ ] Verificar que `SECRET_KEY`, tokens de WhatsApp y claves S3 nunca están en el código
- [ ] Ejecutar `bandit` (Python security linter): `bandit -r apps/api/app/`
- [ ] Revisar headers de seguridad HTTP con herramienta online (securityheaders.com)
- [ ] Verificar que CORS está configurado solo para orígenes permitidos en producción
- [ ] Verificar que rate limiting está activo en endpoints de auth
- [ ] Revisar que no existen endpoints de debug activos en producción (`/docs` en prod: opcional o protegido)

**Definición de terminado:**
- [ ] 0 issues críticos en bandit
- [ ] Todos los headers de seguridad presentes
- [ ] Data isolation verificada: usuario A no puede ver datos de usuario B

---

#### #F13-02 — Hardening de cookies y sesiones
- **Tipo:** `[BE]` `[SEC]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F13-01

**Tareas:**
- [ ] Verificar `Secure=True` en producción (HTTPS obligatorio)
- [ ] Verificar `HttpOnly=True` en todas las cookies de sesión
- [ ] Verificar `SameSite=Lax` (o Strict según necesidad)
- [ ] Implementar rotación automática de refresh tokens
- [ ] Configurar tiempo de expiración de sesión inactiva (configurable)
- [ ] Implementar invalidación de todas las sesiones al cambiar contraseña
- [ ] Verificar que el Redis de sesiones tiene contraseña configurada en producción

---

#### #F13-03 — Rate limiting y protección contra abuso
- **Tipo:** `[BE]` `[SEC]`
- **Prioridad:** 🟠 ALTO
- **Estado:** ⬜ Pendiente
- **Depende de:** FASE-00 (rate limiting base ya implementado)

**Tareas:**
- [ ] Verificar límites por endpoint:
  - `POST /auth/login`: 10/min por IP
  - `POST /auth/register`: 5/hora por IP
  - `POST /payments/*`: 20/min por usuario
  - `POST /whatsapp/*`: 5/min (evitar spam)
  - Endpoints generales: 200/min por usuario
- [ ] Configurar respuesta 429 con `Retry-After` header
- [ ] Logs de requests bloqueados por rate limiting
- [ ] Alertas si hay muchos 429 de una misma IP (posible ataque)

---

### BACKUPS

---

#### #F13-04 — Configurar backups automáticos de PostgreSQL
- **Tipo:** `[INFRA]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** FASE-12 completa

**Tareas:**
- [ ] Crear script `infra/scripts/backup_postgres.sh`:
  ```bash
  pg_dump -Fc $DATABASE_URL > backup_$(date +%Y%m%d_%H%M%S).dump
  # Comprimir y subir a S3
  # Eliminar backups locales después de subir
  # Loguear resultado
  ```
- [ ] Crear tarea Celery `backup_database()`:
  - Ejecutar `pg_dump` como subproceso
  - Subir resultado a S3 en `backups/daily/YYYY/MM/DD/`
  - Registrar en tabla `backup_logs`: timestamp, size, status, s3_key
  - Si falla: notificación urgente al OWNER
- [ ] Configurar en Beat: diariamente a las 2 AM
- [ ] Política de retención:
  - Daily: 30 días
  - Weekly (domingo): 12 semanas
  - Monthly (día 1): 12 meses
- [ ] Script de limpieza de backups expirados

**Definición de terminado:**
- [ ] Backup se ejecuta y sube a S3 sin errores
- [ ] Backup log creado en BD
- [ ] Fallo de backup → notificación urgente al OWNER

---

#### #F13-05 — Backup de storage (archivos MinIO/S3)
- **Tipo:** `[INFRA]`
- **Prioridad:** 🟠 ALTO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F13-04

**Tareas:**
- [ ] Script de sincronización de bucket principal a bucket de respaldo
- [ ] Usar `aws s3 sync` o equivalente de MinIO
- [ ] Ejecutar diariamente a las 3 AM (después del backup de BD)
- [ ] Verificar integridad de sincronización (comparar conteo de objetos)

---

#### #F13-06 — Procedimiento verificado de restauración
- **Tipo:** `[INFRA]` `[DOCS]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F13-04

**Tareas:**
- [ ] Crear script `infra/scripts/restore_postgres.sh`:
  ```bash
  # 1. Descargar backup de S3
  # 2. Crear BD de prueba temporal
  # 3. Restaurar: pg_restore
  # 4. Ejecutar queries de verificación de integridad
  # 5. Reportar resultado
  # 6. Eliminar BD temporal
  ```
- [ ] Crear tarea Celery `verify_latest_backup()`:
  - Semanal: restaura el backup más reciente en una BD temporal en Docker
  - Ejecuta queries de verificación: COUNT de tablas clave, última transacción
  - Registra resultado en `backup_logs.verified_at`
- [ ] Documentar procedimiento manual de restauración en `docs/backups.md`
- [ ] **Regla:** Un backup no verificado no es un backup válido

---

### DESPLIEGUE EN PRODUCCIÓN

---

#### #F13-07 — Configurar servidor de producción
- **Tipo:** `[INFRA]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F13-01

**Tareas:**
- [ ] Servidor Ubuntu 22.04+ con Docker y Docker Compose instalados
- [ ] Configurar firewall: solo puertos 80, 443, 22 abiertos externamente
- [ ] Configurar fail2ban para protección SSH
- [ ] Crear usuario sin privilegios para ejecutar Docker (no root)
- [ ] Configurar `docker-compose.prod.yml` diferente al de desarrollo:
  - Sin Flower en producción (o protegido con auth)
  - Sin hot-reload
  - Logs configurados correctamente
  - Variables de entorno desde archivo `.env.prod` (en servidor, nunca en git)
- [ ] Volúmenes persistentes para PostgreSQL, Redis y MinIO

---

#### #F13-08 — SSL con Let's Encrypt
- **Tipo:** `[INFRA]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F13-07

**Tareas:**
- [ ] Configurar Nginx como reverse proxy con SSL:
  - `www.hasbun.pe` y `hasbun.pe` → frontend
  - `api.hasbun.pe` → backend API
- [ ] Obtener certificado con Certbot: `certbot --nginx -d hasbun.pe -d www.hasbun.pe`
- [ ] Configurar renovación automática: `certbot renew` en crontab
- [ ] Configurar redirect HTTP → HTTPS
- [ ] Configurar HSTS: `Strict-Transport-Security: max-age=31536000`
- [ ] Verificar con SSL Labs (ssllabs.com): calificación A o A+

---

#### #F13-09 — Pipeline CI/CD para producción
- **Tipo:** `[INFRA]`
- **Prioridad:** 🟠 ALTO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F13-07

**Tareas:**
- [ ] Crear `.github/workflows/deploy.yml`:
  - Trigger: push a `main` después de PR aprobado
  - Steps:
    1. CI completo (lint + tests)
    2. Build Docker images
    3. Push a container registry (Docker Hub o GitHub Container Registry)
    4. SSH al servidor de producción
    5. `docker-compose pull` + `docker-compose up -d`
    6. Ejecutar migraciones: `alembic upgrade head`
    7. Health check: `GET /health` debe responder 200
    8. Si falla el health check: rollback automático a imagen anterior
- [ ] Secrets en GitHub Actions: `PROD_HOST`, `PROD_USER`, `PROD_SSH_KEY`
- [ ] Notificación de deploy exitoso/fallido al OWNER

---

#### #F13-10 — Migraciones seguras en producción
- **Tipo:** `[DB]` `[INFRA]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F13-07

**Tareas:**
- [ ] Procedimiento obligatorio antes de cada migración en producción:
  1. `make backup-prod` — ejecutar backup manual
  2. Verificar que backup fue exitoso (check en S3)
  3. Aplicar migración en staging/test primero
  4. Verificar que migración es backward-compatible (no rompe la versión anterior del código)
  5. Aplicar en producción: `alembic upgrade head`
  6. Verificar `/ready` responde 200 después de la migración
- [ ] Documentar el procedimiento en `docs/deployment.md`
- [ ] Crear script `infra/scripts/migrate_prod.sh` que ejecuta los pasos automáticamente

---

### MONITOREO Y OBSERVABILIDAD

---

#### #F13-11 — Health checks completos y logging en producción
- **Tipo:** `[BE]` `[INFRA]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F13-07

**Tareas:**
- [ ] Verificar que `GET /health` y `GET /ready` funcionan correctamente en producción
- [ ] Configurar Nginx para hacer health check al backend cada 30 segundos
- [ ] Configurar Docker healthcheck en docker-compose.prod.yml para cada servicio
- [ ] Logs en producción escritos a volumen persistente (no solo stdout)
- [ ] Logrotate configurado para evitar logs gigantes
- [ ] Configurar alertas básicas: si `/ready` falla 3 veces → notificación (email o WhatsApp)

---

#### #F13-12 — Tabla backup_logs y monitoreo de backups
- **Tipo:** `[BE]` `[DB]`
- **Prioridad:** 🟠 ALTO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F13-04

**Tareas:**
- [ ] Crear modelo `BackupLog`:
  ```
  BackupLog:
    id (UUID, PK)
    backup_type (ENUM): DATABASE/STORAGE
    status (ENUM): SUCCESS/FAILED
    s3_key (VARCHAR)
    size_bytes (BIGINT)
    duration_seconds (INTEGER)
    verified_at (TIMESTAMPTZ)
    error (TEXT)
    created_at (TIMESTAMPTZ)
  ```
- [ ] Migración
- [ ] Endpoint: `GET /api/v1/admin/backups/logs` — historial (solo OWNER)
- [ ] Panel en frontend (admin → configuración → backups): tabla de últimos backups con estado
- [ ] Alerta si el último backup tiene más de 25 horas (se saltó el diario)

---

### OPTIMIZACIÓN DE RENDIMIENTO

---

#### #F13-13 — Optimización de queries lentas
- **Tipo:** `[BE]` `[DB]`
- **Prioridad:** 🟠 ALTO
- **Estado:** ⬜ Pendiente
- **Depende de:** FASE-12 completa

**Tareas:**
- [ ] Activar `log_slow_queries` en PostgreSQL (queries > 500ms)
- [ ] Revisar todas las queries del dashboard con `EXPLAIN ANALYZE`
- [ ] Revisar queries de reportes con sets de datos grandes
- [ ] Crear índices faltantes detectados (migración Alembic)
- [ ] Verificar que no hay queries N+1 en los endpoints principales:
  - `GET /api/v1/customers/{id}` (carga historial completo)
  - `GET /api/v1/credits/{id}` (carga cuotas)
  - `GET /api/v1/repairs/{id}` (carga evidencias y repuestos)
- [ ] Meta: ningún endpoint del panel tarda más de 1 segundo con datos reales

---

#### #F13-14 — Configurar caché Redis correctamente
- **Tipo:** `[BE]`
- **Prioridad:** 🟠 ALTO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F13-13

**Tareas:**
- [ ] Revisar todos los TTLs de caché y ajustar según uso real:
  - Dashboard KPIs: 2 minutos (ya implementado en FASE 12)
  - Permisos de usuario: 5 minutos (ya implementado en FASE 01)
  - Tipo de cambio actual: 1 hora
  - Productos publicados (tienda): 5 minutos
- [ ] Configurar Redis con `maxmemory-policy allkeys-lru` para evitar OOM
- [ ] Monitorear uso de memoria de Redis en producción

---

#### #F13-15 — Carga y stress testing
- **Tipo:** `[TEST]`
- **Prioridad:** 🟠 ALTO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F13-13

**Tareas:**
- [ ] Instalar `locust` o `k6` para pruebas de carga
- [ ] Crear script de prueba de carga para escenarios principales:
  - 20 usuarios simultáneos en el POS haciendo ventas
  - 10 usuarios simultáneos consultando el dashboard
  - 5 usuarios simultáneos generando reportes
- [ ] Meta de rendimiento mínimo:
  - POS: < 500ms por venta
  - Dashboard OWNER: < 1s de carga
  - Reporte de ventas mensual: < 3s

---

### DOCUMENTACIÓN FINAL

---

#### #F13-16 — Documentación técnica completa
- **Tipo:** `[DOCS]`
- **Prioridad:** 🟠 ALTO
- **Estado:** ⬜ Pendiente
- **Depende de:** FASE-12 completa

**Tareas:**
- [ ] Actualizar `docs/architecture.md` con la arquitectura final implementada
- [ ] Completar `docs/business-rules.md` con todas las reglas de negocio
- [ ] Completar `docs/database.md` con diagrama ER final y descripción de tablas críticas
- [ ] Completar `docs/security.md` con todas las medidas implementadas
- [ ] Completar `docs/deployment.md` con instrucciones de deploy paso a paso
- [ ] Completar `docs/backups.md` con procedimientos de backup y restauración
- [ ] Completar `docs/permissions.md` con matriz final de permisos
- [ ] Completar `docs/whatsapp.md` con guía de configuración de proveedor
- [ ] Completar `docs/api.md` con ejemplos de uso de los endpoints principales
- [ ] Crear `docs/runbook.md`: guía de operaciones para incidentes comunes

---

#### #F13-17 — Variables de entorno de producción documentadas
- **Tipo:** `[DOCS]` `[SEC]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F13-07

**Tareas:**
- [ ] Actualizar `.env.example` con todas las variables de producción necesarias
- [ ] Documentar cada variable: descripción, ejemplo, si es obligatoria
- [ ] Crear checklist de variables a configurar antes de primer deploy
- [ ] Verificar que ninguna variable de producción real está en el repositorio
- [ ] Verificar que `.env`, `.env.prod`, `.env.local` están en `.gitignore`

---

#### #F13-18 — Manual de usuario básico para OWNER
- **Tipo:** `[DOCS]`
- **Prioridad:** 🟡 MEDIO
- **Estado:** ⬜ Pendiente
- **Depende de:** FASE-12 completa

**Tareas:**
- [ ] Crear `docs/user-manual-owner.md` con:
  - Cómo abrir y cerrar caja
  - Cómo aprobar créditos y descuentos
  - Cómo ver y exportar reportes
  - Cómo gestionar usuarios y permisos
  - Cómo aprobar cierre de caja con diferencia
  - Qué hacer si hay un error en una venta

---

### VERIFICACIÓN FINAL

---

#### #F13-19 — Checklist de go-live
- **Tipo:** `[INFRA]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** Todos los anteriores

**Checklist completo antes de salir a producción:**

**Seguridad:**
- [ ] Todos los endpoints tienen autenticación correcta
- [ ] HTTPS activo con certificado válido
- [ ] Cookies HttpOnly + Secure + SameSite
- [ ] Credenciales cifradas en BD (verificado)
- [ ] Sin secretos en el repositorio
- [ ] Rate limiting activo en auth
- [ ] CORS configurado solo para dominio de producción
- [ ] Headers de seguridad presentes (verificado con securityheaders.com)

**Backups:**
- [ ] Backup diario automático configurado y verificado
- [ ] Primer backup manual ejecutado y subido a S3
- [ ] Procedimiento de restauración probado
- [ ] Alertas de fallo de backup configuradas

**Rendimiento:**
- [ ] Dashboard carga en < 1s
- [ ] POS responde en < 500ms
- [ ] Queries lentas revisadas y optimizadas
- [ ] Índices de BD creados

**Funcionalidad:**
- [ ] Seed de datos de producción ejecutado (roles, permisos, usuario OWNER real)
- [ ] Configuración del sistema completada (tasas, límites, etc.)
- [ ] WhatsApp configurado con proveedor real (o mock activo con aviso)
- [ ] Tipo de cambio actualizado con valor real

**CI/CD:**
- [ ] Pipeline de deploy funcional
- [ ] Rollback probado
- [ ] Health check automático post-deploy

**Documentación:**
- [ ] Toda la documentación técnica actualizada
- [ ] Manual básico para OWNER entregado
- [ ] Credenciales de producción documentadas y guardadas de forma segura

---

#### #F13-20 — Verificación final de FASE 13 y del proyecto completo
- **Tipo:** `[INFRA]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F13-19

**Tareas:**
- [ ] Ejecutar suite completa de tests en entorno de staging (copia de producción)
- [ ] Ejecutar prueba de carga con Locust/k6
- [ ] Ejecutar prueba de restauración de backup
- [ ] Demo completa del sistema con el OWNER:
  - Crear venta
  - Crear crédito
  - Pagar cuota
  - Crear reparación
  - Cerrar caja
  - Ver reporte de ventas
- [ ] Sign-off del OWNER
- [ ] PR final mergeado a `main`
- [ ] Tag de versión: `v1.0.0`
- [ ] Comunicar go-live

---

## Resumen del proyecto completo

```
FASE 00 — Fundación            18 issues   ✅
FASE 01 — Auth y Permisos      22 issues   ✅
FASE 02 — Catálogo             24 issues   ✅
FASE 03 — Inventario           20 issues   ✅
FASE 04 — Caja, POS, Ventas    32 issues   ✅
FASE 05 — Créditos y Mora      30 issues   ✅
FASE 06 — Cotizaciones/WA      22 issues   ✅
FASE 07 — Reparaciones         28 issues   ✅
FASE 08 — Servicios de campo   26 issues   ✅
FASE 09 — Garantías/Dev.       18 issues   ✅
FASE 10 — Sublimación          14 issues   ✅
FASE 11 — Software/Web         14 issues   ✅
FASE 12 — Dashboard/Reportes   24 issues   ✅
FASE 13 — Producción           20 issues   ✅
─────────────────────────────────────────
TOTAL                         292 issues
```

---

*Referencia: [REQUIREMENTS.md](../REQUIREMENTS.md) §32 Seguridad, §36 Backups, §37 Despliegue*
*Fase anterior: [FASE 12](FASE-12-dashboard-reportes-notificaciones.md)*
*← Volver al índice: [TASKS.md](../TASKS.md)*
