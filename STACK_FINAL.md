# Stack Tecnológico Final
## Plataforma Inteligente de Gestión de Siniestros

---

## 🎯 Objetivo del Proyecto

Desarrollar una **plataforma SaaS multi-tenant** que permita a aseguradoras de automóviles:

- 📋 **Centralizar expedientes digitales** de siniestros con documentación multimedia
- 👥 **Gestionar usuarios y roles** con autenticación segura (JWT + MFA)
- 🔍 **Buscar y filtrar** reclamos por múltiples criterios
- 🤖 **Detectar fraudes** usando inteligencia artificial
- ⚠️ **Identificar inconsistencias** entre declaraciones y evidencias
- 🔄 **Encontrar reclamos duplicados** mediante búsqueda semántica
- 📊 **Generar reportes y análisis** con dashboards interactivos
- 🏢 **Aislar datos por aseguradora** (database-per-tenant)

**Valor agregado:** IA integrada que automatiza el análisis y detección de fraudes, reduciendo tiempo de procesamiento y mejorando precisión.

---

## 📐 Alcance del Proyecto

### **Incluido:**

✅ **Módulo de Usuarios**
- Autenticación JWT
- Multi-factor authentication (TOTP)
- Roles: Admin, Supervisor, Analista
- Permisos granulares

✅ **Módulo de Datos**
- Registro de asegurados
- Registro de pólizas vehiculares
- Registro de vehículos asegurados

✅ **Módulo de Siniestros**
- Crear y editar expedientes
- Estado workflow (Registrado → En Revisión → Aprobado/Rechazado → Cerrado)
- Registro de observaciones técnicas
- Solicitud de documentación adicional

✅ **Módulo de Evidencias**
- Carga de fotos y videos
- Carga de facturas e informes técnicos
- Gestión multimedia con almacenamiento en S3
- Procesamiento async de archivos

✅ **Módulo de Análisis Inteligente (IA)**
- Detección de inconsistencias (LLM analysis)
- Detección de fraudes (ML model XGBoost)
- Detección de reclamos duplicados (vector similarity)
- Puntaje de riesgo con explicación (SHAP)

✅ **Módulo de Búsqueda**
- Full-text search en expedientes (Elasticsearch)
- Búsqueda semántica (Pinecone vectors)
- Filtros avanzados

✅ **Módulo de Reportes**
- Dashboard gerencial con KPIs
- Reportes exportables (PDF/Excel)
- Log de auditoría completo
- Trazabilidad de acciones

✅ **Módulo de Configuración de Tenant**
- Gestión de suscripción
- Onboarding de usuarios
- Configuración personalizable
- Integración con fuentes externas

### **No Incluido (Fuera de Alcance):**

❌ Portal para asegurados (solo para personal interno)  
❌ Procesamiento de pagos (sin integración bancaria)  
❌ Gestión de pólizas (solo lectura)  
❌ Mobile app nativa (responsive web es suficiente)  
❌ Videollamadas en tiempo real  
❌ Integración con sistemas legacy (futura)  

---

## 📌 Objetivo del Stack

Crear una plataforma **SaaS escalable, moderna y optimizada para IA** que permita a aseguradoras gestionar siniestros de automóviles con:

✅ **Alto rendimiento** → APIs rápidas y frontend responsivo  
✅ **IA integrada** → Detección de fraude, inconsistencias, duplicados  
✅ **Type-safety** → TypeScript en frontend para menos errores  
✅ **Escalabilidad** → Fácil de crecer sin refactorización mayor  
✅ **Developer Experience** → Herramientas modernas y documentación automática  

---

## 🏗️ Arquitectura General

```
┌─────────────────────────────────────────────────────┐
│                  CLIENTE (Navegador)                │
└────────────────────┬────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────┐
│  FRONTEND: Next.js 14 + React + TypeScript + Vite  │
│  (http://localhost:3000)                            │
│                                                      │
│  ├─ Componentes: Shadcn/ui + Tailwind CSS          │
│  ├─ State: Zustand + TanStack Query                 │
│  ├─ Forms: React Hook Form + Zod                    │
│  └─ HTTP: Axios con JWT interceptors               │
└────────────────────┬────────────────────────────────┘
                     │ (REST API)
                     ↓
┌─────────────────────────────────────────────────────┐
│   BACKEND: FastAPI + Python 3.12                    │
│   (http://localhost:8000)                           │
│                                                      │
│   ├─ API: FastAPI (async/await)                     │
│   ├─ ORM: SQLAlchemy                                │
│   ├─ Validación: Pydantic + Zod                     │
│   ├─ Auth: JWT + MFA (TOTP)                         │
│   ├─ Tasks: Celery + Redis                          │
│   └─ Docs: Swagger (auto-generado)                  │
└────────────────────┬────────────────────────────────┘
                     │
         ┌───────────┼───────────┐
         ↓           ↓           ↓
    ┌────────┐  ┌────────┐  ┌──────────┐
    │PostgreS│  │ Redis  │  │Elastic   │
    │   QL   │  │ Cache  │  │search    │
    └────────┘  └────────┘  └──────────┘
         │
         ↓
    ┌──────────────────┐
    │  ML/IA Services  │
    │                  │
    │ ├─ LangChain     │
    │ ├─ OpenAI API    │
    │ ├─ XGBoost       │
    │ ├─ Pinecone      │
    │ └─ SHAP          │
    └──────────────────┘
```

