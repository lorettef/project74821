# Startup Engine v2.0 — FAANG-Style 5-Day Migration Plan

> **Stack Migration**: Streamlit/JSON → Next.js + FastAPI + PostgreSQL
> **Owner**: Startup Engine Team | **Sprint**: 5 days | **Methodology**: XP + Trunk-Based Development

---

## Stack Decision: Old → New

| Layer | Old Stack | ❌ Why Drop | New Stack | ✅ Why |
|-------|----------|------------|-----------|--------|
| **Frontend** | Streamlit (Python SSR) | Смесь UI+логики в одном файле, не масштабируется, нет компонентного подхода, XSRF отключён | **Next.js 14** (App Router) + **TypeScript** | Декларативный UI, компонентная архитектура, серверные компоненты, streaming, встроенная безопасность |
| **Styling** | Streamlit markup + raw HTML | `unsafe_allow_html` — XSS-векторы, нет дизайн-системы | **Tailwind CSS** + **shadcn/ui** | Utility-first, готовая дизайн-система из 40+ компонентов, zero-runtime, tree-shaking |
| **Charts** | Plotly (Python, 5 MB JS bundle) | Тяжёлый, блокирует рендеринг, нет SSR | **Tremor** (React) | Нативный React, SSR-совместим, 30+ типов дашборд-чартов из коробки |
| **Backend** | Streamlit-embedded logic | Нет API, всё в одном процессе, нет разделения слоёв | **FastAPI** (Python 3.12) | Async-native, авто-документация OpenAPI, Pydantic v2 валидация, производительность на уровне Node |
| **Database** | JSON-файлы (`data/storage/`) | Race conditions, нет ACID, нет миграций, нет referential integrity | **PostgreSQL 16** + **SQLAlchemy 2.0** + **Alembic** | ACID, конкурентный доступ, миграции, индексы, foreign keys |
| **Auth** | Phone + PBKDF2-SHA256 + JSON-сессии | Нет стандарта, нет OAuth2, сессии в файле | **JWT** (access + refresh) + **OAuth2** (Password Flow) + **bcrypt** | RFC-стандарт, stateless, refresh rotation, готова интеграция с Google/Yandex OAuth |
| **AI** | GigaChat (3 дублирующих клиента) | Дублирование ~4000 строк, `print()` вместо `logging`, bare `except` | **GigaChat SDK** (единый клиент) + **LangChain** обёртка | Один клиент, structured output через Pydantic, retry + circuit breaker, логирование через structlog |
| **Testing** | pytest (55 тестов, ~5% покрытие) | Auth/UI/AI без тестов, нет E2E | **pytest** (backend) + **Vitest** (frontend) + **Playwright** (E2E) | 85%+ coverage, property-based testing, E2E smoke tests |
| **CI/CD** | Отсутствует | Ручной деплой | **GitHub Actions** + **Docker Compose** | Авто-тесты → линтер → билд → деплой |
| **Infra** | Один процесс Streamlit | Не масштабируется | **Docker** (3 контейнера: frontend, backend, db) | Изоляция, воспроизводимость, горизонтальное масштабирование |

---

## Day 0 (Pre-Sprint): Architecture & Scaffolding

### 09:00–10:00 — Architecture Decision Record (ADR)

- [ ] **ADR-001**: Выбрать FastAPI как backend (причина: Python-экосистема для AI, async-native, auto-docs)
- [ ] **ADR-002**: Выбрать Next.js App Router (причина: RSC, streaming, server actions)
- [ ] **ADR-003**: Выбрать PostgreSQL (причина: ACID, JSONB для гибких метрик, бесплатно на Supabase/Railway)
- [ ] **ADR-004**: Принять структуру монорепо: `apps/backend` + `apps/frontend` + `packages/shared`

### 10:00–13:00 — Database Schema Design

ER-диаграмма новой схемы (замена 7 dataclass-моделей):

