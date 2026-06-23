# Startup Engine v2.0 — Architecture Decision Record

## ADR-001: Backend — FastAPI over Streamlit-embedded

**Status**: Accepted
**Date**: 2026-06-24

### Context
v1.0 used Streamlit as both UI and backend — business logic, API calls, and rendering were mixed in one 2,271-line file. Auth was PBKDF2 with JSON-file sessions. Data was stored in flat JSON files with no concurrency control.

### Decision
Use **FastAPI** (Python 3.12) as the backend API layer. FastAPI provides:
- Async-native request handling (uvicorn + asyncio)
- Automatic OpenAPI documentation
- Pydantic v2 integration for request/response validation
- JWT + OAuth2 password flow (RFC-compliant)
- Separation of concerns: UI (Next.js) → API (FastAPI) → DB (PostgreSQL)

### Alternatives Considered
- **Keep Streamlit**: No API, no separation, no scaling
- **Node.js/Express**: Different ecosystem for AI (GigaChat is Python SDK)
- **Django REST Framework**: Heavier, less async-native

### Consequences
- Frontend must be built separately (Next.js)
- Two services to deploy instead of one
- Network calls between frontend and backend (mitigated by server-side rendering)

---

## ADR-002: Frontend — Next.js 14 App Router

**Status**: Accepted
**Date**: 2026-06-24

### Context
v1.0 Streamlit rendered everything server-side, mixing HTML generation with business logic. No component architecture, no client-side interactivity beyond Streamlit's built-in widgets.

### Decision
Use **Next.js 14** with App Router. Provides:
- React Server Components for zero-JS data fetching
- Server Actions for form submissions (no API route boilerplate)
- File-based routing with layouts and loading states
- Built-in image/font optimization
- TypeScript end-to-end

### Alternatives Considered
- **Vite + React SPA**: No SSR, worse SEO, manual routing
- **Remix**: Similar capabilities, smaller ecosystem
- **SvelteKit**: Different ecosystem, smaller talent pool

### Consequences
- Two language ecosystems (Python backend, TypeScript frontend)
- Shared types must be synced (mitigated: OpenAPI → TypeScript generation)

---

## ADR-003: Database — PostgreSQL 16

**Status**: Accepted
**Date**: 2026-06-24

### Context
v1.0 used JSON files (`data/storage/`) with race conditions, no ACID, no referential integrity, no migrations.

### Decision
Use **PostgreSQL 16** with SQLAlchemy 2.0 (async) and Alembic. Provides:
- ACID transactions
- JSONB for flexible stage-specific metrics
- Foreign keys for referential integrity
- Row-level security potential
- Alembic for versioned schema migrations
- Free tier on Supabase/Railway

### Alternatives Considered
- **SQLite**: Works but lacks JSONB, concurrent write issues for multi-user
- **MongoDB**: Document store matches JSON pattern but no joins, no ACID by default
- **MySQL**: Fewer features than PostgreSQL (no JSONB, weaker enum support)

### Consequences
- Requires running PostgreSQL (Docker in dev, managed service in prod)
- Migration from JSON files needed (script at `scripts/migrate_v1_to_v2.py`)

---

## ADR-004: Monorepo Structure

**Status**: Accepted
**Date**: 2026-06-24

### Decision

```
project74821/
├── apps/
│   ├── backend/          # FastAPI (Python)
│   └── frontend/         # Next.js (TypeScript)
├── packages/
│   └── shared/           # TypeScript types from OpenAPI
├── docs/
│   ├── architecture.md   # This file
│   └── PLAN.md           # 5-day migration plan
├── scripts/
│   └── migrate_v1_to_v2.py
├── docker-compose.yml
└── .github/workflows/
    ├── ci.yml
    └── deploy.yml
```

### Consequences
- No shared code between Python and TypeScript (different ecosystems)
- `packages/shared` only contains TypeScript type definitions
- Deployment: 3 containers (frontend, backend, db)

---

## Entity-Relationship Diagram

