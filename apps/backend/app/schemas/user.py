import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    """Schema for creating a user (used internally)."""

    phone: str = Field(..., min_length=5, max_length=20)
    password: str = Field(..., min_length=6, max_length=128)
    email: str | None = Field(None, max_length=255)

    model_config = {"from_attributes": True}


class UserRead(BaseModel):
    """Public user representation."""

    id: uuid.UUID
    phone: str
    email: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
