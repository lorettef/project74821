import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, uuid_pk


class AIAdvice(Base):
    __tablename__ = "ai_advice"

    id: Mapped[uuid.UUID] = uuid_pk()
    company_id: Mapped[uuid.UUID] = mapped_column(
        sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )
    category: Mapped[str | None] = mapped_column(sa.String(50), nullable=True)
    title: Mapped[str] = mapped_column(sa.String(500), nullable=False)
    content: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    related_metrics: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    extra_data: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)
    is_applied: Mapped[bool] = mapped_column(
        sa.Boolean, default=False, server_default=sa.false(), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now()
    )

    company = relationship("Company", back_populates="ai_advice")