```sql
-- Core
users (id, phone, email, hashed_password, created_at, updated_at)
companies (id, owner_id FK→users, name, stage ENUM, created_at, updated_at)

-- Metrics (замена MetricHistory + Company fields)
company_metrics (id, company_id FK→companies, recorded_at, mrr, arr, customers,
  cash_balance, monthly_burn, cac, ltv, churn_rate, gross_margin,
  ltv_cac_ratio, payback_period, team_size, stage_specific_data JSONB)

-- Cohorts
cohorts (id, company_id FK, cohort_month, size, retention, avg_revenue, cac)

-- Planning
plans (id, company_id FK, name, period, start_date, end_date, status, created_at)
plan_targets (id, plan_id FK, metric_name, target_value, current_value, progress)
plan_adjustments (id, plan_id FK, changed_by FK→users, previous_targets JSONB,
  new_targets JSONB, reason, created_at)

-- Tasks
tasks (id, company_id FK, creator_id FK→users, assignee_id FK→users nullable,
  title, description, category, priority, status, due_date, tags TEXT[])

-- AI
ai_advice (id, company_id FK, category, title, content, related_metrics JSONB,
  metadata JSONB, is_applied BOOLEAN DEFAULT false, created_at)
ai_analysis_cache (id, company_id FK, analysis_type, input_hash, response JSONB,
  created_at, expires_at)

-- Auth
refresh_tokens (id, user_id FK→users, token_hash, expires_at, revoked BOOLEAN)
```

### 13:00–18:00 — Project Scaffolding

```bash
startup-engine/
├── apps/
│   ├── backend/           # FastAPI
│   │   ├── app/
│   │   │   ├── api/v1/    # Route handlers
│   │   │   ├── core/      # Config, security, deps
│   │   │   ├── models/    # SQLAlchemy models
│   │   │   ├── schemas/   # Pydantic schemas
│   │   │   ├── services/  # Business logic
│   │   │   └── main.py
│   │   ├── alembic/
│   │   ├── tests/
│   │   ├── Dockerfile
│   │   └── pyproject.toml
│   └── frontend/          # Next.js 14
│       ├── src/
│       │   ├── app/       # App Router pages
│       │   ├── components/ # UI components
│       │   ├── lib/       # API client, utils
│       │   └── hooks/     # Custom hooks
│       ├── tests/
│       ├── Dockerfile
│       └── package.json
├── packages/
│   └── shared/            # TypeScript types, API contracts
│       ├── src/types/
│       └── package.json
├── docker-compose.yml
├── .github/workflows/
│   ├── ci.yml
│   └── deploy.yml
└── README.md
```

### Deliverables Day 0
- [x] ER-диаграмма согласована → PR #0: `docs/architecture.md`
- [x] Монорепо инициализировано → PR #1: `chore: project scaffold`
- [x] Docker Compose запускает frontend + backend + db → зелёный healthcheck
- [x] Alembic инициализирован, `alembic upgrade head` создаёт все таблицы

---

## Day 1: Backend Foundation & Auth

### Daily Goal
PostgreSQL схема готова, FastAPI отдаёт `/api/v1/health`, аутентификация работает с JWT.

### 09:00–09:15 — Standup
- Блокеры с Day 0? DB поднялась? Миграции прошли?
- Распределение: 2 backend-разработчика (модели + auth), 0 frontend сегодня.

### 09:15–11:00 — SQLAlchemy Models + Pydantic Schemas
**Owner**: Backend Dev A

- [ ] Создать все 10 SQLAlchemy моделей (`apps/backend/app/models/`)
- [ ] Создать Pydantic v2 схемы для всех CRUD операций (`apps/backend/app/schemas/`)
- [ ] Написать миграцию Alembic (`alembic revision --autogenerate -m "init"`)
- [ ] **QA Gate**: `alembic upgrade head && alembic downgrade -1` — roundtrip без ошибок
- [ ] **QA Gate**: `psql` → `\dt` → все 10 таблиц существуют с правильными foreign keys

