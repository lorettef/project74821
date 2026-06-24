import os
import uuid as _uuid
from datetime import datetime, timezone

import bcrypt as _bcrypt_lib

_orig_hashpw = _bcrypt_lib.hashpw
_orig_checkpw = _bcrypt_lib.checkpw


def _safe_hashpw(password: bytes, salt: bytes) -> bytes:
    if len(password) > 72:
        password = password[:72]
    return _orig_hashpw(password, salt)


def _safe_checkpw(password: bytes, hashed_password: bytes) -> bool:
    if len(password) > 72:
        password = password[:72]
    return _orig_checkpw(password, hashed_password)


_bcrypt_lib.hashpw = _safe_hashpw
_bcrypt_lib.checkpw = _safe_checkpw

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine, event
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import Session
from sqlalchemy.pool import NullPool

from app.models.base import Base


@compiles(JSONB, "sqlite")
def _compile_jsonb_on_sqlite(type_, compiler, **kw):
    return "JSON"


@compiles(ARRAY, "sqlite")
def _compile_array_on_sqlite(type_, compiler, **kw):
    return "JSON"


def _sqlite_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class _SyncAsyncSession:
    """Bridge a synchronous SQLAlchemy Session so it satisfies the
    ``AsyncSession`` interface the application routes expect."""

    def __init__(self, sync_session: Session):
        self.sync = sync_session

    async def execute(self, *args, **kwargs):
        return self.sync.execute(*args, **kwargs)

    async def flush(self, *args, **kwargs):
        self.sync.flush(*args, **kwargs)

    async def commit(self):
        self.sync.commit()

    async def rollback(self):
        self.sync.rollback()

    def add(self, obj):
        self.sync.add(obj)

    def add_all(self, objs):
        self.sync.add_all(objs)

    async def get(self, *args, **kwargs):
        return self.sync.get(*args, **kwargs)

    async def refresh(self, *args, **kwargs):
        return self.sync.refresh(*args, **kwargs)

    async def delete(self, obj):
        self.sync.delete(obj)

    async def close(self):
        self.sync.close()


@pytest_asyncio.fixture(scope="module")
def test_engine():
    """Synchronous SQLAlchemy engine backed by a SQLite file.

    Custom SQL functions are registered so PostgreSQL-specific server
    defaults (``gen_random_uuid``, ``now``) work with SQLite.
    DateTime(timezone=True) columns loaded from SQLite are given UTC
    tzinfo so comparisons with offset-aware datetimes succeed.
    """
    db_path = os.path.join(os.getcwd(), "test.db")
    if os.path.exists(db_path):
        os.remove(db_path)

    engine = create_engine(
        "sqlite:///./test.db",
        echo=False,
        poolclass=NullPool,
        connect_args={"check_same_thread": False},
    )

    @event.listens_for(engine, "connect")
    def _register_sqlite_functions(dbapi_connection, _connection_record):
        dbapi_connection.create_function(
            "gen_random_uuid", 0, lambda: _uuid.uuid4().hex
        )
        dbapi_connection.create_function("now", 0, _sqlite_now)

    Base.metadata.create_all(engine)

    from app.models import RefreshToken

    @event.listens_for(RefreshToken, "load")
    def _fix_refresh_token_tz(instance, _context):
        if instance.expires_at is not None and instance.expires_at.tzinfo is None:
            instance.expires_at = instance.expires_at.replace(tzinfo=timezone.utc)

    yield engine

    Base.metadata.drop_all(engine)
    engine.dispose()

    if os.path.exists(db_path):
        os.remove(db_path)


@pytest_asyncio.fixture
async def test_session(test_engine):
    """Clean synchronous session backed by the test engine."""
    session = Session(test_engine, expire_on_commit=False)
    try:
        yield session
    finally:
        session.close()


@pytest_asyncio.fixture
async def client(test_engine):
    """httpx.AsyncClient wired to the FastAPI application.

    The ``get_session`` dependency is overridden so every request uses
    a synchronous SQLite session via the ``_SyncAsyncSession`` bridge.
    """
    from app.core.database import get_session
    from app.main import app

    async def _override_get_session():
        session = Session(test_engine, expire_on_commit=False)
        try:
            yield _SyncAsyncSession(session)
        finally:
            session.close()

    app.dependency_overrides[get_session] = _override_get_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
