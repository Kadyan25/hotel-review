from app.config import Settings


def test_plain_postgresql_url_gets_asyncpg_driver():
    s = Settings(database_url="postgresql://user:pass@host:5432/db")
    assert s.database_url == "postgresql+asyncpg://user:pass@host:5432/db"


def test_heroku_style_postgres_url_gets_asyncpg_driver():
    s = Settings(database_url="postgres://user:pass@host:5432/db")
    assert s.database_url == "postgresql+asyncpg://user:pass@host:5432/db"


def test_already_asyncpg_url_is_unchanged():
    s = Settings(database_url="postgresql+asyncpg://user:pass@host:5432/db")
    assert s.database_url == "postgresql+asyncpg://user:pass@host:5432/db"
