import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field


class PlanTargetCreate(BaseModel):
    """Create a target within a plan."""

    metric_name: str = Field(..., min_length=1, max_length=100)
    target_value: float
    current_value: float | None = None
    progress: float | None = None


class PlanTargetRead(BaseModel):
    """Plan target from the database."""

    id: uuid.UUID
    plan_id: uuid.UUID
    metric_name: str
    target_value: float
    current_value: float | None = None
    progress: float | None = None

    model_config = {"from_attributes": True}


class PlanCreate(BaseModel):
    """Create a new plan."""

    name: str = Field(..., min_length=1, max_length=255)
    period: str | None = Field(None, max_length=50)
    start_date: date | None = None
    end_date: date | None = None
    status: str = "draft"


class PlanUpdate(BaseModel):
    """Update plan fields."""

    name: str | None = Field(None, min_length=1, max_length=255)
    period: str | None = Field(None, max_length=50)
    start_date: date | None = None
    end_date: date | None = None
    status: str | None = None


class PlanRead(BaseModel):
    """Plan from the database."""

    id: uuid.UUID
    company_id: uuid.UUID
    name: str
    period: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class PlanAdjustmentRead(BaseModel):
    """Plan adjustment from the database."""

    id: uuid.UUID
    plan_id: uuid.UUID
    changed_by: uuid.UUID
    previous_targets: dict | None = None
    new_targets: dict | None = None
    reason: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
