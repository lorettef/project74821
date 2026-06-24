#!/usr/bin/env python3
"""Standalone test runner — no pytest required.

DNS is unreliable in this environment so pip-installing pytest /
pytest-asyncio / aiosqlite is impossible.  This script manually
orchestrates the same fixtures as :file:`conftest.py` and runs every
test function in :file:`test_auth.py`, :file:`test_health.py`,
and :file:`test_companies.py`.
"""
from __future__ import annotations

import asyncio
import inspect
import os
import sys
import traceback

# Ensure the backend package is importable.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from tests.helpers import apply_bcrypt_patch, make_client, make_engine, teardown_engine  # noqa: E402

apply_bcrypt_patch()


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

    db_path = os.path.join(os.getcwd(), "test.db")
    engine = make_engine(db_path)
    client_gen = make_client(engine)
    client = await anext(client_gen)

    try:
        # Discover tests from test modules.
        import tests.test_auth as auth_mod
        import tests.test_health as health_mod
        import tests.test_companies as companies_mod

        auth_tests = list(_discover_test_funcs(auth_mod))
        health_tests = list(_discover_test_funcs(health_mod))
        companies_tests = list(_discover_test_funcs(companies_mod))

        # Also pick up class methods from each module.
        def _collect_class_tests(mod):
            collected = []
            for name, cls in inspect.getmembers(mod, inspect.isclass):
                if name.startswith("Test"):
                    instance = cls()
                    for mname, method in inspect.getmembers(instance, inspect.iscoroutinefunction):
                        if mname.startswith("test_"):
                            collected.append((f"{name}.{mname}", method))
            return collected

        auth_tests += _collect_class_tests(auth_mod)
        health_tests += _collect_class_tests(health_mod)
        companies_tests += _collect_class_tests(companies_mod)

        all_tests = auth_tests + health_tests + companies_tests

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
        teardown_engine(engine)


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
