from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class WorkerSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    env: str = "dev"
    tz: str = "UTC"
    redis_url: str = "redis://redis:6379/0"
    database_url: str = "postgresql+asyncpg://neuroplan:neuroplan@postgres:5432/neuroplan"


@lru_cache(maxsize=1)
def get_settings() -> WorkerSettings:
    return WorkerSettings()
