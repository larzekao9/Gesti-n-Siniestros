# Gestión Siniestros

Plataforma SaaS **multi-tenant** para aseguradoras: gestión integral de siniestros
vehiculares, desde que el asegurado lo reporta por la **app móvil** hasta que el
expediente se aprueba/rechaza en el **panel web**, con **análisis inteligente** (IA)
de inconsistencias, duplicados, score de fraude y daño por foto.

Tiene **dos frentes de usuario**:
- **Panel web** (Next.js) — personal interno: admin, supervisor, analista.
- **App móvil** (React Native + Expo) — el asegurado: reporta el siniestro, sube
  evidencias con cámara/GPS y sigue el estado de su reclamo. Ver
  **[mobile/README.md](./mobile/README.md)**.

> **Todo el backend + web se maneja con Docker Compose.** No hace falta instalar Python,
> Node ni las bases de datos en la máquina: los 6 servicios corren en contenedores. Funciona
> igual en **Windows y macOS** (solo se necesita Docker Desktop). La **app móvil** es lo único
> que se buildea fuera de Docker (toolchain nativo) — ver [mobile/README.md](./mobile/README.md).

## Stack

| Capa | Tecnologías |
|------|------------|
| **Frontend (web)** | Next.js 14 (App Router) · React · TypeScript · Tailwind · Zustand · TanStack Query · Axios (refresh rotativo) |
| **App móvil** | React Native · Expo SDK 54 · expo-router · NativeWind 4 · expo-camera/location/notifications |
| **Backend** | FastAPI · Python 3.12 (async) · SQLAlchemy 2.0 · Pydantic v2 · Celery |
| **Auth** | JWT + refresh rotativo + MFA (TOTP) · roles: admin / supervisor / analista · multi-tenant por `tenant_id` |
| **Bases de datos** | PostgreSQL 16 (**pgvector**) · Redis 7 (broker Celery) · Elasticsearch 8 (levantado, full-text aún no indexado) |
| **IA/ML** | OpenAI (chat · vision · embeddings) · **pgvector** para duplicados (ADR-011) · fraud score **heurístico explicable** (ADR-010) · on-device móvil: ML Kit (OCR) + TFLite/MobileNet |
| **Infra** | Docker Compose · S3 (evidencias) · build móvil local/EAS |

> **Nota de arquitectura:** el plan original (Pinecone, XGBoost+SHAP) fue **reemplazado**
> por `pgvector` y una heurística explicable (ver ADR-010/011 en `Context.md`). No se usan
> Pinecone, XGBoost ni SHAP.

## Arquitectura

```
   App móvil (Expo)                 Panel web (Next.js :3000)
   asegurado                        admin / supervisor / analista
        │                                   │
        └──────────────┬────────────────────┘
                       │  REST (JSON)
                       ▼
              FastAPI  :8000  (async, multi-tenant)
                       │
     ┌─────────────────┼──────────────────────┐
     ▼                 ▼                       ▼
 PostgreSQL 16     Redis 7              Elasticsearch 8
 (datos + pgvector) (broker Celery)    (full-text, pendiente de índice)
                       │
                  Celery Worker
                       │
                  IA (OpenAI · pgvector · heurística de fraude)
```

## Inicio rápido (Docker)

Único requisito: **Docker + Docker Compose** (Docker Desktop en Windows/macOS). Todos los
comandos son los mismos en cualquier sistema.

```bash
# 1) Crear el .env (copia del ejemplo)
cp .env.example .env          # o: make setup

# 2) Levantar los 6 servicios (postgres, redis, elasticsearch, backend, celery-worker, frontend)
docker compose up --build     # o: make up   (en background)

# 3) Migraciones + datos de prueba
make migrate                  # o: docker compose exec backend alembic upgrade head
make seed                     # o: docker compose exec backend python scripts/seed.py
```

El override `docker-compose.override.yml` se aplica solo en desarrollo (hot reload del
backend y el frontend dentro de los contenedores: editás el código en tu máquina y se
recarga solo).

> ⚠️ Si cambiás la imagen de Postgres o el esquema y la BD queda inconsistente, reseteá el
> volumen: `make down-volumes && make up && make migrate && make seed`.

Credenciales generadas por el seed (organización / **slug** `demo`):

| Slug (tenant) | Email | Contraseña | Rol |
|---|---|---|---|
| `demo` | `admin@demo.com` | `Admin123!` | Admin |
| `demo` | `supervisor@demo.com` | `Admin123!` | Supervisor |
| `demo` | `analista@demo.com` | `Admin123!` | Analista |
| `demo` | `analista2@demo.com` | `Admin123!` | Analista |

> El login web pide **email + contraseña + slug del tenant** (`demo`). El seed también
> crea asegurados, pólizas y vehículos de ejemplo.

### URLs

| Servicio | URL |
|---|---|
| Frontend (panel web) | http://localhost:3000 |
| Backend API | http://localhost:8000/api |
| Swagger docs | http://localhost:8000/docs |

## Comandos útiles (Makefile)

```bash
make up / make down           # levantar / bajar (preserva la BD)
make down-volumes             # bajar y borrar volúmenes (reset total de la BD)
make logs / make logs-backend # seguir logs
make ps                       # estado de los contenedores
make migrate / make seed      # migraciones / datos de prueba
make test-backend             # tests del backend dentro del contenedor
```

