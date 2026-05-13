# Asignación de Sprints - Modelo Simple
## Plataforma Inteligente de Gestión de Siniestros

---

## 👥 Equipo: 5 Full-Stacks

| Rol | Sprint | Responsabilidad | Horas |
|-----|--------|-----------------|-------|
| **Full-Stack #1** | **Sprint 1** | Auth + Multi-tenant (FE + BE) | 40h |
| **Full-Stack #2** | **Sprint 2** | CRUD Core Models (FE + BE) | 38h |
| **Full-Stack #3** | **Sprint 3** | Siniestro Workflow (FE + BE) | 42h |
| **Full-Stack #4** | **Sprint 4** | Search Elasticsearch (FE + BE) | 36h |
| **Full-Stack #5** | **Sprint 5** | Dashboard + Reports (FE + BE) | 38h |
| **Backend Lead** | **Sprint 6** | AI/Fraud Detection (ML) | 45h |
| **Data Engineer** | **Sprint 7** | Vector Search (Data) | 40h |

---

## 📋 Sprints Detallados

### **Sprint 1: Auth + Multi-tenant (40h)**
**Responsable:** Full-Stack #1

**Tareas:**
```
BACKEND:
├─ Database schema
├─ JWT + MFA implementation
├─ Auth endpoints (6 endpoints)
├─ Security (rate limiting, CORS)
└─ Backend tests

FRONTEND:
├─ Login/Register components
├─ Zustand auth store
├─ Axios JWT interceptor
├─ MFA QR code + verification

INTEGRATION:
├─ End-to-end testing
├─ Multi-tenant isolation
└─ Documentation
```

**Entrega:**
- ✅ Login/Register funcional
- ✅ JWT tokens válidos
- ✅ MFA opcional para admins
- ✅ Multi-tenant isolation verificada

---

### **Sprint 2: CRUD Core Models (38h)**
**Responsable:** Full-Stack #2

**Tareas:**
```
BACKEND:
├─ Database schema (Policyholders, Policies, Vehicles)
├─ CRUD endpoints (15 endpoints)
├─ Pagination + filtering
└─ Backend tests

FRONTEND:
├─ DataTable component (reusable)
├─ PoliceholdersList + Form
├─ PoliciesList + Form
├─ VehiclesList + Form
├─ Shared components (Modal, Delete)
├─ Form validation (Zod)
└─ Integration tests
```

**Entrega:**
- ✅ CRUD ABMs completos
- ✅ Paginación y búsqueda
- ✅ Validaciones end-to-end
- ✅ Tests >80% coverage

---

### **Sprint 3: Siniestro Workflow (42h)**
**Responsable:** Full-Stack #3

**Tareas:**
```
BACKEND:
├─ Database schema (Claims, Notes, Evidence, DocRequests)
├─ Claims CRUD endpoints
├─ Evidence upload (S3 presigned URLs)
├─ Notes endpoints
├─ Document requests endpoints
├─ Workflow state machine
├─ Celery file processing tasks
└─ Backend tests

FRONTEND:
├─ ClaimsList component
├─ ClaimDetail with tabs (General, Evidence, Notes, Requests)
├─ EvidenceUploader (drag & drop)
├─ EvidenceGallery (lightbox)
├─ NotesThread (comments)
├─ Document requests UI
└─ Integration tests
```

**Entrega:**
- ✅ Claims workflow completo
- ✅ Evidence upload con S3
- ✅ Workflow de estados funcional
- ✅ Notes y requests operativos

---

### **Sprint 4: Search (Elasticsearch) (36h)**
**Responsable:** Full-Stack #4

**Tareas:**
```
BACKEND:
├─ Elasticsearch setup + mapping
├─ Celery indexing tasks
├─ Search endpoint (full-text + filters)
├─ Query optimization
├─ Result caching (Redis)
├─ Performance testing (load testing)
└─ Backend tests

FRONTEND:
├─ SearchBar con debounce
├─ AdvancedFilters component (multiselect, date, slider)
├─ SearchResults (infinite scroll)
├─ Filter state management (Zustand)
├─ Search analytics (trending keywords)
└─ Integration tests
```

**Entrega:**
- ✅ Full-text search funcional
- ✅ Filtros avanzados
- ✅ Queries <1s en 10k documentos
- ✅ Auto-indexing en background

---

### **Sprint 5: Dashboard + Reports (38h)**
**Responsable:** Full-Stack #5

**Tareas:**
```
BACKEND:
├─ Analytics database schema
├─ KPI endpoints (GET /api/analytics/*)
├─ Report generation (PDF/Excel)
├─ Permission checks (Admin/Supervisor only)
└─ Backend tests

FRONTEND:
├─ KPICard component (metrics + trends)
├─ Dashboard layout (responsive)
├─ LineChart (claims by date)
├─ BarChart (status distribution)
├─ PieChart (coverage types)
├─ ReportsSection (date picker, export)
├─ Report preview
└─ Integration tests
```

