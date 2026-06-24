"""Shared test utilities for both pytest conftest.py and standalone runner.

All bcrypt monkey-patching, SQL compiler hooks, engine/client factories,
and the SyncAsyncSession bridge live here so they are defined once.
"""

from __future__ import annotations

import os
import uuid as _uuid
from datetime import datetime, timezone

import bcrypt as _bcrypt_lib

_orig_hashpw = _bcrypt_lib.hashpw
_orig_checkpw = _bcrypt_lib.checkpw
_bcrypt_patched = False


def apply_bcrypt_patch() -> None:
    """Monkey-patch bcrypt to truncate passwords longer than 72 bytes.

    bcrypt 5.0.0 enforces a 72-byte password limit, but passlib's
    ``detect_wrap_bug`` sends a 255-byte test password.  Call this
    **once** before importing any application code.
    """
    global _bcrypt_patched
    if _bcrypt_patched:
        return

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
    _bcrypt_patched = True


# ------------------------------------------------------------------
#  SQLAlchemy compiler hooks — auto-register at import time
# ------------------------------------------------------------------

from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy import create_engine, event  # noqa: E402
from sqlalchemy.dialects.postgresql import ARRAY, JSONB  # noqa: E402
from sqlalchemy.ext.compiler import compiles  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402
from sqlalchemy.pool import NullPool  # noqa: E402


@compiles(JSONB, "sqlite")
def _compile_jsonb_on_sqlite(type_, compiler, **kw):
    return "JSON"


@compiles(ARRAY, "sqlite")
def _compile_array_on_sqlite(type_, compiler, **kw):
    return "JSON"


# ------------------------------------------------------------------
#  Utilities
# ------------------------------------------------------------------


def sqlite_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class SyncAsyncSession:
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


# ------------------------------------------------------------------
#  Engine factory
# ------------------------------------------------------------------


def make_engine(db_path: str):
    """Create a synchronous SQLAlchemy engine backed by a SQLite file.

    Custom SQL functions are registered so PostgreSQL-specific server
    defaults (``gen_random_uuid``, ``now``) work with SQLite.
    ``DateTime(timezone=True)`` columns loaded from SQLite are given
    UTC tzinfo so comparisons with offset-aware datetimes succeed.
    """
    if os.path.exists(db_path):
        os.remove(db_path)

    engine = create_engine(
        f"sqlite:///{db_path}",
        echo=False,
        poolclass=NullPool,
        connect_args={"check_same_thread": False},
    )

    @event.listens_for(engine, "connect")
    def _register_sqlite_functions(dbapi_connection, _connection_record):
        dbapi_connection.create_function("gen_random_uuid", 0, lambda: _uuid.uuid4().hex)
        dbapi_connection.create_function("now", 0, sqlite_now)

    from app.models.base import Base

    Base.metadata.create_all(engine)

    from app.models import RefreshToken

    @event.listens_for(RefreshToken, "load")
    def _fix_refresh_token_tz(instance, _context):
        if instance.expires_at is not None and instance.expires_at.tzinfo is None:
            instance.expires_at = instance.expires_at.replace(tzinfo=timezone.utc)

    return engine


def teardown_engine(engine) -> None:
    """Drop all tables, dispose the engine, and remove the SQLite file."""
    from app.models.base import Base

    Base.metadata.drop_all(engine)
    engine.dispose()
    db_path = os.path.join(os.getcwd(), "test.db")
    if os.path.exists(db_path):
        os.remove(db_path)


# ------------------------------------------------------------------
#  HTTP client factory
# ------------------------------------------------------------------


async def make_client(engine):
    """Async generator yielding an ``httpx.AsyncClient`` wired to the
    FastAPI application.

    The ``get_session`` dependency is overridden so every request uses
    a synchronous SQLite session via the ``SyncAsyncSession`` bridge.
    """
    from app.core.database import get_session
    from app.main import app

    async def _override_get_session():
        session = Session(engine, expire_on_commit=False)
        try:
            yield SyncAsyncSession(session)
        finally:
            session.close()

    app.dependency_overrides[get_session] = _override_get_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