## App móvil (canal del asegurado)

La app es un **proyecto independiente** en [`mobile/`](./mobile) y **no** corre en Docker
(necesita el toolchain nativo de Android/iOS); consume la misma API del backend. Para
invitar a un asegurado, probar la app y **buildear el APK** —incluye la nota importante de
que **la ruta del proyecto no debe tener espacios**, con comandos para **Windows y macOS**—
ver **[mobile/README.md](./mobile/README.md)**.

Flujo de prueba end-to-end (resumen): el analista invita al asegurado desde el web →
el asegurado activa su cuenta en la app → reporta un siniestro con fotos y GPS → el
analista lo toma/formaliza en el web → el asegurado recibe push y sigue el estado.

## Tests

```bash
# Backend (135 tests · pytest) — dentro del contenedor:
make test-backend             # o: docker compose exec backend pytest tests/ -v

# Frontend (77 tests · Vitest):
cd frontend && npm install && npm test

# Móvil (32 tests · jest-expo):
cd mobile && npm install && npm test
```

## Estado por ciclos

| Ciclo | Feature | Estado |
|--------|---------|--------|
| 1 | Auth + Multi-tenant (JWT, MFA, roles) | ✅ |
| 2 | CRUD catálogos (usuarios, asegurados, pólizas, vehículos) + reset/cambio de contraseña | ✅ |
| 3 | Núcleo del expediente: solicitudes, formalización, observaciones, terceros, workflow | ✅ |
| 4 | Evidencias (S3) + documentación + información de tránsito | ✅ |
| 5 | Aprobación/supervisión: escalamiento, decisión, asignación, notificaciones | ✅ |
| 6 | Dashboard + reportes (PDF/Excel) + bitácora de auditoría | ✅ |
| 7 | Canal del asegurado: **app móvil** (CU-01..CU-08) | ✅ |
| 8 | Análisis inteligente: inconsistencias, duplicados (pgvector), fraude (heurística), visión/OCR/clasificación móvil | ✅ |

> Detalle de los 36 casos de uso en **[CasosDeUso.md](./CasosDeUso.md)**; arquitectura,
> modelo de datos, ADRs y deuda técnica en **[Context.md](./Context.md)**.

## Estructura del proyecto

```
├── backend/                  # FastAPI (async, en capas: routers → services → models)
│   ├── app/
│   │   ├── core/             # config, security, database, celery
│   │   ├── models/           # SQLAlchemy 2.0 (tenants, claims, evidences, ai_analyses, …)
│   │   ├── schemas/          # Pydantic v2
│   │   ├── routers/          # auth, users, policyholders, policies, vehicles, claims,
│   │   │                     #   claim_requests, evidences, workflow, analytics, reports,
│   │   │                     #   ai_analyses, insured_auth, me, notifications, audit_logs, …
│   │   ├── services/         # ★ lógica de negocio (reusable desde routers y Celery)
│   │   ├── tasks/            # Celery (procesamiento de evidencias, IA)
│   │   └── middleware/       # aislamiento por tenant
│   ├── alembic/              # migraciones
│   ├── tests/                # pytest (135 tests)
│   └── scripts/              # seed.py
├── frontend/                 # Next.js 14 (panel web interno)
│   ├── app/(auth)/           # login, register, mfa, recuperación de contraseña
│   ├── app/(dashboard)/      # expedientes, solicitudes, catálogos, reportes, auditoría, IA
│   ├── components/           # ui (Shadcn) + auth + claims + dashboard + …
│   ├── lib/                  # api (axios+refresh), stores (Zustand), validations (Zod)
│   └── __tests__/            # Vitest (77 tests)
├── mobile/                   # React Native + Expo (app del asegurado) — ver mobile/README.md
├── docker-compose.yml        # postgres · redis · elasticsearch · backend · celery-worker · frontend
├── docker-compose.override.yml   # dev: hot reload
├── Makefile
└── .github/workflows/        # CI
```

## Variables de entorno

Ver [`.env.example`](./.env.example) para la lista completa. Las críticas:

```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/siniestros
SECRET_KEY=...                          # JWT signing key (openssl rand -hex 32)
REDIS_URL=redis://redis:6379/0
NEXT_PUBLIC_API_URL=http://localhost:8000/api
OPENAI_API_KEY=                         # solo backend (la web y la app NUNCA la conocen)
# S3 (evidencias): AWS_S3_BUCKET, AWS_REGION, AWS_S3_ENDPOINT, AWS_ACCESS_KEY_ID/SECRET
```

## Documentación

| Documento | Para qué |
|---|---|
| [mobile/README.md](./mobile/README.md) | Correr y **buildear la app móvil** (Windows/macOS, requisito de ruta sin espacios) |
| [Context.md](./Context.md) | Arquitectura, modelo de datos, ADRs, planificación por ciclos, deuda técnica |
| [CasosDeUso.md](./CasosDeUso.md) | Especificación detallada de los 36 casos de uso |
| [GUIA_DESPLIEGUE_AWS.md](./GUIA_DESPLIEGUE_AWS.md) | Despliegue en AWS |
| [GUIA_DEMO_DEFENSA.md](./GUIA_DEMO_DEFENSA.md) | Guion de la demo / defensa |
</content>
