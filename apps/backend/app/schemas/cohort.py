import uuid
from datetime import date

from pydantic import BaseModel, Field


class CohortCreate(BaseModel):
    """Add a cohort record."""

    cohort_month: date
    size: int = Field(..., ge=0)
    retention: float | None = None
    avg_revenue: float | None = None
    cac: float | None = None


class CohortRead(BaseModel):
    """Cohort record from the database."""

    id: uuid.UUID
    company_id: uuid.UUID
    cohort_month: date
    size: int
    retention: float | None = None
    avg_revenue: float | None = None
    cac: float | None = None

    model_config = {"from_attributes": True}
