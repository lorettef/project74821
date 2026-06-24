#!/usr/bin/env python3
"""
Standalone data migration script: imports v1 JSON files into PostgreSQL.

Usage:
    cd apps/backend && python scripts/migrate_v1_to_v2.py

Reads JSON files from ../../data/storage/ (relative to script location,
i.e. <project_root>/data/storage/) and inserts into PostgreSQL using
SQLAlchemy Core (sync engine, no async).

Import order: users → companies → company_metrics → cohorts → plans (+targets) → tasks → ai_advice
"""

from __future__ import annotations

import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert as pg_insert

_BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_BACKEND_DIR))

# Project root is 4 parents up: scripts/ → backend/ → apps/ → <root>
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "storage"

from app.core.config import settings  # noqa: E402
from app.models import Base  # noqa: E402


def _build_sync_url(async_url: str) -> str:
    return async_url.replace("+asyncpg", "").replace("+psycopg", "")


SYNC_URL = _build_sync_url(settings.DATABASE_URL)
engine = sa.create_engine(SYNC_URL, echo=False)


def load_json(filename: str) -> list[dict[str, Any]]:
    filepath = DATA_DIR / filename
    if not filepath.exists():
        print(f"  ⚠  {filename} not found — skipping.")
        return []
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def safe_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


def safe_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt)
        except (ValueError, TypeError):
            continue
    return None


def normalize_churn(raw: float | int | None) -> float | None:
    """Normalize churn_rate to 0.0–1.0. Values > 1.0 are treated as percentages (÷100)."""
    if raw is None:
        return None
    if raw > 1.0:
        return raw / 100.0
    return float(raw)


