import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class AIAdviceCreate(BaseModel):
    """Create an AI advice record."""

    category: str | None = Field(None, max_length=50)
    title: str = Field(..., min_length=1, max_length=500)
    content: str | None = None
    related_metrics: dict | None = None
    extra_data: dict | None = None


class AIAdviceRead(BaseModel):
    """AI advice from the database."""

    id: uuid.UUID
    company_id: uuid.UUID
    category: str | None = None
    title: str
    content: str | None = None
    related_metrics: dict | None = None
    extra_data: dict | None = None
    is_applied: bool = False
    created_at: datetime

    model_config = {"from_attributes": True}
