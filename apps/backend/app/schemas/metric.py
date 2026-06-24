import uuid
from datetime import datetime

from pydantic import BaseModel


class CompanyMetricCreate(BaseModel):
    """Record metrics for a company at a specific point in time."""

    recorded_at: datetime | None = None
    mrr: float | None = None
    arr: float | None = None
    customers: int | None = None
    cash_balance: float | None = None
    monthly_burn: float | None = None
    cac: float | None = None
    ltv: float | None = None
    churn_rate: float | None = None
    gross_margin: float | None = None
    ltv_cac_ratio: float | None = None
    payback_period: float | None = None
    team_size: int | None = None
    stage_specific_data: dict | None = None


class CompanyMetricRead(BaseModel):
    """Metric record from the database."""

    id: uuid.UUID
    company_id: uuid.UUID
    recorded_at: datetime
    mrr: float | None = None
    arr: float | None = None
    customers: int | None = None
    cash_balance: float | None = None
    monthly_burn: float | None = None
    cac: float | None = None
    ltv: float | None = None
    churn_rate: float | None = None
    gross_margin: float | None = None
    ltv_cac_ratio: float | None = None
    payback_period: float | None = None
    team_size: int | None = None
    stage_specific_data: dict | None = None

    model_config = {"from_attributes": True}
