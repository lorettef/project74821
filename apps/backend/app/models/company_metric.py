import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, uuid_pk


class CompanyMetric(Base):
    __tablename__ = "company_metrics"

    id: Mapped[uuid.UUID] = uuid_pk()
    company_id: Mapped[uuid.UUID] = mapped_column(
        sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )
    recorded_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )
    mrr: Mapped[float | None] = mapped_column(sa.Float, nullable=True)
    arr: Mapped[float | None] = mapped_column(sa.Float, nullable=True)
    customers: Mapped[int | None] = mapped_column(sa.Integer, nullable=True)
    cash_balance: Mapped[float | None] = mapped_column(sa.Float, nullable=True)
    monthly_burn: Mapped[float | None] = mapped_column(sa.Float, nullable=True)
    cac: Mapped[float | None] = mapped_column(sa.Float, nullable=True)
    ltv: Mapped[float | None] = mapped_column(sa.Float, nullable=True)
    churn_rate: Mapped[float | None] = mapped_column(sa.Float, nullable=True)
    gross_margin: Mapped[float | None] = mapped_column(sa.Float, nullable=True)
    ltv_cac_ratio: Mapped[float | None] = mapped_column(sa.Float, nullable=True)
    payback_period: Mapped[float | None] = mapped_column(sa.Float, nullable=True)
    team_size: Mapped[int | None] = mapped_column(sa.Integer, nullable=True)
    stage_specific_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    company = relationship("Company", back_populates="metrics")