**Entrega:**
- ✅ Dashboard con 6+ KPIs
- ✅ Charts interactivos (Recharts)
- ✅ Reportes PDF y Excel
- ✅ Access control

---

### **Sprint 6: AI/Fraud Detection (45h)**
**Responsable:** Backend Lead

**Tareas:**
```
MACHINE LEARNING:
├─ XGBoost model training
├─ Feature engineering (claim amount, time, policy age, etc)
├─ Cross-validation + metrics
└─ Model persistence

LLM INTEGRATION:
├─ LangChain + OpenAI setup
├─ Inconsistency detection
├─ Text analysis pipeline
└─ Prompt engineering

API:
├─ Analysis endpoint
├─ Celery background tasks
├─ SHAP explanations
└─ Tests

INTEGRATION:
├─ Connect to claim detail UI
├─ Store analysis results
└─ Create alerts for high fraud scores
```

**Entrega:**
- ✅ Fraud scores asignados
- ✅ Inconsistencias detectadas
- ✅ Análisis automático en background
- ✅ SHAP explicaciones

---

### **Sprint 7: Vector Search + Duplicates (40h)**
**Responsable:** Data Engineer

**Tareas:**
```
EMBEDDINGS:
├─ Pinecone setup + index creation
├─ Embeddings generation (OpenAI API)
├─ Text preprocessing (claims + OCR)
└─ Batch indexing script

SIMILARITY SEARCH:
├─ Similarity search endpoint
├─ Duplicate detection logic (threshold > 0.90)
├─ Celery batch processing
└─ Performance optimization

DATA PIPELINE:
├─ OCR text extraction from images
├─ Text cleaning + normalization
├─ Feature extraction
└─ Tests

FRONTEND INTEGRATION:
├─ SimilarClaimsPanel
├─ DuplicateAlert warning
└─ Comparison view
```

**Entrega:**
- ✅ Búsqueda semántica funcional
- ✅ Duplicados detectados automáticamente
- ✅ Batch indexing <5 min
- ✅ Queries <2s

---

## 📅 Timeline (8 Semanas)

```
Semana 1: Sprint 1 (Full-Stack #1)
└─ Auth + Multi-tenant

Semana 2: Sprint 2 (Full-Stack #2)
└─ CRUD Core Models

Semana 3: Sprint 3 (Full-Stack #3)
└─ Siniestro Workflow

Semana 4: Sprint 4 (Full-Stack #4)
└─ Search Elasticsearch

Semana 5: Sprint 5 (Full-Stack #5)
└─ Dashboard + Reports

Semana 6: Sprint 6 (Backend Lead)
└─ AI/Fraud Detection

Semana 7: Sprint 7 (Data Engineer)
└─ Vector Search

Semana 8: Sprint 8 (TODOS)
└─ Production Deploy + Monitoring
```

---

## ✅ Modelo Full-Stack: Ventajas

| Ventaja | Descripción |
|---------|------------|
| **Ownership** | Una persona = responsable total del sprint |
| **Decisiones rápidas** | No necesita sincronización constante |
| **Debugging fácil** | Conoce FE + BE + DB |
| **End-to-end testing** | Entiende toda la feature |
| **Documentación clara** | Una sola fuente de verdad |

---

## ⚙️ Modo Operación

**Daily Standup:** 15 min (09:00 AM)
- Reportes por sprint
- Blockers y soporte

**Code Review:**
- Mínimo 1 aprobación de otra persona
- Focus: calidad, tests, docs

**Pair Programming (Sprints 6-7):**
- Backend Lead + UI support (2-3h/semana)
- Data Engineer + UI support (2-3h/semana)

---

## 📊 Carga de Trabajo

```
Full-Stack #1: 40h (1 semana)
Full-Stack #2: 38h (1 semana)
Full-Stack #3: 42h (1 semana)
Full-Stack #4: 36h (1 semana)
Full-Stack #5: 38h (1 semana)
Backend Lead:  45h (1 semana) + soporte
Data Engineer: 40h (1 semana) + soporte

TOTAL: 279 horas en 8 semanas
PROMEDIO: 35h/semana por persona
```

---

## 🎯 Success Criteria

### Por Sprint
- ✅ Todas las tareas completadas
- ✅ Code review aprobado (2+ personas)
- ✅ Tests >80% coverage (backend), >60% (frontend)
- ✅ Documentation actualizada
- ✅ Feature funciona end-to-end

### Proyecto
- ✅ 8 sprints completados
- ✅ En producción con monitoring
- ✅ Documentación completa
- ✅ Team entrenado en operaciones

---

## 🚀 Próximos Pasos

1. ✅ Entender modelo (1 persona = 1 sprint)
2. → Asignar personas a roles
3. → Setup GitHub repos + teams
4. → Primera standup mañana 09:00 AM
5. → Comenzar Sprint 1

---

**Versión:** 1.0  
**Modelo:** Full-Stack por Sprint  
**Total de tiempo:** 8 semanas  
**Estado:** Listo para ejecutar

