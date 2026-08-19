# TASKS — INVERSIONES HASBUN ERP
## Índice Maestro de Fases e Issues

**Proyecto:** Sistema Empresarial ERP + POS + E-Commerce + Servicios
**Repositorio:** hasbun/
**Metodología:** Una fase a la vez. No avanzar a la siguiente hasta que la actual pase CI, tests y documentación.

---

## Estado General

| Fase | Nombre | Issues | Estado | Rama Git |
|---|---|---|---|---|
| [FASE 00](tasks/FASE-00-fundacion.md) | Fundación y Arquitectura | 18 | ✅ Completado | `feature/fase-00-fundacion` |
| [FASE 01](tasks/FASE-01-auth.md) | Auth, Usuarios y Permisos | 22 | 🔵 En progreso (10/22) | `feature/fase-01-auth` |
| [FASE 02](tasks/FASE-02-catalogo.md) | Catálogo de Productos | 24 | ⬜ Pendiente | `feature/fase-02-catalogo` |
| [FASE 03](tasks/FASE-03-inventario-compras.md) | Inventario y Compras | 20 | ⬜ Pendiente | `feature/fase-03-inventario` |
| [FASE 04](tasks/FASE-04-caja-pos-ventas.md) | Caja, POS y Ventas | 32 | ⬜ Pendiente | `feature/fase-04-ventas` |
| [FASE 05](tasks/FASE-05-creditos-cuotas-mora.md) | Créditos, Cuotas y Mora | 30 | ⬜ Pendiente | `feature/fase-05-creditos` |
| [FASE 06](tasks/FASE-06-cotizaciones-whatsapp.md) | Cotizaciones y WhatsApp | 22 | ⬜ Pendiente | `feature/fase-06-cotizaciones` |
| [FASE 07](tasks/FASE-07-reparaciones.md) | Reparaciones | 28 | ⬜ Pendiente | `feature/fase-07-reparaciones` |
| [FASE 08](tasks/FASE-08-mantenimientos-instalaciones-envios.md) | Mantenimientos, Instalaciones y Envíos | 26 | ⬜ Pendiente | `feature/fase-08-servicios` |
| [FASE 09](tasks/FASE-09-garantias-devoluciones.md) | Garantías y Devoluciones | 18 | ⬜ Pendiente | `feature/fase-09-garantias` |
| [FASE 10](tasks/FASE-10-sublimacion.md) | Sublimación y Personalización | 14 | ⬜ Pendiente | `feature/fase-10-sublimacion` |
| [FASE 11](tasks/FASE-11-software-proyectos.md) | Proyectos de Software | 14 | ⬜ Pendiente | `feature/fase-11-software` |
| [FASE 12](tasks/FASE-12-dashboard-reportes-notificaciones.md) | Dashboard, Reportes y Notificaciones | 24 | ⬜ Pendiente | `feature/fase-12-dashboard` |
| [FASE 13](tasks/FASE-13-produccion-hardening.md) | Producción y Hardening | 20 | ⬜ Pendiente | `feature/fase-13-produccion` |

---

## Convenciones

### Etiquetas de estado por issue
| Símbolo | Significado |
|---|---|
| ⬜ | Pendiente |
| 🔵 | En progreso |
| ✅ | Completado |
| 🔴 | Bloqueado |
| ⏭️ | Pospuesto |

### Etiquetas de tipo
| Etiqueta | Descripción |
|---|---|
| `[BE]` | Backend (FastAPI / Python) |
| `[FE]` | Frontend (Next.js / TypeScript) |
| `[DB]` | Base de datos / Migración Alembic |
| `[TEST]` | Tests automatizados |
| `[INFRA]` | Infraestructura / Docker / CI |
| `[DOCS]` | Documentación |
| `[SEC]` | Seguridad |
| `[TASK]` | Tarea Celery (worker) |

### Etiquetas de prioridad
| Etiqueta | Descripción |
|---|---|
| `🔴 CRÍTICO` | Bloquea otras tareas o tiene impacto financiero |
| `🟠 ALTO` | Importante para el flujo principal |
| `🟡 MEDIO` | Necesario pero no bloqueante |
| `🟢 BAJO` | Mejora o detalle |

---

## Regla de avance entre fases

```
✅ Todos los issues de la fase completados
✅ CI pasa (lint + type check + tests)
✅ Migraciones ejecutadas sin errores
✅ Endpoints verificados manualmente
✅ Permisos verificados (403 en los correctos)
✅ Transacciones verificadas
✅ Documentación actualizada
─────────────────────────────────────────
→ Solo entonces: merge a develop + iniciar siguiente fase
```

---

## Ramas Git

```
main        → producción (solo merge desde develop, requiere PR + aprobación)
develop     → integración (requiere PR + CI verde)
feature/*   → desarrollo de cada fase o issue
bugfix/*    → corrección de bugs encontrados en testing
hotfix/*    → corrección urgente sobre main
```

---

*Última actualización: 2026-08-17*
*Referencia: [REQUIREMENTS.md](REQUIREMENTS.md)*
