import uuid

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, uuid_pk


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = uuid_pk()
    phone: Mapped[str] = mapped_column(sa.String(20), unique=True, nullable=False)
    email: Mapped[str | None] = mapped_column(sa.String(255), nullable=True)
    hashed_password: Mapped[str] = mapped_column(sa.String(255), nullable=False)

    companies = relationship("Company", back_populates="owner")
    created_tasks = relationship(
        "Task", back_populates="creator", foreign_keys="Task.creator_id"
    )
    assigned_tasks = relationship(
        "Task", back_populates="assignee", foreign_keys="Task.assignee_id"
    )
    plan_adjustments = relationship("PlanAdjustment", back_populates="changed_by_user")
    refresh_tokens = relationship("RefreshToken", back_populates="user")