def migrate() -> None:
    print("=" * 60)
    print("  V1 → V2 Data Migration")
    print(f"  Data dir : {DATA_DIR}")
    print(f"  Database : {SYNC_URL.split('@')[-1] if '@' in SYNC_URL else SYNC_URL}")
    print("=" * 60)

    if not DATA_DIR.exists():
        print(f"\n  ✘  Data directory does not exist: {DATA_DIR}")
        print("     Nothing to migrate. Exiting.")
        return

    with engine.begin() as conn:
        users_json = load_json("users.json")
        phone_to_id: dict[str, str] = {}
        if users_json:
            users_table = Base.metadata.tables["users"]
            rows = [
                {
                    "phone": u["phone"],
                    "hashed_password": u["hashed_password"],
                    "email": u.get("email"),
                }
                for u in users_json
            ]
            result = conn.execute(
                pg_insert(users_table).values(rows).returning(
                    users_table.c.id,
                    users_table.c.phone,
                )
            )
            for row in result:
                phone_to_id[row.phone] = str(row.id)
            print(f"  ✓  Migrated {len(phone_to_id)} users")
        else:
            print("  -  No users to migrate")

        companies_json = load_json("companies.json")
        name_to_id: dict[str, str] = {}
        name_to_owner_id: dict[str, str] = {}
        if companies_json:
            companies_table = Base.metadata.tables["companies"]
            rows = []
            for c in companies_json:
                owner_phone = c.get("owner", "")
                owner_id = phone_to_id.get(owner_phone)
                if not owner_id:
                    print(f"  ⚠  Skipping company '{c.get('name')}' — owner '{owner_phone}' not found in users")
                    continue
                rows.append({
                    "name": c["name"],
                    "stage": c.get("stage", "idea"),
                    "owner_id": owner_id,
                })
            if rows:
                result = conn.execute(
                    pg_insert(companies_table).values(rows).returning(
                        companies_table.c.id,
                        companies_table.c.name,
                        companies_table.c.owner_id,
                    )
                )
                for row in result:
                    name_to_id[row.name] = str(row.id)
                    name_to_owner_id[row.name] = str(row.owner_id)
                print(f"  ✓  Migrated {len(name_to_id)} companies")
            else:
                print("  -  No valid companies to migrate (check owner references)")
        else:
            print("  -  No companies to migrate")

        metrics_json = load_json("metric_history.json")
        if metrics_json:
            metrics_table = Base.metadata.tables["company_metrics"]
            rows = []
            for m in metrics_json:
                company_name = m.get("company_name", "")
                company_id = name_to_id.get(company_name)
                if not company_id:
                    print(f"  ⚠  Skipping metric — company '{company_name}' not found")
                    continue
                rows.append({
                    "company_id": company_id,
                    "recorded_at": safe_datetime(m.get("recorded_at")) or datetime.now(timezone.utc),
                    "mrr": m.get("mrr"),
                    "arr": m.get("arr"),
                    "customers": m.get("customers"),
                    "cash_balance": m.get("cash_balance"),
                    "monthly_burn": m.get("monthly_burn"),
                    "cac": m.get("cac"),
                    "ltv": m.get("ltv"),
                    "churn_rate": normalize_churn(m.get("churn_rate")),
                    "gross_margin": m.get("gross_margin"),
                    "ltv_cac_ratio": m.get("ltv_cac_ratio"),
                    "payback_period": m.get("payback_period"),
                    "team_size": m.get("team_size"),
                    "stage_specific_data": m.get("stage_specific_data"),
                })
            if rows:
                conn.execute(pg_insert(metrics_table).values(rows))
                print(f"  ✓  Migrated {len(rows)} company metrics")
            else:
                print("  -  No valid metrics to migrate (check company references)")
        else:
            print("  -  No metrics to migrate")

        cohorts_json = load_json("cohorts.json")
        if cohorts_json:
            cohorts_table = Base.metadata.tables["cohorts"]
            rows = []
            for ch in cohorts_json:
                company_name = ch.get("company_name", "")
                company_id = name_to_id.get(company_name)
                if not company_id:
                    print(f"  ⚠  Skipping cohort — company '{company_name}' not found")
                    continue
                rows.append({
                    "company_id": company_id,
                    "cohort_month": safe_date(ch.get("cohort_month")),
                    "size": ch.get("size", 0),
                    "retention": ch.get("retention"),
                    "avg_revenue": ch.get("avg_revenue"),
                    "cac": ch.get("cac"),
                })
            if rows:
                conn.execute(pg_insert(cohorts_table).values(rows))
                print(f"  ✓  Migrated {len(rows)} cohorts")
            else:
                print("  -  No valid cohorts to migrate (check company references)")
        else:
            print("  -  No cohorts to migrate")

        plans_json = load_json("plans.json")
        if plans_json:
            plans_table = Base.metadata.tables["plans"]
            targets_table = Base.metadata.tables["plan_targets"]
            plan_count = 0
            target_count = 0
            for p in plans_json:
                company_name = p.get("company_name", "")
                company_id = name_to_id.get(company_name)
                if not company_id:
                    print(f"  ⚠  Skipping plan '{p.get('name')}' — company '{company_name}' not found")
                    continue
                result = conn.execute(
                    pg_insert(plans_table)
                    .values(
                        company_id=company_id,
                        name=p.get("name", "Unnamed Plan"),
                        period=p.get("period"),
                        start_date=safe_date(p.get("start_date")),
                        end_date=safe_date(p.get("end_date")),
                        status=p.get("status", "draft"),
                    )
                    .returning(plans_table.c.id)
                )
                plan_id = str(result.scalar())
                plan_count += 1

                raw_targets = p.get("targets", [])
                if raw_targets:
                    target_rows = []
                    for t in raw_targets:
                        target_rows.append({
                            "plan_id": plan_id,
                            "metric_name": t.get("metric", ""),
                            "target_value": float(t.get("target", 0)),
                            "current_value": float(t["current"]) if t.get("current") is not None else None,
                            "progress": float(t["progress"]) if t.get("progress") is not None else None,
                        })
                    conn.execute(pg_insert(targets_table).values(target_rows))
                    target_count += len(target_rows)

            print(f"  ✓  Migrated {plan_count} plans ({target_count} targets)")
        else:
            print("  -  No plans to migrate")

        tasks_json = load_json("tasks.json")
        if tasks_json:
            tasks_table = Base.metadata.tables["tasks"]
            rows = []
            for t in tasks_json:
                company_name = t.get("company_name", "")
                company_id = name_to_id.get(company_name)
                if not company_id:
                    print(f"  ⚠  Skipping task '{t.get('title')}' — company '{company_name}' not found")
                    continue
                assignee_id = None
                assignee_phone = t.get("assignee")
                if assignee_phone:
                    assignee_id = phone_to_id.get(str(assignee_phone))
                rows.append({
                    "company_id": company_id,
                    "creator_id": name_to_owner_id.get(company_name),
                    "assignee_id": assignee_id,
                    "title": t.get("title", "Untitled Task"),
                    "description": t.get("description"),
                    "category": t.get("category"),
                    "priority": t.get("priority", "medium"),
                    "status": t.get("status", "todo"),
                    "due_date": safe_date(t.get("due_date")),
                    "tags": t.get("tags"),
                    "created_at": safe_datetime(t.get("created_at")) or datetime.now(timezone.utc),
                    "updated_at": safe_datetime(t.get("updated_at")) or datetime.now(timezone.utc),
                })
            if rows:
                conn.execute(pg_insert(tasks_table).values(rows))
                print(f"  ✓  Migrated {len(rows)} tasks")
            else:
                print("  -  No valid tasks to migrate (check company references)")
        else:
            print("  -  No tasks to migrate")

        advice_json = load_json("ai_advice.json")
        if advice_json:
            advice_table = Base.metadata.tables["ai_advice"]
            rows = []
            for a in advice_json:
                company_name = a.get("company_name", "")
                company_id = name_to_id.get(company_name)
                if not company_id:
                    print(f"  ⚠  Skipping advice '{a.get('title')}' — company '{company_name}' not found")
                    continue
                rows.append({
                    "company_id": company_id,
                    "category": a.get("category"),
                    "title": a.get("title", "Untitled Advice"),
                    "content": a.get("content"),
                    "related_metrics": a.get("related_metrics"),
                    "extra_data": a.get("extra_data"),
                    "is_applied": a.get("is_applied", False),
                    "created_at": safe_datetime(a.get("created_at")) or datetime.now(timezone.utc),
                })
            if rows:
                conn.execute(pg_insert(advice_table).values(rows))
                print(f"  ✓  Migrated {len(rows)} ai_advice items")
            else:
                print("  -  No valid ai_advice to migrate (check company references)")
        else:
            print("  -  No ai_advice to migrate")

    print("\n" + "=" * 60)
    print("  Migration complete.")
    print("=" * 60)


if __name__ == "__main__":
    migrate()