### 11:00–14:00 — Auth System (JWT + OAuth2)
**Owner**: Backend Dev B

- [ ] `POST /api/v1/auth/register` — phone + password → bcrypt → JWT pair
- [ ] `POST /api/v1/auth/login` — phone + password → verify → JWT pair
- [ ] `POST /api/v1/auth/refresh` — refresh token rotation (старый инвалидируется)
- [ ] `POST /api/v1/auth/logout` — revoke refresh token
- [ ] `GET /api/v1/auth/me` — текущий пользователь из JWT claims
- [ ] Dependency `get_current_user` для protected endpoints
- [ ] **QA Gate**: `curl -X POST /auth/register` → получаем `access_token` → `curl -H "Authorization: Bearer $TOKEN" /auth/me` → 200 с user_id
- [ ] **QA Gate**: Expired token → 401. Revoked refresh → 401. Wrong password → 401.

### 14:00–15:30 — API Foundation
**Owner**: Backend Dev A

- [ ] `GET /api/v1/health` — возвращает `{"status": "ok", "db": "connected", "version": "2.0.0"}`
- [ ] Глобальный exception handler: `ValidationError` → 422, `IntegrityError` → 409, `HTTPException` → pass
- [ ] CORS middleware: разрешить `localhost:3000` (Next.js dev)
- [ ] Rate limiting: 100 req/min на `/auth/*`
- [ ] Structlog: JSON-логирование всех запросов (request_id, duration, status)
- [ ] **QA Gate**: `GET /health` → 200. `GET /api/v1/nonexistent` → 404 JSON. Invalid JSON body → 422 с деталями.

### 15:30–17:00 — Data Migration Script
**Owner**: Backend Dev B

- [ ] Скрипт `scripts/migrate_v1_to_v2.py`:
  - Читает старые JSON-файлы из `data/storage/`
  - Нормализует `churn_rate` (всё в decimal 0.0–1.0)
  - Создаёт `users` из `users.json`
  - Создаёт `companies` из `companies.json`
  - Импортирует `metric_history` → `company_metrics`
  - Импортирует `plans`, `tasks`, `cohorts`, `ai_advice`
- [ ] **QA Gate**: Запуск на копии старых данных → row count в SQL совпадает с количеством записей в JSON

### 17:00–18:00 — Testing + Code Review
- [ ] unit-тесты для auth flow: register → login → refresh → logout → cannot reuse refresh
- [ ] unit-тесты для моделей: создание компании с несуществующим user_id → IntegrityError
- [ ] **Code Review Gate**: PR #2 → ревьюер проверяет:
  - bcrypt используется (не PBKDF2)
  - Refresh token хранится как hash (не plaintext)
  - Нет SQL-инъекций (все запросы через SQLAlchemy ORM)
  - Pydantic модели валидируют все поля

### Deliverables Day 1
- [x] 10 SQLAlchemy моделей + миграция Alembic → PR #2
- [x] Auth API: 5 endpoints → 100% покрытие тестами
- [x] `/health` + логирование + CORS + rate limiting
- [x] Скрипт миграции данных v1 → v2
- [x] CI: `pytest` зелёный, `ruff` без ошибок

---

## Day 2: Business Logic + AI Integration

### Daily Goal
StartupEngine перенесён в FastAPI-сервисы, GigaChat клиент переписан как один модуль, все расчёты работают через API.

### 09:00–09:15 — Standup
- Миграция данных прошла успешно?
- Есть ли компании в БД после миграции?

### 09:15–12:00 — Core Business Services
**Owner**: Backend Dev A

- [ ] `CompanyService` — CRUD компаний (`POST/GET/PUT/DELETE /api/v1/companies`)
- [ ] `MetricsService` — запись и чтение метрик (`POST/GET /api/v1/companies/{id}/metrics`)
  - Расчёт производных метрик: LTV = ARPU × average_lifetime_months, CAC ratio, NRR, Magic Number, Payback Period
  - Нормализация churn_rate на уровне сервиса
