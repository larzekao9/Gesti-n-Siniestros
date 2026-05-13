# Gestión Siniestros

Plataforma SaaS multi-tenant para aseguradoras: gestión de siniestros vehiculares con detección de fraude mediante IA.

## Stack

| Capa | Tecnologías |
|------|------------|
| **Frontend** | Next.js 14 · React 18 · TypeScript · Shadcn/ui · Tailwind · Zustand · TanStack Query |
| **Backend** | FastAPI · Python 3.12 · SQLAlchemy · Pydantic v2 · Celery |
| **Auth** | JWT + MFA (TOTP) · Roles: admin / supervisor / analista |
| **Bases de datos** | PostgreSQL · Redis · Elasticsearch · Pinecone |
| **IA/ML** | LangChain · OpenAI · XGBoost · SHAP |
| **Infra** | Docker · GitHub Actions · AWS ECS Fargate · RDS · S3 · CloudFront |

## Arquitectura

```
Navegador
    │
    ▼
Next.js 14  :3000
    │  REST
    ▼
FastAPI     :8000
    │
    ├── PostgreSQL  :5432  (datos principales, por tenant)
    ├── Redis       :6379  (caché + broker Celery)
    └── Elasticsearch :9200 (búsqueda full-text)
              │
         Celery Worker
              │
         IA/ML (XGBoost · LangChain · SHAP · Pinecone)
```

## Inicio rápido

### Requisitos
- Docker + Docker Compose
- Python 3.12 (solo para desarrollo local del backend)
- Node.js 20+

### Levantar el entorno

```bash
cp .env.example .env        # configurar variables
docker compose up --build   # levanta los 6 servicios
```

El override `docker-compose.override.yml` se aplica automáticamente en desarrollo con hot reload.

### Cargar datos de prueba

```bash
docker compose exec backend python scripts/seed.py
```

Credenciales generadas:

| Organización | Email | Contraseña | Rol |
|---|---|---|---|
| `demo` | `admin@demo.com` | `Admin123!` | Admin |
| `demo` | `supervisor@demo.com` | `Admin123!` | Supervisor |
| `demo` | `analista@demo.com` | `Admin123!` | Analista |

### URLs

| Servicio | URL |
|---|---|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| Swagger docs | http://localhost:8000/docs |

## Desarrollo local (sin Docker)

**Backend:**
```bash
cd backend
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

**Tests:**
```bash
# Backend (11 tests)
cd backend && pytest tests/ -v

# Frontend (71 tests)
cd frontend && npm test
```

O con Makefile:
```bash
make test-backend
make up / make down / make logs
```

## Sprints

| Sprint | Feature | Estado |
|--------|---------|--------|
| 1 | Auth + Multi-tenant (JWT, MFA, roles) | ✅ Completo |
| 2 | CRUD core (asegurados, pólizas, vehículos) | 🔜 En curso |
| 3 | Workflow siniestros + evidencias S3 | ⏳ |
| 4 | Búsqueda Elasticsearch | ⏳ |
| 5 | Dashboard + reportes PDF/Excel | ⏳ |
| 6 | Fraud detection (XGBoost + SHAP + LangChain) | ⏳ |
| 7 | Vector search + duplicados (Pinecone) | ⏳ |
| 8 | Deploy producción AWS | ⏳ |

## Estructura del proyecto

```
├── backend/
│   ├── app/
│   │   ├── core/        # config, security, database, celery
│   │   ├── models/      # Tenant, User, RefreshToken
│   │   ├── schemas/     # Pydantic schemas
│   │   ├── routers/     # auth (6 endpoints)
│   │   └── middleware/  # tenant isolation
│   ├── alembic/         # migraciones
│   ├── tests/           # pytest + asyncio
│   └── scripts/         # seed.py
├── frontend/
│   ├── app/
│   │   ├── (auth)/      # login, register, mfa
│   │   └── (dashboard)/ # panel principal
│   ├── components/
│   │   ├── auth/        # formularios de autenticación
│   │   └── ui/          # componentes Shadcn/ui
│   └── lib/
│       ├── api/          # Axios client + auth endpoints
│       ├── stores/       # Zustand auth store
│       └── validations/  # Zod schemas
├── docker-compose.yml
├── docker-compose.override.yml   # dev: hot reload
├── Makefile
└── .github/workflows/ci.yml
```

## Variables de entorno

Ver `.env.example` para la lista completa. Las variables críticas:

```env
DATABASE_URL=postgresql+asyncpg://...
SECRET_KEY=...                    # JWT signing key
REDIS_URL=redis://redis:6379/0
NEXT_PUBLIC_API_URL=http://localhost:8000
```
