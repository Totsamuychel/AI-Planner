from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    env: str = Field(default="dev")
    tz: str = Field(default="UTC")

    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_secret_key: str = "change-me"
    api_cors_origins: str = "http://localhost:3000"

    database_url: str = "postgresql+asyncpg://neuroplan:neuroplan@postgres:5432/neuroplan"
    sync_database_url: str = "postgresql+psycopg://neuroplan:neuroplan@postgres:5432/neuroplan"

    redis_url: str = "redis://redis:6379/0"

    obsidian_vault_path: str = "/data/vault"

    openai_api_key: str = ""
    ai_provider: str = "openai"
    ai_model: str = "gpt-4o-mini"

    ollama_base_url: str = "http://ollama:11434"
    ollama_model: str = "qwen2.5:7b"

    telegram_bot_token: str = ""
    telegram_admin_chat_id: str = ""

    # --- Google OAuth (Calendar) ---
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8000/api/v1/google/callback"
    google_post_auth_redirect: str = "http://localhost:3000/settings?google=connected"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.api_cors_origins.split(",") if o.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
