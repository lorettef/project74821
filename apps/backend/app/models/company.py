import uuid

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, StageEnum, TimestampMixin, uuid_pk


class Company(Base, TimestampMixin):
    __tablename__ = "companies"

    id: Mapped[uuid.UUID] = uuid_pk()
    owner_id: Mapped[uuid.UUID] = mapped_column(
        sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    stage: Mapped[StageEnum] = mapped_column(
        sa.Enum(StageEnum, name="stage_enum", create_type=True),
        nullable=False,
        default=StageEnum.idea,
    )

    owner = relationship("User", back_populates="companies")
    metrics = relationship("CompanyMetric", back_populates="company")
    cohorts = relationship("Cohort", back_populates="company")
    plans = relationship("Plan", back_populates="company")
    tasks = relationship("Task", back_populates="company")
    ai_advice = relationship("AIAdvice", back_populates="company")
