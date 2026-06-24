"""API v1 routes."""

from app.api.v1.auth import router as auth_router
from app.api.v1.companies import router as companies_router

__all__ = ["auth_router", "companies_router"]
