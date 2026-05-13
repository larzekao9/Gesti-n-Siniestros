# Progreso del Proyecto — Gestión de Siniestros

## Estado General
**Semana actual:** 1 de 8  
**Sprint actual:** 2 — CRUD Core Models  
**Último sprint cerrado:** Sprint 1 ✅

---

## Sprints

| Sprint | Feature | Estado | Notas |
|--------|---------|--------|-------|
| **1** | Auth + Multi-tenant | ✅ Completo | JWT, MFA, roles, 11 tests, multi-tenant isolation |
| **2** | CRUD Core Models | 🔜 Siguiente | Asegurados, pólizas, vehículos |
| **3** | Workflow siniestros + evidencias S3 | ⏳ Pendiente | |
| **4** | Búsqueda Elasticsearch | ⏳ Pendiente | |
| **5** | Dashboard + reportes PDF/Excel | ⏳ Pendiente | |
| **6** | Fraud detection (XGBoost + SHAP + LangChain) | ⏳ Pendiente | |
| **7** | Vector search + duplicados (Pinecone) | ⏳ Pendiente | |
| **8** | Deploy producción AWS | ⏳ Pendiente | |

---

## Sprint 1 — Detalle de lo entregado ✅

### Backend (`backend/`)
- **Modelos SQLAlchemy:** `Tenant`, `User` (roles: admin/supervisor/analyst), `RefreshToken`
- **Auth endpoints (6):** `POST /api/auth/register`, `/login`, `/refresh`, `/logout`, `/mfa/setup`, `/mfa/verify`
- **Seguridad:** JWT (python-jose), bcrypt (passlib), TOTP/MFA (pyotp), rate limiting (slowapi)
- **Multi-tenant:** `TenantMixin` en todos los modelos, isolation verificada en cada query
- **Alembic:** configurado para migraciones async
- **Tests:** 11 tests (pytest-asyncio + SQLite in-memory), incluyendo cross-tenant isolation
- **Celery:** instancia base configurada con Redis broker

### Frontend (`frontend/`)
- **Next.js 14** App Router + TypeScript strict, sin errores `tsc --noEmit`
- **Páginas auth:** Login, Register, MFA Setup, MFA Verify
- **Zustand store:** auth persistido en localStorage, escribe cookie para middleware server-side
- **Axios client:** interceptor JWT + refresh silencioso con cola de reintentos
- **middleware.ts:** protección de rutas `/dashboard/*`, redirect según sesión
- **Componentes:** LoginForm, RegisterForm, MFASetupCard, MFAVerifyForm + Shadcn/ui base
- **Tests:** 71 tests (Vitest + Testing Library), 0 fallos

### Infra
- **`docker-compose.yml`:** 6 servicios con healthchecks (postgres, redis, elasticsearch, backend, celery-worker, frontend)
- **Dockerfiles:** multi-stage para backend y frontend (imágenes optimizadas)
- **`docker-compose.override.yml`:** hot reload automático en desarrollo
- **`.github/workflows/ci.yml`:** lint + tests + build check en cada PR
- **`Makefile`:** `make up/down/logs/migrate/test-backend/venv`

---

## Estructura actual del proyecto

```
Gestión Siniestros/
  backend/
    app/
      core/       → config, security, database, celery_app
      models/     → base, tenant, user, refresh_token
      schemas/    → auth
      routers/    → auth (6 endpoints)
      middleware/ → tenant
      dependencies.py
    tests/        → conftest, test_auth (11 tests)
    alembic/
    main.py · requirements.txt · Dockerfile · pytest.ini
  frontend/
    app/
      (auth)/     → login, register, mfa/setup, mfa/verify
      (dashboard)/→ layout con sidebar, dashboard placeholder
    components/
      auth/       → LoginForm, RegisterForm, MFASetupCard, MFAVerifyForm
      ui/         → button, input, label, card
    lib/
      api/        → client.ts (Axios), auth.ts
      stores/     → authStore.ts (Zustand)
      validations/→ auth.ts (Zod)
    types/auth.ts · middleware.ts · providers.tsx · Dockerfile
  docker-compose.yml · docker-compose.override.yml
  Makefile · .github/workflows/ci.yml · .env.example · .gitignore
```

---

## Nota importante — Python

El proyecto requiere **Python 3.12** (no 3.14).  
En macOS con Homebrew: `/opt/homebrew/bin/python3.12`

```bash
make venv                          # crea backend/.venv con Python 3.12
source backend/.venv/bin/activate
cd backend && pytest tests/ -v     # corre los 11 tests
```

---

## Próximo paso — Sprint 2

**Feature:** CRUD Core Models  
**Scope:**
- Backend: modelos + endpoints CRUD para `Policyholder`, `Policy`, `Vehicle` (15 endpoints con paginación y filtros)
- Frontend: DataTable reutilizable, formularios con Zod, modales de confirmación
- Tests: cobertura >80% backend, >60% frontend