- [ ] `RunwayService` — расчёт взлётной полосы (`GET /api/v1/companies/{id}/runway`)
  - Перенос логики из `core/runway.py`
  - Stage-specific пороги как конфигурация (не магические числа)
- [ ] `CohortService` — когортный анализ (`POST/GET /api/v1/companies/{id}/cohorts`)
- [ ] `RoadmapService` — дорожная карта по стадиям (`GET /api/v1/companies/{id}/roadmap`)

### 12:00–14:00 — Plan-Fact Analyzer + Tasks
**Owner**: Backend Dev B

- [ ] `PlanService` — CRUD планов, расчёт прогресса (`POST/GET/PUT /api/v1/companies/{id}/plans`)
- [ ] `PlanAnalyzer` — план-факт отклонения (`POST /api/v1/companies/{id}/plans/{plan_id}/analyze`)
- [ ] `TaskService` — CRUD задач с приоритетами и дедлайнами
- [ ] `ActionOrchestrator` — генерация задач из рекомендаций

### 14:00–16:00 — GigaChat Client Refactor (CRITICAL)

**Текущая боль**: 3 клиента (~4000 строк), `print()` вместо `logging`, bare `except`, monkey-patching.

**Новая архитектура**:

```
services/
├── ai/
│   ├── gigachat_client.py    # Единый HTTP-клиент (токены, retry, SSL)
│   ├── gigachat_parser.py    # Structured output парсер (Pydantic модели)
│   ├── analysis/
│   │   ├── metrics.py        # Анализ метрик
│   │   ├── runway.py         # Анализ runway
│   │   ├── plan_fact.py      # План-факт анализ
│   │   └── recommendations.py # Генерация рекомендаций
│   └── prompts/              # Промпты (шаблоны Jinja2)
│       ├── metrics.j2
│       ├── runway.j2
│       └── ...
```

- [ ] `GigaChatClient` — единый класс:
  - `async get_token()` → кеширование с TTL (не хранить в глобальной переменной)
  - `async chat(prompt, response_model: Type[T])` → возвращает Pydantic-модель, а не dict
  - Circuit breaker: 3 ошибки подряд → 30s пауза
  - Все ошибки через `structlog`, а не `print()`
  - Специфичные исключения: `GigaChatAuthError`, `GigaChatRateLimitError`, `GigaChatParseError`
- [ ] `GigaChatParser` — один парсер с structured output:
  - `extract_json(text)` → Pydantic model
  - 3-stage recovery (как раньше, но в одном месте)
  - Логирование неудачных парсингов для отладки
- [ ] Промпты вынесены в Jinja2-шаблоны (не захардкожены в коде)

### 16:00–17:00 — API Endpoints для AI
- [ ] `POST /api/v1/companies/{id}/ai/recommendations` — получить рекомендации
- [ ] `POST /api/v1/companies/{id}/ai/analyze-metrics` — анализ текущих метрик
- [ ] `GET /api/v1/companies/{id}/ai/advice` — история AI-советов
- [ ] `PATCH /api/v1/companies/{id}/ai/advice/{advice_id}/apply` — отметить совет как применённый

### 17:00–18:00 — Testing + Code Review
- [ ] Unit-тесты для каждого сервиса (mock GigaChat API)
- [ ] Интеграционный тест: создать компанию → записать метрики → получить AI-анализ → проверить structured output
- [ ] **Code Review Gate**: PR #3 → ревьюер проверяет:
  - `GigaChatClient` — нет дублирования со старыми версиями
  - Все промпты в шаблонах, не в коде
  - Нет `except:` без конкретного типа
  - Нет `print()` — только `structlog`

