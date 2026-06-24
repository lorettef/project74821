import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.base import StageEnum


class CompanyCreate(BaseModel):
    """Create a new company."""

    name: str = Field(..., min_length=1, max_length=255)
    stage: StageEnum = StageEnum.idea


class CompanyUpdate(BaseModel):
    """Update company fields."""

    name: str | None = Field(None, min_length=1, max_length=255)
    stage: StageEnum | None = None


class CompanyRead(BaseModel):
    """Company representation in API responses."""

    id: uuid.UUID
    owner_id: uuid.UUID
    name: str
    stage: StageEnum
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
