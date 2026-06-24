import re
import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator


class RegisterRequest(BaseModel):
    """POST /auth/register — phone + password."""

    phone: str = Field(..., min_length=5, max_length=20, pattern=r"^\+?\d{5,20}$")
    password: str = Field(..., min_length=8, max_length=128)
    email: EmailStr | None = Field(None, max_length=255)

    @field_validator("password")
    @classmethod
    def _validate_password_complexity(cls, v: str) -> str:
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>_\-+=\[\]\\;'/`~]", v):
            raise ValueError("Password must contain at least one special character")
        return v


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
