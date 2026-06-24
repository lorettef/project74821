#!/usr/bin/env python3
"""Standalone test runner — no pytest required.

DNS is unreliable in this environment so pip-installing pytest /
pytest-asyncio / aiosqlite is impossible.  This script manually
orchestrates the same fixtures as :file:`conftest.py` and runs every
test function in :file:`test_auth.py` and :file:`test_health.py`.
"""
from __future__ import annotations

import asyncio
import inspect
import os
import sys
import traceback
import uuid as _uuid
from datetime import datetime, timezone

# ------------------------------------------------------------------
#  bcrypt 5.0.0 enforces a 72-byte password limit, but passlib's
#  detect_wrap_bug sends a 255-byte test password.  Monkey-patch
#  bcrypt to silently truncate long passwords before the app imports.
# ------------------------------------------------------------------
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

from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine, event
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import Session
from sqlalchemy.pool import NullPool

# Ensure the backend package is importable.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.models.base import Base


@compiles(JSONB, "sqlite")
def _compile_jsonb_on_sqlite(type_, compiler, **kw):
    return "JSON"


@compiles(ARRAY, "sqlite")
def _compile_array_on_sqlite(type_, compiler, **kw):
    return "JSON"


# ──────────────────────────────────────────────────────────────────
#  Replicas of conftest.py helpers
# ──────────────────────────────────────────────────────────────────


def _sqlite_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class _SyncAsyncSession:
    """Bridge synchronous Session → async interface for FastAPI routes."""

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


# ──────────────────────────────────────────────────────────────────
#  Fixture factory
# ──────────────────────────────────────────────────────────────────


def _make_engine():
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
        dbapi_connection.create_function("gen_random_uuid", 0, lambda: _uuid.uuid4().hex)
        dbapi_connection.create_function("now", 0, _sqlite_now)

    Base.metadata.create_all(engine)

    from app.models import RefreshToken

    @event.listens_for(RefreshToken, "load")
    def _fix_refresh_token_tz(instance, _context):
        if instance.expires_at is not None and instance.expires_at.tzinfo is None:
            instance.expires_at = instance.expires_at.replace(tzinfo=timezone.utc)

    return engine


def _teardown_engine(engine):
    Base.metadata.drop_all(engine)
    engine.dispose()
    db_path = os.path.join(os.getcwd(), "test.db")
    if os.path.exists(db_path):
        os.remove(db_path)


async def _make_client(engine):
    from app.core.database import get_session
    from app.main import app

    async def _override_get_session():
        session = Session(engine, expire_on_commit=False)
        try:
            yield _SyncAsyncSession(session)
        finally:
            session.close()

    app.dependency_overrides[get_session] = _override_get_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()


# ──────────────────────────────────────────────────────────────────
#  Discovery & execution
# ──────────────────────────────────────────────────────────────────


def _discover_test_funcs(module):
    """Yield (name, async_func) for every ``async def test_*`` in *module*."""
    for name, obj in inspect.getmembers(module):
        if name.startswith("test_") and inspect.iscoroutinefunction(obj):
            yield name, obj


async def _run_one(name: str, func, client) -> tuple[str, bool, str | None]:
    try:
        sig = inspect.signature(func)
        params = list(sig.parameters.keys())
        # Support both "self" (class methods) and plain functions.
        if params == ["self", "client"] or params == ["client"]:
            await func(client)
        elif params == ["self"]:
            await func()
        else:
            await func()
        return name, True, None
    except Exception:
        return name, False, traceback.format_exc()


async def main() -> int:
    print("=" * 60)
    print("  Startup Engine Backend — Test Suite")
    print("=" * 60)

    engine = _make_engine()
    client_gen = _make_client(engine)
    client = await anext(client_gen)

    try:
        # Discover tests from the two test modules.
        import tests.test_auth as auth_mod
        import tests.test_health as health_mod

        auth_tests = list(_discover_test_funcs(auth_mod))
        health_tests = list(_discover_test_funcs(health_mod))

        # Also pick up TestAuthFlow class methods.
        for name, cls in inspect.getmembers(auth_mod, inspect.isclass):
            if name.startswith("Test"):
                instance = cls()
                for mname, method in inspect.getmembers(instance, inspect.iscoroutinefunction):
                    if mname.startswith("test_"):
                        auth_tests.append((f"{name}.{mname}", method))

        # Also pick up TestHealth class methods.
        for name, cls in inspect.getmembers(health_mod, inspect.isclass):
            if name.startswith("Test"):
                instance = cls()
                for mname, method in inspect.getmembers(instance, inspect.iscoroutinefunction):
                    if mname.startswith("test_"):
                        health_tests.append((f"{name}.{mname}", method))

        all_tests = auth_tests + health_tests

        passed = 0
        failed = 0
        failures: list[str] = []

        for test_name, test_func in all_tests:
            name, ok, tb = await _run_one(test_name, test_func, client)
            status = "PASS" if ok else "FAIL"
            print(f"  [{status}] {name}")
            if ok:
                passed += 1
            else:
                failed += 1
                failures.append((name, tb))

        print()
        print(f"  Results: {passed} passed, {failed} failed out of {len(all_tests)}")

        if failures:
            print()
            print("  FAILURES:")
            for fname, ftb in failures:
                print(f"    --- {fname} ---")
                print(ftb)
            return 1

        print("  All tests passed!")
        return 0
    finally:
        await client.aclose()
        try:
            await client_gen.aclose()
        except Exception:
            pass
        _teardown_engine(engine)


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
