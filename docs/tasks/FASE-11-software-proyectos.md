# FASE 11 — Proyectos de Software y Publicaciones Web

**Rama:** `feature/fase-11-software`
**Objetivo:** Portafolio de proyectos de software gestionado por el rol SOFTWARE_DEVELOPER. Publicaciones visibles en la web pública. Casos de éxito de clientes.
**Prerrequisito:** FASE 10 completada y mergeada a `develop`.
**Criterio de salida:** SOFTWARE_DEVELOPER puede crear y publicar proyectos. La web pública muestra el portafolio. Solo proyectos PUBLISHED son visibles públicamente.

---

## Progreso

| Completados | Total | Porcentaje |
|---|---|---|
| 0 | 14 | 0% |

---

## Issues

### MODELOS

---

#### #F11-01 — Modelos de proyectos de software con migración
- **Tipo:** `[BE]` `[DB]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** FASE-10 completa

**Tareas:**
- [ ] Crear `apps/api/app/modules/software_projects/domain/models.py`:
  ```
  SoftwareProject:
    id (UUID, PK)
    name (VARCHAR, not null)
    slug (VARCHAR, unique, not null)
    description (TEXT)
    short_description (TEXT)           — para tarjetas (máx. 200 chars)
    status (ENUM): DRAFT/PUBLISHED/ARCHIVED
    client_name (VARCHAR)              — puede ser anónimo ("Cliente confidencial")
    project_url (VARCHAR)              — URL pública si está disponible
    repository_url (VARCHAR)           — privado, solo admin
    year_completed (INTEGER)
    featured (BOOLEAN, default False)  — destacado en portada
    published_at (TIMESTAMPTZ)
    created_by (UUID, FK → User)
    created_at, updated_at (TIMESTAMPTZ)

  ProjectImage:
    id (UUID, PK)
    project_id (UUID, FK → SoftwareProject)
    file_id (UUID, FK → FileObject)
    order (INTEGER)
    caption (TEXT)
    is_cover (BOOLEAN, default False)  — imagen principal del proyecto
    created_at (TIMESTAMPTZ)

  ProjectTechnology:
    id (UUID, PK)
    project_id (UUID, FK → SoftwareProject)
    tech_name (VARCHAR)                — React, FastAPI, PostgreSQL, etc.
    tech_category (ENUM):
      FRONTEND/BACKEND/DATABASE/DEVOPS/MOBILE/OTHER
    created_at (TIMESTAMPTZ)

  ClientSuccessStory:
    id (UUID, PK)
    project_id (UUID, FK → SoftwareProject)
    client_name (VARCHAR, not null)
    client_role (VARCHAR)              — CEO, Gerente, etc.
    client_company (VARCHAR)
    testimonial (TEXT, not null)
    client_avatar_file_id (UUID, FK → FileObject, nullable)
    published (BOOLEAN, default False)
    created_at (TIMESTAMPTZ)
  ```
- [ ] Migración Alembic
- [ ] Slug autogenerado del nombre del proyecto (único)

---

### LÓGICA DE NEGOCIO

---

#### #F11-02 — CRUD de proyectos con control de publicación
- **Tipo:** `[BE]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F11-01

**Tareas:**
- [ ] Crear `SoftwareProjectService`:
  - `create_project(data, user)` → DRAFT (SOFTWARE_DEVELOPER u OWNER)
  - `update_project(id, data, user)` → solo si DRAFT o creador es el mismo
  - `publish_project(id, user)`:
    - Verificar al menos 1 imagen de portada
    - Verificar descripción no vacía
    - DRAFT → PUBLISHED
    - published_at = now()
    - AuditLog
  - `unpublish_project(id, user)` → PUBLISHED → DRAFT
  - `archive_project(id, user)` → ARCHIVED (solo OWNER)
  - `set_featured(id, featured, user)` (solo OWNER)
