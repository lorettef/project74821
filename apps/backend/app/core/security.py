import hashlib
import uuid
from datetime import datetime, timedelta, timezone

import structlog
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

logger = structlog.get_logger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


ACCESS_TOKEN_TYPE = "access"
REFRESH_TOKEN_TYPE = "refresh"


def _create_token(data: dict, expires_delta: timedelta, token_type: str) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta
    # jti keeps each token (and its hash) unique even when two tokens for the
    # same subject share an identical `exp` second — required by the unique
    # token_hash index and refresh-token rotation.
    to_encode.update({"exp": expire, "type": token_type, "jti": uuid.uuid4().hex})
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return _create_token(data, expires_delta, ACCESS_TOKEN_TYPE)


def create_refresh_token(data: dict) -> str:
    expires_delta = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    return _create_token(data, expires_delta, REFRESH_TOKEN_TYPE)


def decode_token(token: str, expected_type: str | None = None) -> dict:
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
    except JWTError as exc:
        logger.warning("jwt_decode_failed", error=str(exc))
        raise

    if expected_type is not None and payload.get("type") != expected_type:
        logger.warning(
            "jwt_wrong_token_type",
            expected=expected_type,
            actual=payload.get("type"),
        )
        raise JWTError(
            f"Invalid token type: expected '{expected_type}', "
            f"got '{payload.get('type')}'"
        )

    return payload


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()
