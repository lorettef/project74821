import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field


class TaskCreate(BaseModel):
    """Create a new task."""

    title: str = Field(..., min_length=1, max_length=500)
    description: str | None = None
    category: str | None = Field(None, max_length=50)
    priority: str = "medium"
    status: str = "todo"
    due_date: date | None = None
    tags: list[str] | None = None
    assignee_id: uuid.UUID | None = None


class TaskUpdate(BaseModel):
    """Update task fields."""

    title: str | None = Field(None, min_length=1, max_length=500)
    description: str | None = None
    category: str | None = Field(None, max_length=50)
    priority: str | None = None
    status: str | None = None
    due_date: date | None = None
    tags: list[str] | None = None
    assignee_id: uuid.UUID | None = None


class TaskRead(BaseModel):
    """Task from the database."""

    id: uuid.UUID
    company_id: uuid.UUID
    creator_id: uuid.UUID
    assignee_id: uuid.UUID | None = None
    title: str
    description: str | None = None
    category: str | None = None
    priority: str
    status: str
    due_date: date | None = None
    tags: list[str] | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
