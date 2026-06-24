from app.schemas.auth import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenPair,
    UserResponse,
)
from app.schemas.user import UserCreate, UserRead
from app.schemas.company import CompanyCreate, CompanyRead, CompanyUpdate
from app.schemas.metric import CompanyMetricCreate, CompanyMetricRead
from app.schemas.cohort import CohortCreate, CohortRead
from app.schemas.plan import (
    PlanAdjustmentRead,
    PlanCreate,
    PlanRead,
    PlanTargetCreate,
    PlanTargetRead,
    PlanUpdate,
)
from app.schemas.task import TaskCreate, TaskRead, TaskUpdate
from app.schemas.ai_advice import AIAdviceCreate, AIAdviceRead

__all__ = [
    # Auth
    "RegisterRequest",
    "LoginRequest",
    "RefreshRequest",
    "TokenPair",
    "UserResponse",
    # User
    "UserCreate",
    "UserRead",
    # Company
    "CompanyCreate",
    "CompanyRead",
    "CompanyUpdate",
    # Metric
    "CompanyMetricCreate",
    "CompanyMetricRead",
    # Cohort
    "CohortCreate",
    "CohortRead",
    # Plan
    "PlanCreate",
    "PlanRead",
    "PlanUpdate",
    "PlanTargetCreate",
    "PlanTargetRead",
    "PlanAdjustmentRead",
    # Task
    "TaskCreate",
    "TaskRead",
    "TaskUpdate",
    # AI Advice
    "AIAdviceCreate",
    "AIAdviceRead",
]
