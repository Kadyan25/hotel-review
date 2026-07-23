from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://azzurro:azzurro@localhost:5437/azzurro_reviews"

    @field_validator("database_url")
    @classmethod
    def _use_asyncpg_driver(cls, v: str) -> str:
        # Railway (and Heroku-style hosts) hand out a plain postgresql://
        # or postgres:// URL with no driver suffix -- SQLAlchemy then
        # defaults to psycopg2, which isn't installed (this app is
        # asyncpg-only throughout). Normalize once here so every caller
        # (app engine, alembic env.py, scripts) gets the right dialect
        # without needing to know about this quirk.
        for prefix in ("postgresql://", "postgres://"):
            if v.startswith(prefix):
                return "postgresql+asyncpg://" + v[len(prefix) :]
        return v

    anthropic_api_key: str | None = None
    apify_api_token: str | None = None

    enable_llm_classification: bool = False
    max_llm_classifications: int = 50
    max_reviews_per_property_apify: int = 500
    scrape_max_pages_per_run: int = 15
    scrape_lookback_days: int = 30
    scrape_full_history: bool = False
    scrape_headless: bool = True
    # Off by default -- the whole point of "scraper runs locally, not from
    # the cloud-hosted API" (see architecture.md) is protecting the
    # residential-IP advantage. Local/demo use can turn this on; a public
    # Railway deployment should never set it.
    enable_scrape_endpoint: bool = False

    allowed_origins: str = "http://localhost:5173"

    @property
    def allowed_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]

    @property
    def llm_configured(self) -> bool:
        return bool(self.anthropic_api_key) and self.enable_llm_classification

    @property
    def apify_configured(self) -> bool:
        return bool(self.apify_api_token)


@lru_cache
def get_settings() -> Settings:
    return Settings()
