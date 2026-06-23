import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, uuid_pk


class PlanAdjustment(Base):
    __tablename__ = "plan_adjustments"

    id: Mapped[uuid.UUID] = uuid_pk()
    plan_id: Mapped[uuid.UUID] = mapped_column(
        sa.ForeignKey("plans.id", ondelete="CASCADE"), nullable=False
    )
    changed_by: Mapped[uuid.UUID] = mapped_column(
        sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    previous_targets: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    new_targets: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    reason: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now()
    )

    plan = relationship("Plan", back_populates="adjustments")
    changed_by_user = relationship("User", back_populates="plan_adjustments")
