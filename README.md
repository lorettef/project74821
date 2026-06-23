# Startup Engine v2.0

Платформа для управления SaaS-стартапом на всех стадиях роста: от идеи до pre-IPO.

## Стек

| Уровень | Технология |
|---------|-----------|
| Frontend | Next.js 14 (App Router) + TypeScript + Tailwind CSS + shadcn/ui + Tremor |
| Backend | FastAPI (Python 3.12) + SQLAlchemy 2.0 + Alembic |
| Database | PostgreSQL 16 |
| Auth | JWT + OAuth2 + bcrypt |
| AI | GigaChat (Сбер) |
| Infra | Docker Compose + GitHub Actions |

## Быстрый старт

```bash
# 1. Клонировать
git clone https://github.com/lorettef/project74821.git
cd project74821

# 2. Запустить (требуется Docker)
docker compose up -d

# 3. Проверить
curl http://localhost:8000/api/v1/health
open http://localhost:3000
```

## Структура

```
apps/
├── backend/      # FastAPI API
└── frontend/     # Next.js UI
packages/
└── shared/       # TypeScript-типы (автогенерация из OpenAPI)
docs/
├── PLAN.md           # 5-дневный план разработки
└── architecture.md   # ADR + ER-диаграмма
```

## Документация

- [Архитектура](docs/architecture.md) — ADR, ER-диаграмма, flow данных
- [План разработки](docs/PLAN.md) — 5-дневный FAANG-style план миграции
- [API Docs](http://localhost:8000/docs) — Swagger UI (после запуска)

## Команды

```bash
# Линтинг
cd apps/backend && ruff check .
cd apps/frontend && npm run lint

# Тесты
cd apps/backend && pytest
cd apps/frontend && npm test

# Миграции
cd apps/backend && alembic upgrade head
```
