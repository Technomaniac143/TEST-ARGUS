from functools import lru_cache

from dotenv import load_dotenv
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()


class Settings(BaseSettings):
    """Runtime configuration with SQLite fallback for local development."""

    app_name: str = "ARGUS Backend"
    database_url: str = Field(
        default="sqlite:///./argus.db",
        validation_alias="DATABASE_URL",
    )
    cors_allowed_origins: str = Field(
        default=(
            "http://localhost:3000,"
            "http://127.0.0.1:3000,"
            "http://localhost:3001,"
            "http://127.0.0.1:3001,"
            "http://localhost:3100,"
            "http://127.0.0.1:3100,"
            "https://argus-frontend-seven.vercel.app,"
            "null"
        ),
        validation_alias="CORS_ALLOWED_ORIGINS",
    )
    argus_mode: str = Field(default="auto", validation_alias="ARGUS_MODE")
    request_timeout_seconds: float = 12.0
    argus_search_timeout_seconds: float = Field(default=10.0, validation_alias="ARGUS_SEARCH_TIMEOUT_SECONDS")
    enable_live_search: bool = Field(default=False, validation_alias="ENABLE_LIVE_SEARCH")
    argus_offline_mode: bool = Field(default=True, validation_alias="ARGUS_OFFLINE_MODE")
    argus_demo_mode: bool = Field(default=True, validation_alias="ARGUS_DEMO_MODE")
    argus_max_concurrency: int = Field(default=5, validation_alias="ARGUS_MAX_CONCURRENCY")
    argus_cache_ttl_seconds: int = Field(default=86400, validation_alias="ARGUS_CACHE_TTL_SECONDS")
    argus_crawl_cache_ttl_seconds: int = Field(default=86400, validation_alias="ARGUS_CRAWL_CACHE_TTL_SECONDS")
    argus_max_source_targets: int = Field(default=5, validation_alias="ARGUS_MAX_SOURCE_TARGETS")
    argus_max_results_per_source: int = Field(default=10, validation_alias="ARGUS_MAX_RESULTS_PER_SOURCE")
    argus_max_source_queries: int = Field(default=12, validation_alias="ARGUS_MAX_SOURCE_QUERIES")
    argus_max_results_per_query: int = Field(default=10, validation_alias="ARGUS_MAX_RESULTS_PER_QUERY")
    argus_max_pages_per_site: int = Field(default=4, validation_alias="ARGUS_MAX_PAGES_PER_SITE")
    argus_max_pages_per_source: int = Field(default=3, validation_alias="ARGUS_MAX_PAGES_PER_SOURCE")
    argus_production_safe_mode: bool = Field(default=False, validation_alias="ARGUS_PRODUCTION_SAFE_MODE")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @field_validator("database_url", mode="before")
    @classmethod
    def use_sqlite_when_blank(cls, value: str | None) -> str:
        if not value:
            return "sqlite:///./argus.db"
        database_url = value.strip()
        if database_url.startswith("postgres://"):
            return database_url.replace("postgres://", "postgresql+psycopg://", 1)
        if database_url.startswith("postgresql://"):
            return database_url.replace("postgresql://", "postgresql+psycopg://", 1)
        return database_url

    @field_validator("argus_mode", mode="before")
    @classmethod
    def normalize_mode(cls, value: str | None) -> str:
        mode = (value or "auto").strip().lower()
        if mode not in {"online", "offline", "demo", "auto"}:
            return "auto"
        return mode


@lru_cache
def get_settings() -> Settings:
    return Settings()