### Deliverables Day 2
- [x] 5 core services (Company, Metrics, Runway, Cohort, Roadmap)
- [x] Plan + Task management API
- [x] Единый GigaChat клиент (замена 3 старых)
- [x] AI analysis endpoints
- [x] Интеграционные тесты: metrics → AI advice flow

---

## Day 3: Frontend Foundation

### Daily Goal
Next.js приложение с аутентификацией, дашбордом и навигацией. Backend API подключён через типизированный клиент.

### 09:00–09:15 — Standup
- Все backend endpoints работают? Swagger docs доступны?
- Блокеры по API-контрактам?

### 09:15–10:30 — Frontend Scaffolding + Shared Types
**Owner**: Frontend Dev A

- [ ] Next.js 14 App Router с `src/` директорией
- [ ] Tailwind CSS + shadcn/ui инициализированы (тема: startup/saas)
- [ ] Пакет `packages/shared` — TypeScript-типы, сгенерированные из OpenAPI-схемы FastAPI
  - `npx openapi-typescript http://localhost:8000/openapi.json -o packages/shared/src/types/api.ts`
- [ ] API-клиент: `apps/frontend/src/lib/api.ts`
  - `createApiClient(baseUrl, getToken)` → типизированные методы для каждого endpoint
  - Автоматический refresh token при 401
  - Retry с exponential backoff

### 10:30–13:00 — Auth Pages + Middleware
**Owner**: Frontend Dev B

- [ ] Next.js Middleware: защита роутов (`/dashboard/*` → проверка JWT в httpOnly cookie)
- [ ] Страницы:
  - `/login` — форма телефона + пароля
  - `/register` — форма регистрации с валидацией
- [ ] `AuthContext` (React Context) — хранит user, access_token, методы login/logout/register
- [ ] Server Actions для auth (форма не раскрывает API URL клиенту)
- [ ] **QA Gate**: Зарегистрироваться → редирект на `/dashboard` → обновить страницу → не редиректит на `/login`
- [ ] **QA Gate**: Истёкший токен → 401 → авто-refresh → запрос повторён успешно

### 13:00–15:30 — Dashboard + Layout
**Owner**: Frontend Dev A

- [ ] Root Layout: Sidebar (компании, навигация) + Header (user menu, уведомления)
- [ ] Компоненты shadcn/ui: `Sidebar`, `DropdownMenu`, `Avatar`, `Badge`, `Card`
- [ ] Страница `/dashboard`:
  - **Metric Cards** (Tremor): MRR, ARR, Customers, Churn, LTV, CAC — 6 карточек в ряд
  - **Runway Gauge** (Tremor): полукруглый gauge с зонами (красная/жёлтая/зелёная)
  - **MRR Trend Chart** (Tremor AreaChart): линия за последние 12 месяцев
  - **Cohort Heatmap** (Tremor): retention по когортам
- [ ] **QA Gate**: Дашборд рендерится с реальными данными из API. Карточки показывают правильные значения.

### 15:30–17:30 — Company Selector + Profile
**Owner**: Frontend Dev B

- [ ] `/companies` — список компаний пользователя (таблица)
- [ ] `/companies/[id]` — профиль компании:
  - Форма редактирования (стадия, метрики)
  - Stage progress bar (идея → ... → series_d)
  - Кнопка смены стадии
- [ ] `/companies/new` — форма создания компании
- [ ] **QA Gate**: Создать компанию → она появляется в `/companies` → открыть → изменить метрики → сохранить → дашборд обновлён

### 17:30–18:00 — Code Review
- [ ] **Code Review Gate**: PR #4 → ревьюер проверяет:
  - API-клиент типизирован (нет `any`)
  - Server Actions для auth (нет client-side API key leak)
  - httpOnly cookie для refresh token (не localStorage)
  - Все формы с `useFormState` и валидацией
  - RSC где возможно (дашборд — серверный компонент с streaming)