- [ ] Endpoints:
  - `GET /api/v1/software-projects` — lista (admin: todos; público: solo PUBLISHED)
  - `POST /api/v1/software-projects` — crear (SOFTWARE_DEVELOPER + OWNER)
  - `GET /api/v1/software-projects/{id}` — detalle
  - `GET /api/v1/software-projects/slug/{slug}` — por slug (público)
  - `PUT /api/v1/software-projects/{id}` — editar (SOFTWARE_DEVELOPER + OWNER)
  - `POST /api/v1/software-projects/{id}/publish` — publicar
  - `POST /api/v1/software-projects/{id}/unpublish` — despublicar
  - `POST /api/v1/software-projects/{id}/archive` — archivar (OWNER)
  - `POST /api/v1/software-projects/{id}/featured` — destacar (OWNER)
  - `POST /api/v1/software-projects/{id}/images` — agregar imagen
  - `DELETE /api/v1/software-projects/{id}/images/{img_id}` — eliminar imagen
  - `POST /api/v1/software-projects/{id}/technologies` — agregar tecnología
  - `DELETE /api/v1/software-projects/{id}/technologies/{tech_id}` — eliminar
  - `POST /api/v1/software-projects/{id}/success-stories` — agregar caso de éxito
  - `PUT /api/v1/software-projects/{id}/success-stories/{story_id}/publish` — publicar testimonio

**Definición de terminado:**
- [ ] SOFTWARE_DEVELOPER puede crear y editar proyectos
- [ ] SALES intenta crear proyecto → 403
- [ ] Proyecto DRAFT no visible en endpoint público
- [ ] Proyecto PUBLISHED visible sin autenticación

---

#### #F11-03 — Gestión de imágenes y tecnologías
- **Tipo:** `[BE]`
- **Prioridad:** 🟠 ALTO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F11-02

**Tareas:**
- [ ] Máximo 10 imágenes por proyecto (configurable)
- [ ] Solo 1 imagen puede ser `is_cover=True` (el servicio garantiza unicidad)
- [ ] Reordenamiento de imágenes: `PUT /api/v1/software-projects/{id}/images/reorder`
- [ ] Tecnologías sin duplicados por proyecto (unique constraint en project_id + tech_name)
- [ ] Seed de tecnologías sugeridas comunes para autocompletar en frontend

---

### FRONTEND

---

#### #F11-04 — Panel de gestión de proyectos (admin)
- **Tipo:** `[FE]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F11-02

**Tareas:**
- [ ] `apps/web/app/admin/software/page.tsx` — lista de proyectos:
  - Tarjetas con imagen de portada, nombre, estado, tecnologías
  - Filtros: estado (DRAFT/PUBLISHED/ARCHIVED), destacado
  - Solo visible para SOFTWARE_DEVELOPER y OWNER
- [ ] `apps/web/app/admin/software/nuevo/page.tsx` — formulario:
  - Datos del proyecto (nombre, cliente, año, URLs)
  - Editor de descripción (textarea rico, sin Markdown complejo por ahora)
  - Upload de imágenes (múltiple, reordenable)
  - Agregar tecnologías con chips
  - Vista previa antes de publicar
- [ ] `apps/web/app/admin/software/[id]/page.tsx`:
  - Detalle completo con todas las secciones
  - Gestión de casos de éxito
  - Botón de publicar/despublicar
  - Botón de destacar

---

#### #F11-05 — Dashboard del SOFTWARE_DEVELOPER
- **Tipo:** `[FE]`
- **Prioridad:** 🟠 ALTO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F11-02

**Tareas:**
- [ ] `apps/web/app/admin/dashboard/page.tsx` — variante para SOFTWARE_DEVELOPER:
  - Proyectos publicados (contador)
  - Proyectos en borrador (contador)
  - Casos de éxito publicados (contador)
  - Accesos rápidos: Nuevo proyecto, Ver portafolio público
- [ ] Redirigir automáticamente al dashboard correcto según rol al hacer login

---

#### #F11-06 — Portafolio público (web)
- **Tipo:** `[FE]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F11-02

**Tareas:**
- [ ] `apps/web/app/(public)/proyectos/page.tsx`:
  - Grid de proyectos PUBLISHED (con imagen de portada, nombre, descripción corta, tecnologías)
  - Proyectos `featured=True` destacados al inicio
  - Filtro por tecnología (frontend)
- [ ] `apps/web/app/(public)/proyectos/[slug]/page.tsx`:
  - Galería de imágenes
  - Descripción completa
  - Stack tecnológico con íconos/badges
  - Testimonios publicados
  - Botón "Quiero un proyecto similar" → WhatsApp
- [ ] SSG (Static Site Generation) para páginas de proyectos públicos (mejor SEO)
- [ ] Meta tags: `<title>`, `<description>`, Open Graph para redes sociales

---

#### #F11-07 — Página de inicio (web pública) — sección proyectos
- **Tipo:** `[FE]`
- **Prioridad:** 🟠 ALTO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F11-06

