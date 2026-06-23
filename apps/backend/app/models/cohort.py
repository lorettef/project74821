import uuid
from datetime import date

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, uuid_pk


class Cohort(Base):
    __tablename__ = "cohorts"

    id: Mapped[uuid.UUID] = uuid_pk()
    company_id: Mapped[uuid.UUID] = mapped_column(
        sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )
    cohort_month: Mapped[date] = mapped_column(sa.Date, nullable=False)
    size: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0)
    retention: Mapped[float | None] = mapped_column(sa.Float, nullable=True)
    avg_revenue: Mapped[float | None] = mapped_column(sa.Float, nullable=True)
    cac: Mapped[float | None] = mapped_column(sa.Float, nullable=True)

    company = relationship("Company", back_populates="cohorts")
