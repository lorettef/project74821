from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.models import User
from app.schemas import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenPair,
    UserResponse,
)
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_session),
) -> User:
    return await auth_service.get_current_user(db, token)


@router.post("/register", response_model=TokenPair, status_code=201)
async def register(
    request: RegisterRequest,
    db: AsyncSession = Depends(get_session),
) -> TokenPair:
    return await auth_service.register_user(db, request)


@router.post("/login", response_model=TokenPair)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_session),
) -> TokenPair:
    return await auth_service.authenticate_user(db, request)


@router.post("/refresh", response_model=TokenPair)
async def refresh(
    request: RefreshRequest,
    db: AsyncSession = Depends(get_session),
) -> TokenPair:
    return await auth_service.refresh_access_token(db, request.refresh_token)


@router.post("/logout", status_code=204)
async def logout(
    request: RefreshRequest,
    db: AsyncSession = Depends(get_session),
) -> None:
    await auth_service.revoke_refresh_token(db, request.refresh_token)


@router.get("/me", response_model=UserResponse)
async def me(
    current_user: User = Depends(get_current_user),
) -> User:
    return current_user