---

## 🎯 Capas y Responsabilidades

### **1. PRESENTATION LAYER (Frontend)**
**Tecnología:** Next.js 14 + React 18 + TypeScript  
**Puerto:** 3000 (desarrollo)  
**Responsabilidades:**
- UI/UX interactiva
- Formularios y validación
- Autenticación y gestión de sesión
- Comunicación con backend vía HTTP

---

### **2. API LAYER (Backend)**
**Tecnología:** FastAPI + Python 3.12  
**Puerto:** 8000 (desarrollo)  
**Responsabilidades:**
- Endpoints REST
- Validación de datos (Pydantic)
- Autenticación (JWT + MFA)
- Multi-tenant isolation
- Rate limiting y seguridad

---

### **3. DATA LAYER**
**Tecnologías:** PostgreSQL, Redis, Elasticsearch  
**Responsabilidades:**
- Persistencia de datos (PostgreSQL)
- Caché distribuido (Redis)
- Búsqueda full-text (Elasticsearch)
- Vectores para IA (Pinecone)

---

### **4. AI/ML LAYER**
**Tecnologías:** LangChain, OpenAI, scikit-learn, XGBoost  
**Responsabilidades:**
- Análisis de inconsistencias (LLM)
- Detección de fraude (ML models)
- Búsqueda semántica (Vector embeddings)
- Explicabilidad (SHAP)

---

## 💻 Stack Detallado por Componente

### **FRONTEND**

```
Next.js 14
├─ Framework: React 18 + TypeScript
├─ Build: Vite (fast refresh)
├─ Routing: App Router (next/navigation)
├─ State: Zustand
├─ Data Fetching: TanStack Query (React Query)
├─ UI Components: Shadcn/ui + Radix UI
├─ Styling: Tailwind CSS
├─ Forms: React Hook Form + Zod validation
├─ HTTP Client: Axios + JWT interceptor
├─ Charts: Recharts
├─ PDF: react-pdf + jsPDF
├─ Testing: Vitest + Playwright
└─ Auth: NextAuth.js v5 (JWT)
```

**Instalación:**
```bash
npm create next-app@latest siniestros-frontend -- --typescript --tailwind
```

---

### **BACKEND**

```
FastAPI + Python 3.12
├─ Framework: FastAPI (ASGI)
├─ Server: Uvicorn
├─ ORM: SQLAlchemy 2.0
├─ Database Driver: psycopg[binary]
├─ Validation: Pydantic v2
├─ Auth: python-jose + passlib + pyotp (MFA)
├─ Tasks: Celery + Redis backend
├─ Search: elasticsearch
├─ Cache: redis
├─ File Storage: boto3 (AWS S3)
├─ ML: scikit-learn, xgboost, pandas, numpy
├─ LLM: langchain, openai
├─ Vector DB: pinecone-client
├─ Monitoring: python-json-logger
└─ Testing: pytest + pytest-asyncio
```

**Setup inicial:**
```bash
python3.12 -m venv venv
source venv/bin/activate
pip install fastapi uvicorn sqlalchemy psycopg[binary] pydantic celery redis
```

---

### **BASE DE DATOS**

| BD | Propósito | Configuración |
|---|---|---|
| **PostgreSQL** | Datos principales (per-tenant) | RDS (AWS) / Local: port 5432 |
| **Redis** | Cache + Celery broker | ElastiCache (AWS) / Local: port 6379 |
| **Elasticsearch** | Búsqueda full-text en expedientes | Elastic Cloud / Local: port 9200 |
| **Pinecone** | Vectores para IA (embeddings) | Cloud SaaS |
| **AWS S3** | Archivos multimedia | Cloud SaaS |

---

### **INFRAESTRUCTURA**