### Deliverables Day 3
- [x] Next.js 14 + Tailwind + shadcn/ui + Tremor — каркас приложения
- [x] Auth flow: login → register → middleware protection → token refresh
- [x] Dashboard: 6 metric cards + runway gauge + MRR chart + cohort heatmap
- [x] Company CRUD: список, профиль, создание
- [x] Типизированный API-клиент (автогенерация из OpenAPI)

---

## Day 4: Feature Pages + Reports

### Daily Goal
Все 9 страниц из старого Streamlit-приложения перенесены в Next.js. Отчёты и экспорт работают.

### 09:00–09:15 — Standup
- Dashboard загружается быстро? Метрики корректны?
- Проблемы с Tremor-чартами?

### 09:15–12:00 — Metrics & Analytics Pages
**Owner**: Frontend Dev A

- [ ] `/companies/[id]/metrics` — страница ввода и истории метрик:
  - Форма ввода метрик за период
  - Таблица истории (пагинация, сортировка, фильтр по дате)
  - График любой метрики за выбранный период (Tremor LineChart)
- [ ] `/companies/[id]/cohorts` — когортный анализ:
  - Форма добавления когорты
  - Интерактивная heatmap (Tremor)
  - Таблица когорт с retention и revenue
- [ ] **QA Gate**: Ввести метрики → график обновился → когорты отображаются корректно

### 12:00–14:00 — Planning & Tasks Pages
**Owner**: Frontend Dev B

- [ ] `/companies/[id]/plans` — управление планами:
  - Создание плана (название, период, цели по метрикам)
  - Карточка плана с progress bar'ом
  - План-факт анализ: таблица отклонений с цветовой индикацией
- [ ] `/companies/[id]/tasks` — канбан-доска задач:
  - Колонки: To Do → In Progress → Review → Done
  - Drag & drop (dnd-kit)
  - Фильтр по приоритету, категории, исполнителю
- [ ] **QA Gate**: Создать план → создать задачу → перетащить в Done → прогресс плана обновился

### 14:00–16:00 — AI Analysis Page
**Owner**: Frontend Dev A

- [ ] `/companies/[id]/ai` — AI-аналитика:
  - Кнопка «Запросить рекомендации» → skeleton loader → карточки с советами
  - История AI-советов с фильтром по категориям
  - Кнопка «Применить» / «Отклонить» совет
- [ ] **QA Gate**: Нажать «Запросить» → через 3-5 секунд карточки с рекомендациями → применить → статус изменился

### 16:00–17:30 — Reports & Export
**Owner**: Frontend Dev B

- [ ] `/companies/[id]/reports` — страница отчётов:
  - **Investor Report** — PDF (генерируется на backend через reportlab, отдаётся как `GET /api/v1/companies/{id}/reports/investor?format=pdf`)
  - **Weekly Digest** — форматированный текст (Markdown → HTML рендеринг)
  - **CSV Export** метрик и когорт
- [ ] API endpoints для отчётов (Backend, быстро):
  - `GET /api/v1/companies/{id}/reports/investor` → PDF
  - `GET /api/v1/companies/{id}/reports/weekly` → JSON/Markdown
  - `GET /api/v1/companies/{id}/metrics/export?format=csv` → CSV download

### 17:30–18:00 — Polish + Code Review
- [ ] Loading skeletons на всех страницах
- [ ] Error boundaries (error.tsx)
- [ ] 404 страница (not-found.tsx)
- [ ] **Code Review Gate**: PR #5 → ревьюер проверяет:
  - Все 9 страниц рендерятся без ошибок
  - Формы валидируются на клиенте (zod) и сервере (Pydantic)
  - Нет `useEffect` для фетчинга (используются Server Components + React Query для мутаций)
  - Drag & drop не ломает данные

### Deliverables Day 4
- [x] Metrics history + charts
- [x] Cohort heatmap + таблица
- [x] Plan management + план-факт анализ
- [x] Kanban-доска задач с drag & drop
- [x] AI-аналитика (запрос → результат → история)
- [x] Investor Report PDF + Weekly Digest + CSV Export

