# TASKS â€” INVERSIONES HASBUN ERP
## Ãndice Maestro de Fases e Issues

**Proyecto:** Sistema Empresarial ERP + POS + E-Commerce + Servicios
**Repositorio:** hasbun/
**MetodologÃ­a:** Una fase a la vez. No avanzar a la siguiente hasta que la actual pase CI, tests y documentaciÃ³n.

---

## Estado General

| Fase | Nombre | Issues | Estado | Rama Git |
|---|---|---|---|---|
| [FASE 00](tasks/FASE-00-fundacion.md) | FundaciÃ³n y Arquitectura | 18 | âœ… Completado | `feature/fase-00-fundacion` |
| [FASE 01](tasks/FASE-01-auth.md) | Auth, Usuarios y Permisos | 22 | âœ… Completada | `develop` |
| [FASE 02](tasks/FASE-02-catalogo.md) | CatÃ¡logo de Productos | 24 | âœ… Completada (24/24, verificaciÃ³n backend hecha 2026-08-20) | `feature/fase-02-catalogo` |
| [FASE 03](tasks/FASE-03-inventario-compras.md) | Inventario y Compras | 20 | âœ… Completada (20/20, verificaciÃ³n 2026-08-21: 72/72 tests, alembic check, seeds 5/21/91) | `feature/fase-03-inventario` |
| [FASE 04](tasks/FASE-04-caja-pos-ventas.md) | Caja, POS y Ventas | 26 | âœ… Completada (26/26, verificaciÃ³n 2026-08-21: 78/78 tests, alembic check, next build) | `feature/fase-04-ventas` |
| [FASE 05](tasks/FASE-05-creditos-cuotas-mora.md) | CrÃ©ditos, Cuotas y Mora | 30 | âœ… Completada (30/30, verificaciÃ³n 2026-08-24: 112/112 tests, ruff+mypy, seeds 6/6/3, next build; PR a develop pendiente) | `feature/fase-05-creditos` |
| [FASE 06](tasks/FASE-06-cotizaciones-whatsapp.md) | Cotizaciones y WhatsApp | 22 | ✅ Completada (22/22, verificación 2026-08-24: pytest/ruff/mypy limpios, migración+seeds en BD dev, panel WhatsApp y vistas de cotizaciones, next build; PR a develop pendiente) | `feature/fase-06-cotizaciones` |
| [FASE 07](tasks/FASE-07-reparaciones.md) | Reparaciones | 28 | â¬œ Pendiente | `feature/fase-07-reparaciones` |
| [FASE 08](tasks/FASE-08-mantenimientos-instalaciones-envios.md) | Mantenimientos, Instalaciones y EnvÃ­os | 26 | â¬œ Pendiente | `feature/fase-08-servicios` |
| [FASE 09](tasks/FASE-09-garantias-devoluciones.md) | GarantÃ­as y Devoluciones | 18 | â¬œ Pendiente | `feature/fase-09-garantias` |
| [FASE 10](tasks/FASE-10-sublimacion.md) | SublimaciÃ³n y PersonalizaciÃ³n | 14 | â¬œ Pendiente | `feature/fase-10-sublimacion` |
| [FASE 11](tasks/FASE-11-software-proyectos.md) | Proyectos de Software | 14 | â¬œ Pendiente | `feature/fase-11-software` |
| [FASE 12](tasks/FASE-12-dashboard-reportes-notificaciones.md) | Dashboard, Reportes y Notificaciones | 24 | â¬œ Pendiente | `feature/fase-12-dashboard` |
| [FASE 13](tasks/FASE-13-produccion-hardening.md) | ProducciÃ³n y Hardening | 20 | â¬œ Pendiente | `feature/fase-13-produccion` |

---

## Convenciones

### Etiquetas de estado por issue
| SÃ­mbolo | Significado |
|---|---|
| â¬œ | Pendiente |
| ðŸ”µ | En progreso |
| âœ… | Completado |
| ðŸ”´ | Bloqueado |
| â­ï¸ | Pospuesto |

### Etiquetas de tipo
| Etiqueta | DescripciÃ³n |
|---|---|
| `[BE]` | Backend (FastAPI / Python) |
| `[FE]` | Frontend (Next.js / TypeScript) |
| `[DB]` | Base de datos / MigraciÃ³n Alembic |
| `[TEST]` | Tests automatizados |
| `[INFRA]` | Infraestructura / Docker / CI |
| `[DOCS]` | DocumentaciÃ³n |
| `[SEC]` | Seguridad |
| `[TASK]` | Tarea Celery (worker) |

### Etiquetas de prioridad
| Etiqueta | DescripciÃ³n |
|---|---|
| `ðŸ”´ CRÃTICO` | Bloquea otras tareas o tiene impacto financiero |
| `ðŸŸ  ALTO` | Importante para el flujo principal |
| `ðŸŸ¡ MEDIO` | Necesario pero no bloqueante |
| `ðŸŸ¢ BAJO` | Mejora o detalle |

---

## Regla de avance entre fases

```
âœ… Todos los issues de la fase completados
âœ… CI pasa (lint + type check + tests)
âœ… Migraciones ejecutadas sin errores
âœ… Endpoints verificados manualmente
âœ… Permisos verificados (403 en los correctos)
âœ… Transacciones verificadas
âœ… DocumentaciÃ³n actualizada
â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
â†’ Solo entonces: merge a develop + iniciar siguiente fase
```

---

## Ramas Git

```
main        â†’ producciÃ³n (solo merge desde develop, requiere PR + aprobaciÃ³n)
develop     â†’ integraciÃ³n (requiere PR + CI verde)
feature/*   â†’ desarrollo de cada fase o issue
bugfix/*    â†’ correcciÃ³n de bugs encontrados en testing
hotfix/*    â†’ correcciÃ³n urgente sobre main
```

---

*Ãšltima actualizaciÃ³n: 2026-08-21*
*Referencia: [REQUIREMENTS.md](REQUIREMENTS.md)*