| Componente | Servicio | Detalles |
|---|---|---|
| **Compute** | AWS ECS Fargate | Contenedores serverless |
| **Load Balancer** | AWS ALB | Distribución de tráfico |
| **CDN** | AWS CloudFront | Caché global + S3 |
| **Database** | AWS RDS PostgreSQL | Una BD por tenant |
| **Cache** | AWS ElastiCache | Redis managed |
| **Storage** | AWS S3 | Documentos + multimedia |
| **Container Registry** | AWS ECR | Private Docker images |
| **Secrets** | AWS Secrets Manager | Credenciales rotadas |
| **Logging** | CloudWatch + ELK | Logs centralizados |
| **Monitoring** | CloudWatch + Prometheus | Métricas + alertas |

---

### **IA/ML**

| Componente | Tecnología | Uso |
|---|---|---|
| **LLM Orquestación** | LangChain + OpenAI | Análisis de inconsistencias |
| **Fraud Detection** | XGBoost + scikit-learn | Modelo de detección |
| **Vector Search** | Pinecone | Búsqueda semántica de claims |
| **Explicabilidad** | SHAP | Explicar scores de fraude |
| **Feature Engineering** | Pandas + NumPy | Procesamiento de datos |

---

## 📦 Stack Resumido (Quick Reference)

```
FRONTEND:
  Next.js 14 • React 18 • TypeScript • Zustand • TanStack Query
  Shadcn/ui • Tailwind • React Hook Form • Axios

BACKEND:
  FastAPI • Python 3.12 • SQLAlchemy • Pydantic
  Celery • Redis • Elasticsearch • Pinecone

DATABASES:
  PostgreSQL • Redis • Elasticsearch • Pinecone • S3

AI/ML:
  LangChain • OpenAI • XGBoost • SHAP

INFRA:
  AWS (ECS Fargate • RDS • ElastiCache • S3 • CloudFront)
  Docker • GitHub Actions (CI/CD)

TESTING:
  Vitest • Playwright (Frontend)
  Pytest • Pytest-asyncio (Backend)
```

---

## 🔄 Flujo de Datos (Ejemplo: Crear Siniestro)

```
1. Usuario rellenan formulario en Next.js
        ↓
2. React Hook Form valida con Zod
        ↓
3. Axios envía POST a FastAPI /api/claims
        ↓
4. FastAPI valida con Pydantic
        ↓
5. JWT token verificado
        ↓
6. SQLAlchemy guarda en PostgreSQL (tenant aislado)
        ↓
7. Celery task indexa en Elasticsearch
        ↓
8. LangChain + OpenAI analiza inconsistencias
        ↓
9. XGBoost calcula fraud score
        ↓
10. SHAP genera explicación
        ↓
11. Resultado vuelve a React vía JSON
        ↓
12. UI actualiza (TanStack Query revalida)
```

---

## 🚀 Ventajas de Este Stack

✅ **Velocidad:** FastAPI es 3x más rápido que Django  
✅ **Type Safety:** TypeScript + Pydantic = menos bugs  
✅ **IA-Ready:** Python nativo para ML/LLM  
✅ **Modern:** Next.js, Vite, async/await en todo  
✅ **Escalable:** Arquitectura de microservicios posible  
✅ **DX:** Hot reload, auto-docs (Swagger), TypeScript everywhere  
✅ **Testing:** Vitest + Pytest son rapidísimos  
✅ **DevOps:** Docker + GitHub Actions simple  

---

## 📋 Roadmap de Implementación

| Sprint | Componente | Tecnología |
|--------|-----------|-----------|
| **0** | Setup Docker, repos, CI/CD | Docker Compose, GitHub Actions |
| **1** | Auth + Tenant Isolation | FastAPI + JWT + PostgreSQL |
| **2** | CRUD Siniestros | SQLAlchemy + Pydantic |
| **3** | Upload multimedia | S3 + Celery |
| **4** | Búsqueda | Elasticsearch |
| **5** | Dashboard | Next.js + Recharts |
| **6** | Fraud Detection | XGBoost + SHAP |
| **7** | IA Analysis | LangChain + OpenAI |
| **8** | Production Deploy | AWS ECS + RDS |

---

## 🎓 Requisitos Previos

**Frontend:**
- Node.js 18+
- npm o yarn

**Backend:**
- Python 3.12
- pip + venv
- Docker

**Services:**
- AWS Account (desarrollo + producción)
- OpenAI API key
- Pinecone account (vector DB)

---

## 📝 Próximos Pasos

1. ✅ Stack definido
2. → Leer SPRINT_0_SETUP.md
3. → Clonar/crear repos
4. → Docker setup local
5. → Primer endpoint funcionando

---

**Versión:** 1.0  
**Fecha:** Mayo 2026  
**Estado:** Listo para implementar  
**Autor:** Luis Angel Arze