---

## Day 5: Testing, CI/CD & Launch

### Daily Goal
85%+ test coverage. CI/CD пайплайн. Docker production-сборка. Документация. Деплой.

### 09:00–09:15 — Standup
- Все фичи работают? Баги за ночь?
- План тестирования финализирован?

### 09:15–11:00 — Backend Testing Sprint
**Owner**: Backend Dev A + B

- [ ] Добить unit-тесты до 85% покрытия:
  - `CompanyService` — все edge cases (невалидная стадия, дубликат имени)
  - `MetricsService` — граничные значения (отрицательный MRR, churn > 100%)
  - `RunwayService` — все 7 стадий × 3 сценария (conservative/expected/optimistic) = 21 тест
  - `GigaChatClient` — mock HTTP: auth error, rate limit, malformed JSON, timeout
- [ ] Property-based тесты (hypothesis):
  - `churn_rate ∈ [0.0, 1.0]` для любой компании
  - `ltv ≥ 0` при любых входных данных
  - `mrr ≤ arr` всегда

### 11:00–13:00 — Frontend Testing Sprint
**Owner**: Frontend Dev A + B

- [ ] Unit-тесты компонентов (Vitest + Testing Library):
  - MetricCard: правильное форматирование чисел ($1.2M → "$1.2M")
  - RunwayGauge: цветовые зоны (0-3 мес красный, 3-6 жёлтый, 6+ зелёный)
  - CohortHeatmap: правильный gradient calc
  - TaskKanban: drag → API call → колонка обновлена
- [ ] **E2E Smoke Tests** (Playwright):
  - `auth.spec.ts`: register → login → dashboard → logout → cannot access /dashboard
  - `company.spec.ts`: create company → edit metrics → verify dashboard update
  - `plan.spec.ts`: create plan → create task → drag to done → verify plan progress
  - `ai.spec.ts`: request recommendations → wait for response → apply advice

### 13:00–14:30 — CI/CD Pipeline
**Owner**: Backend Dev A

- [ ] `.github/workflows/ci.yml`:
  ```yaml
  jobs:
    lint:        # ruff (backend) + biome (frontend)
    typecheck:   # mypy (backend) + tsc (frontend)
    test-be:     # pytest --cov --cov-report=xml (параллельно по сервисам)
    test-fe:     # vitest --coverage
    e2e:         # playwright (запускается после test-be + test-fe)
    build:       # docker build (только при PR в main)
  ```
- [ ] `.github/workflows/deploy.yml`:
  - Build Docker images → push to GitHub Container Registry
  - Deploy to VPS/Vercel/Railway (по выбору)

### 14:30–16:00 — Performance & Security Audit
**Owner**: Backend Dev B

- [ ] **Performance**:
  - Dashboard API: 3 параллельных запроса (company + metrics + cohorts) → < 500ms
  - N+1 prevention: SQLAlchemy `selectinload()`, `joinedload()`
  - API response compression (gzip)
  - Next.js: Image optimization, font optimization, bundle analyzer
- [ ] **Security**:
  - OWASP Top 10 checklist:
    - [x] Broken Access Control → `get_current_user` dependency на каждом endpoint
    - [x] Injection → SQLAlchemy parameterized queries
    - [x] XSS → React auto-escapes, CSP headers
    - [x] CSRF → SameSite=Strict cookies, CSRF token в Server Actions
    - [x] Sensitive Data Exposure → bcrypt, httpOnly cookies, HTTPS only
    - [x] Rate Limiting → slowapi на FastAPI
    - [x] CORS → restricted to frontend origin
  - `npm audit && pip-audit` — нет критических уязвимостей
  - Secrets: всё в environment variables, не в коде

### 16:00–17:00 — Documentation
**Owner**: Frontend Dev A

