import os

from tests.helpers import apply_bcrypt_patch, make_client, make_engine, teardown_engine

apply_bcrypt_patch()

import pytest  # noqa: E402
import pytest_asyncio  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402


@pytest_asyncio.fixture(scope="module")
def test_engine():
    """Synchronous SQLAlchemy engine backed by a SQLite file."""
    db_path = os.path.join(os.getcwd(), "test.db")
    engine = make_engine(db_path)
    yield engine
    teardown_engine(engine)


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
    a synchronous SQLite session via the ``SyncAsyncSession`` bridge.
    """
    client_gen = make_client(test_engine)
    try:
        ac = await anext(client_gen)
        yield ac
    finally:
        await client_gen.aclose()
