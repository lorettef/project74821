"""initial

Revision ID: 0fd99b964855
Revises:
Create Date: 2026-06-24 14:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0fd99b964855"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("phone", sa.String(20), nullable=False),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("phone"),
    )

    op.create_table(
        "companies",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("owner_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column(
            "stage",
            postgresql.ENUM(
                "idea", "pre_seed", "seed", "series_a",
                "series_b", "series_c", "series_d",
                name="stage_enum",
                create_type=True,
            ),
            nullable=False,
            server_default="idea",
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "company_metrics",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("company_id", sa.UUID(), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("mrr", sa.Float(), nullable=True),
        sa.Column("arr", sa.Float(), nullable=True),
        sa.Column("customers", sa.Integer(), nullable=True),
        sa.Column("cash_balance", sa.Float(), nullable=True),
        sa.Column("monthly_burn", sa.Float(), nullable=True),
        sa.Column("cac", sa.Float(), nullable=True),
        sa.Column("ltv", sa.Float(), nullable=True),
        sa.Column("churn_rate", sa.Float(), nullable=True),
        sa.Column("gross_margin", sa.Float(), nullable=True),
        sa.Column("ltv_cac_ratio", sa.Float(), nullable=True),
        sa.Column("payback_period", sa.Float(), nullable=True),
        sa.Column("team_size", sa.Integer(), nullable=True),
        sa.Column("stage_specific_data", postgresql.JSONB(), nullable=True),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "cohorts",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("company_id", sa.UUID(), nullable=False),
        sa.Column("cohort_month", sa.Date(), nullable=False),
        sa.Column("size", sa.Integer(), nullable=False),
        sa.Column("retention", sa.Float(), nullable=True),
        sa.Column("avg_revenue", sa.Float(), nullable=True),
        sa.Column("cac", sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "plans",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("company_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("period", sa.String(50), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column(
            "status",
            postgresql.ENUM("draft", "active", "completed", "archived", name="plan_status_enum", create_type=True),
            nullable=False,
            server_default="draft",
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "plan_targets",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("plan_id", sa.UUID(), nullable=False),
        sa.Column("metric_name", sa.String(100), nullable=False),
        sa.Column("target_value", sa.Float(), nullable=False),
        sa.Column("current_value", sa.Float(), nullable=True),
        sa.Column("progress", sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(["plan_id"], ["plans.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "plan_adjustments",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("plan_id", sa.UUID(), nullable=False),
        sa.Column("changed_by", sa.UUID(), nullable=False),
        sa.Column("previous_targets", postgresql.JSONB(), nullable=True),
        sa.Column("new_targets", postgresql.JSONB(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["changed_by"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["plan_id"], ["plans.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "tasks",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("company_id", sa.UUID(), nullable=False),
        sa.Column("creator_id", sa.UUID(), nullable=False),
        sa.Column("assignee_id", sa.UUID(), nullable=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("category", sa.String(50), nullable=True),
        sa.Column(
            "priority",
            postgresql.ENUM("low", "medium", "high", "critical", name="task_priority_enum", create_type=True),
            nullable=False,
            server_default="medium",
        ),
        sa.Column(
            "status",
            postgresql.ENUM("todo", "in_progress", "review", "done", name="task_status_enum", create_type=True),
            nullable=False,
            server_default="todo",
        ),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("tags", postgresql.ARRAY(sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(["assignee_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["creator_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "ai_advice",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("company_id", sa.UUID(), nullable=False),
        sa.Column("category", sa.String(50), nullable=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("related_metrics", postgresql.JSONB(), nullable=True),
        sa.Column("extra_data", postgresql.JSONB(), nullable=True),
        sa.Column("is_applied", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("token_hash", sa.String(255), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index("ix_company_metrics_company_id", "company_metrics", ["company_id"])
    op.create_index("ix_company_metrics_recorded_at", "company_metrics", ["recorded_at"])
    op.create_index("ix_cohorts_company_id", "cohorts", ["company_id"])
    op.create_index("ix_plans_company_id", "plans", ["company_id"])
    op.create_index("ix_tasks_company_id", "tasks", ["company_id"])
    op.create_index("ix_tasks_status", "tasks", ["status"])
    op.create_index("ix_ai_advice_company_id", "ai_advice", ["company_id"])
    op.create_index(
        "ix_refresh_tokens_token_hash", "refresh_tokens", ["token_hash"], unique=True
    )


def downgrade() -> None:
    op.drop_index("ix_refresh_tokens_token_hash")
    op.drop_index("ix_ai_advice_company_id")
    op.drop_index("ix_tasks_status")
    op.drop_index("ix_tasks_company_id")
    op.drop_index("ix_plans_company_id")
    op.drop_index("ix_cohorts_company_id")
    op.drop_index("ix_company_metrics_recorded_at")
    op.drop_index("ix_company_metrics_company_id")

    op.drop_table("refresh_tokens")
    op.drop_table("ai_advice")
    op.drop_table("tasks")
    op.drop_table("plan_adjustments")
    op.drop_table("plan_targets")
    op.drop_table("plans")
    op.drop_table("cohorts")
    op.drop_table("company_metrics")
    op.drop_table("companies")
    op.drop_table("users")

    op.execute("DROP TYPE IF EXISTS task_status_enum")
    op.execute("DROP TYPE IF EXISTS task_priority_enum")
    op.execute("DROP TYPE IF EXISTS plan_status_enum")
    op.execute("DROP TYPE IF EXISTS stage_enum")