- [ ] `README.md` — getting started, архитектура, стек, env variables
- [ ] `CONTRIBUTING.md` — как запустить локально, coding standards, PR process
- [ ] `docs/api.md` — auto-generated из FastAPI `/docs` (ссылкой)
- [ ] `docs/architecture.md` — ER-диаграмма, flow данных, ADR

### 17:00–18:00 — Launch Prep + Retro
- [ ] Production Docker Compose: `docker compose -f docker-compose.prod.yml up -d`
- [ ] Health check: `curl https://api.startupengine.dev/health` → 200
- [ ] Smoke test production: пройти auth → создать компанию → дашборд
- [ ] **Team Retro** (30 min):
  - Что прошло хорошо?
  - Что заблокировало?
  - Что улучшить в следующем спринте?

### Deliverables Day 5
- [x] 85%+ test coverage (backend + frontend)
- [x] E2E smoke tests (4 сценария Playwright)
- [x] CI/CD: lint → typecheck → test → build → deploy
- [x] Performance: dashboard API < 500ms, Lighthouse > 90
- [x] Security: OWASP checklist пройден, 0 critical vulnerabilities
- [x] Documentation: README, CONTRIBUTING, API docs
- [x] Production деплой + health check

---

## Success Metrics (Day 5 EOD)

| Metric | Target | Measurement |
|--------|--------|-------------|
| Test coverage | ≥ 85% | `pytest --cov` + `vitest --coverage` |
| E2E tests pass | 4/4 | `npx playwright test` |
| API response time | < 500ms p95 | `/api/v1/companies/{id}` endpoint |
| Lighthouse score | > 90 | `/dashboard` page |
| OWASP compliance | 10/10 | Security checklist |
| Zero `except:` bare | 0 | `grep -r "except:" apps/backend/` |
| Zero `print()` | 0 (only structlog) | `grep -r "print(" apps/backend/` |
| JWT refresh rotation | enforced | Integration test |
| DB migrations roundtrip | pass | `alembic upgrade && downgrade` |
| Docker healthcheck | green | `docker compose ps` |

---

## Risk Register

| Risk | Probability | Impact | Mitigation |
|------|-----------|--------|-----------|
| GigaChat API нестабилен | Medium | High | Circuit breaker, fallback-режим, кеширование ответов |
| Миграция данных теряет записи | Low | Critical | Dry-run на копии, валидация row count, rollback-скрипт |
| Next.js App Router сложность | Medium | Medium | RSC только для read-only страниц, мутации через React Query |
| PostgreSQL не поднимается в CI | Low | Medium | GitHub Actions service containers, health check с retry |
| Не хватает времени на все фичи | High | Medium | Приоритет: Auth > Core Services > Dashboard > AI > Reports. Всё что ниже — в Day 6+ |

---

## Daily Ceremonies

| Время | Церемония | Длительность |
|-------|----------|-------------|
| 09:00 | Daily Standup (все) | 15 min |
| 12:00 | Async check-in (Slack: что сделано, блокеры) | 5 min |
| 16:00 | Mid-day review (парное ревью рабочих веток) | 30 min |
| 18:00 | Code Review Gate + PR Merge | 30 min |

---

## Branch Strategy (Trunk-Based)

```
main
  ├── feat/backend-scaffold     → PR #1 (Day 0)
  ├── feat/backend-models-auth  → PR #2 (Day 1)
  ├── feat/backend-services-ai  → PR #3 (Day 2)
  ├── feat/frontend-foundation  → PR #4 (Day 3)
  ├── feat/frontend-features    → PR #5 (Day 4)
  └── chore/ci-cd-launch        → PR #6 (Day 5)
```

**Правила**:
- PR в main только после Code Review Gate
- CI должен быть зелёным перед merge
- Коммиты: conventional commits (`feat:`, `fix:`, `chore:`, `test:`)
- Merge strategy: squash merge, линейная история
