import uuid

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, uuid_pk


class PlanTarget(Base):
    __tablename__ = "plan_targets"

    id: Mapped[uuid.UUID] = uuid_pk()
    plan_id: Mapped[uuid.UUID] = mapped_column(
        sa.ForeignKey("plans.id", ondelete="CASCADE"), nullable=False
    )
    metric_name: Mapped[str] = mapped_column(sa.String(100), nullable=False)
    target_value: Mapped[float] = mapped_column(sa.Float, nullable=False)
    current_value: Mapped[float | None] = mapped_column(sa.Float, nullable=True)
    progress: Mapped[float | None] = mapped_column(sa.Float, nullable=True)

    plan = relationship("Plan", back_populates="targets")
