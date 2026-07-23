"""Test-only DB wiring.

Windows + asyncpg + the pooled engine's pool_pre_ping combination breaks
under httpx's ASGITransport (each request rides a fresh anyio task; a
pre-ping on a connection checked out from a different task's proactor
context raises AttributeError deep in asyncpg's transport instead of
transparently reconnecting). NullPool sidesteps it entirely by never
reusing a connection across requests -- standard practice for test
suites anyway, not a workaround for anything in production code (uvicorn
runs a single persistent event loop, where the pooled engine is fine).
"""

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.config import get_settings
from app.db.session import get_db
from app.main import app

_settings = get_settings()
_test_engine = create_async_engine(_settings.database_url, poolclass=NullPool)
_test_session_maker = async_sessionmaker(_test_engine, expire_on_commit=False)


async def _get_test_db():
    async with _test_session_maker() as session:
        yield session


app.dependency_overrides[get_db] = _get_test_db