**Tareas:**
- [ ] En `apps/web/app/(public)/page.tsx` agregar sección:
  - "Nuestros trabajos" con los 3 proyectos más recientes `featured=True`
  - Botón "Ver todos" → `/proyectos`
  - Sección de tecnologías que manejamos
- [ ] Sección de testimonios de clientes (ClientSuccessStory publicadas)

---

### SEEDS Y TESTS

---

#### #F11-08 — Seeds de proyectos ficticios
- **Tipo:** `[BE]`
- **Prioridad:** 🟠 ALTO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F11-02

**Tareas:**
- [ ] 3 proyectos PUBLISHED con imágenes ficticias, tecnologías y testimonios
- [ ] 1 proyecto DRAFT (visible solo en admin)
- [ ] 1 proyecto ARCHIVED
- [ ] 2 proyectos marcados como `featured=True`
- [ ] Datos completamente ficticios (nombres de clientes inventados)

---

#### #F11-09 — Tests de proyectos de software
- **Tipo:** `[TEST]`
- **Prioridad:** 🟠 ALTO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F11-02

**Tareas:**
- [ ] `test_software_developer_can_create_project` → 201
- [ ] `test_sales_cannot_create_project` → 403
- [ ] `test_draft_not_visible_in_public_api` — endpoint público no retorna DRAFT
- [ ] `test_published_visible_in_public_api`
- [ ] `test_cannot_publish_without_cover_image` → error descriptivo
- [ ] `test_cannot_publish_without_description` → error descriptivo
- [ ] `test_only_owner_can_archive`
- [ ] `test_slug_unique` → 409 si slug duplicado

---

#### #F11-10 — Documentar módulo de software
- **Tipo:** `[DOCS]`
- **Prioridad:** 🟡 MEDIO
- **Estado:** ⬜ Pendiente

**Tareas:**
- [ ] Documentar el flujo de publicación y los requisitos mínimos
- [ ] Documentar el rol SOFTWARE_DEVELOPER y sus capacidades
- [ ] Actualizar `docs/permissions.md` con permisos de este módulo

---

#### #F11-11 — SEO básico para portafolio
- **Tipo:** `[FE]`
- **Prioridad:** 🟡 MEDIO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F11-06

**Tareas:**
- [ ] `sitemap.xml` generado dinámicamente incluyendo slugs de proyectos PUBLISHED
- [ ] `robots.txt` configurado
- [ ] Meta description dinámica por proyecto
- [ ] Structured data básico (JSON-LD) para proyectos

---

#### #F11-12 — Integrar proyectos en búsqueda global
- **Tipo:** `[BE]`
- **Prioridad:** 🟡 MEDIO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F11-02

**Tareas:**
- [ ] Agregar SoftwareProject al módulo de búsqueda global (nombre, cliente, tecnologías)
- [ ] Solo admins buscan proyectos DRAFT; público busca solo PUBLISHED

---

#### #F11-13 — Casos de éxito: gestión completa
- **Tipo:** `[BE]` `[FE]`
- **Prioridad:** 🟡 MEDIO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F11-02

**Tareas:**
- [ ] CRUD completo de ClientSuccessStory
- [ ] Solo testimonios con `published=True` visibles en web pública
- [ ] Upload de avatar del cliente (FileObject)
- [ ] Frontend admin: formulario de agregar testimonio al proyecto
- [ ] Frontend público: sección de testimonios en página del proyecto

---

#### #F11-14 — Verificación final de FASE 11
- **Tipo:** `[INFRA]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** Todos los anteriores

**Checklist de salida de fase:**
- [ ] SOFTWARE_DEVELOPER crea y publica proyectos sin errores
- [ ] SALES no puede acceder al módulo → 403
- [ ] Proyectos DRAFT no visibles en la web pública
- [ ] Portafolio público muestra proyectos con SEO básico
- [ ] Testimonios publicados visibles en la página del proyecto
- [ ] Dashboard del SW_DEV muestra KPIs relevantes
- [ ] CI verde
- [ ] PR mergeado a `develop`

---

*Referencia: [REQUIREMENTS.md](../REQUIREMENTS.md) §21 Desarrollo de Software*
*Fase anterior: [FASE 10](FASE-10-sublimacion.md) | Siguiente fase: [FASE 12](FASE-12-dashboard-reportes-notificaciones.md)*