```
┌──────────┐       ┌──────────────┐       ┌──────────────────┐
│  users   │       │  companies   │       │ company_metrics  │
├──────────┤       ├──────────────┤       ├──────────────────┤
│ id (PK)  │──1:N──│ id (PK)      │──1:N──│ id (PK)          │
│ phone    │       │ owner_id(FK) │       │ company_id (FK)  │
│ email    │       │ name         │       │ recorded_at      │
│ passwd   │       │ stage (ENUM) │       │ mrr, arr, cust...│
│ created  │       │ created_at   │       │ cac, ltv, churn  │
│ updated  │       │ updated_at   │       │ stage_data(JSONB)│
└──────────┘       └──────────────┘       └──────────────────┘
     │ 1:N              │ 1:N                   
     │                  │                       
     ▼                  ▼                       
┌──────────────┐  ┌──────────────┐   ┌──────────────┐
│refresh_tokens│  │   cohorts    │   │    plans     │
├──────────────┤  ├──────────────┤   ├──────────────┤
│ id (PK)      │  │ id (PK)      │   │ id (PK)      │
│ user_id (FK) │  │ company_id   │   │ company_id   │
│ token_hash   │  │ cohort_month │   │ name, period │
│ expires_at   │  │ size, retent │   │ start/end    │
│ revoked      │  │ avg_revenue  │   │ status       │
└──────────────┘  │ cac          │   └──────────────┘
                  └──────────────┘         │ 1:N
                          │                │
                          │         ┌──────┴──────────┐
                          │         ▼                  ▼
                          │  ┌──────────────┐  ┌───────────────┐
                          │  │ plan_targets │  │plan_adjustments│
                          │  ├──────────────┤  ├───────────────┤
                          │  │ id (PK)      │  │ id (PK)       │
                          │  │ plan_id (FK) │  │ plan_id (FK)  │
                          │  │ metric_name  │  │ changed_by FK │
                          │  │ target_value │  │ prev (JSONB)  │
                          │  │ current_val  │  │ new (JSONB)   │
                          │  │ progress     │  │ reason        │
                          │  └──────────────┘  └───────────────┘
                          │
                          ▼
                   ┌──────────────┐
                   │    tasks     │       ┌──────────────┐
                   ├──────────────┤       │  ai_advice   │
                   │ id (PK)      │       ├──────────────┤
                   │ company_id   │       │ id (PK)      │
                   │ creator_id FK│       │ company_id   │
                   │ assignee FK  │       │ category     │
                   │ title, desc  │       │ title,content│
                   │ category     │       │ metrics(JSONB)│
                   │ priority     │       │ metadata     │
                   │ status       │       │ is_applied   │
                   │ due_date     │       │ created_at   │
                   │ tags TEXT[]  │       └──────────────┘
                   └──────────────┘

Enums:
  stage: idea | pre_seed | seed | series_a | series_b | series_c | series_d
  task_priority: low | medium | high | critical
  task_status: todo | in_progress | review | done
  task_category: runway | churn | growth | fundraising | team | product | marketing | sales
  plan_status: draft | active | completed | archived
  advice_category: metrics | runway | churn | growth | fundraising | team | risk | general
```

---

## Data Flow

```
Browser (Next.js)
    │
    ├── GET /api/v1/companies/{id} ────────┐
    ├── POST /api/v1/companies/{id}/metrics │
    ├── GET /api/v1/companies/{id}/runway   │
    │                                       ▼
    │                              ┌─────────────────┐
    │                              │    FastAPI       │
    │                              │  (apps/backend)  │
    │                              ├─────────────────┤
    │                              │ Auth (JWT)       │
    │                              │ CRUD Services    │
    │                              │ Metrics Engine   │
    │                              │ AI Client        │
    │                              └────────┬────────┘
    │                                       │
    │                              ┌────────▼────────┐
    │                              │   PostgreSQL     │
    │                              │   (Docker)       │
    │                              └────────┬────────┘
    │                                       │
    │                              ┌────────▼────────┐
    │                              │  GigaChat API    │
    │                              │  (Sber, external)│
    │                              └─────────────────┘
    │
    ├── Server Components (RSC) → fetch from FastAPI
    ├── Server Actions → POST to FastAPI
    └── Client Components → React Query → FastAPI
```

---

## API Design Principles

1. **RESTful**: Resources at `/api/v1/{resource}` with standard HTTP verbs
2. **Versioned**: `/api/v1/` prefix for future-compatibility
3. **JWT Auth**: Bearer token in Authorization header
4. **Error format**:
   ```json
   {
     "error": {
       "code": "VALIDATION_ERROR",
       "message": "company_id is required",
       "details": [{"field": "company_id", "reason": "missing"}]
     }
   }
   ```
5. **Pagination**: `?offset=0&limit=50`, response includes `total` count
6. **Filtering**: `?stage=seed&status=active`
7. **Sorting**: `?sort_by=created_at&order=desc`

---

## Security Model

| Concern | Implementation |
|---------|---------------|
| Authentication | JWT (access 15min + refresh 7d), OAuth2 Password Flow |
| Password Storage | bcrypt ($2b$ rounds=12) |
| Token Storage | httpOnly, Secure, SameSite=Strict cookies |
| CSRF | SameSite cookies + Origin header check |
| XSS | React auto-escape + CSP headers |
| SQL Injection | SQLAlchemy parameterized queries |
| Rate Limiting | 100 req/min on /auth/*, 300 req/min general |
| CORS | Restricted to frontend origin only |
| Secrets | Environment variables, never in code |
| HTTPS | Required in production (TLS termination at reverse proxy) |
