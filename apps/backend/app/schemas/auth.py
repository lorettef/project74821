import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    """POST /auth/register — phone + password."""

    phone: str = Field(..., min_length=5, max_length=20, pattern=r"^\+?\d{5,20}$")
    password: str = Field(..., min_length=6, max_length=128)
    email: str | None = Field(None, max_length=255)


class LoginRequest(BaseModel):
    """POST /auth/login — phone + password."""

    phone: str = Field(..., min_length=5, max_length=20)
    password: str = Field(..., min_length=1, max_length=128)


class RefreshRequest(BaseModel):
    """POST /auth/refresh — rotate refresh token."""

    refresh_token: str = Field(..., min_length=1)


class TokenPair(BaseModel):
    """Response with access + refresh token pair."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    """User data returned from /auth/me and /auth/register."""

    id: uuid.UUID
    phone: str
    email: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
