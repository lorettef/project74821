import uuid
from datetime import datetime, timedelta, timezone

import structlog
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import ConflictError, UnauthorizedError
from app.core.security import (
    ACCESS_TOKEN_TYPE,
    REFRESH_TOKEN_TYPE,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.models import RefreshToken, User
from app.schemas import (
    LoginRequest,
    RegisterRequest,
    TokenPair,
)

logger = structlog.get_logger(__name__)


async def register_user(
    db: AsyncSession, request: RegisterRequest
) -> TokenPair:
    existing = await db.execute(select(User).where(User.phone == request.phone))
    if existing.scalar_one_or_none() is not None:
        raise ConflictError("Phone already registered")

    user = User(
        phone=request.phone,
        email=request.email,
        hashed_password=hash_password(request.password),
    )
    db.add(user)
    await db.flush()

    logger.info("user_registered", user_id=str(user.id))

    return await _create_token_pair(db, user)


async def authenticate_user(
    db: AsyncSession, request: LoginRequest
) -> TokenPair:
    result = await db.execute(select(User).where(User.phone == request.phone))
    user = result.scalar_one_or_none()

    if user is None:
        raise UnauthorizedError("Invalid phone or password")

    if not verify_password(request.password, user.hashed_password):
        raise UnauthorizedError("Invalid phone or password")

    logger.info("user_authenticated", user_id=str(user.id))

    return await _create_token_pair(db, user)


async def refresh_access_token(
    db: AsyncSession, refresh_token: str
) -> TokenPair:
    token_hash = hash_token(refresh_token)

    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.revoked == False,
        )
    )
    stored_token = result.scalar_one_or_none()

    if stored_token is None:
        raise UnauthorizedError("Invalid or revoked refresh token")

    if stored_token.expires_at < datetime.now(timezone.utc):
        stored_token.revoked = True
        await db.commit()
        raise UnauthorizedError("Refresh token expired")

    try:
        payload = decode_token(refresh_token, expected_type=REFRESH_TOKEN_TYPE)
    except JWTError:
        raise UnauthorizedError("Invalid refresh token")

    user_id_str = payload.get("sub")
    if user_id_str is None:
        raise UnauthorizedError("Invalid refresh token payload")

    user = await db.get(User, uuid.UUID(user_id_str))
    if user is None:
        raise UnauthorizedError("User not found")

    stored_token.revoked = True

    new_access = create_access_token({"sub": str(user.id)})
    new_refresh = create_refresh_token({"sub": str(user.id)})
    new_hash = hash_token(new_refresh)
    new_expires = datetime.now(timezone.utc) + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )

    db.add(
        RefreshToken(
            user_id=user.id,
            token_hash=new_hash,
            expires_at=new_expires,
        )
    )

    await db.commit()

    logger.info("refresh_token_rotated", user_id=str(user.id))

    return TokenPair(access_token=new_access, refresh_token=new_refresh)


async def revoke_refresh_token(
    db: AsyncSession, refresh_token: str
) -> None:
    token_hash = hash_token(refresh_token)

    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    )
    stored_token = result.scalar_one_or_none()

    if stored_token is None:
        return

    stored_token.revoked = True
    await db.commit()

    logger.info("refresh_token_revoked", token_id=str(stored_token.id))


async def get_current_user(
    db: AsyncSession, token: str
) -> User:
    try:
        payload = decode_token(token, expected_type=ACCESS_TOKEN_TYPE)
    except JWTError:
        raise UnauthorizedError("Invalid or expired access token")

    user_id_str = payload.get("sub")
    if user_id_str is None:
        raise UnauthorizedError("Invalid access token payload")

    user = await db.get(User, uuid.UUID(user_id_str))
    if user is None:
        raise UnauthorizedError("User not found")

    return user


async def _create_token_pair(db: AsyncSession, user: User) -> TokenPair:
    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})

    token_hash = hash_token(refresh_token)
    expires_at = datetime.now(timezone.utc) + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )

    db.add(
        RefreshToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at,
        )
    )
    await db.commit()

    return TokenPair(access_token=access_token, refresh_token=refresh_token)
