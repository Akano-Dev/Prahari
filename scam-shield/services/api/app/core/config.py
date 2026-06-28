"""Runtime settings, read from the environment with safe local defaults.

We deliberately avoid ``pydantic-settings`` so the API boots with only FastAPI +
Pydantic installed. ``DATABASE_URL`` / ``REDIS_URL`` being unset selects the
in-memory repository / broker, so the app runs out of the box; set them to switch
to Postgres / Redis in production.
"""
from __future__ import annotations

import os
from functools import lru_cache


class Settings:
    def __init__(self) -> None:
        self.app_name = "ScamShield API"
        self.jwt_secret = os.environ.get("SCAMSHIELD_JWT_SECRET", "dev-insecure-change-me")
        self.jwt_expires_seconds = int(os.environ.get("SCAMSHIELD_JWT_EXPIRES", "3600"))
        # None => in-memory implementations (default, runs anywhere).
        self.database_url = os.environ.get("DATABASE_URL") or None
        self.redis_url = os.environ.get("REDIS_URL") or None
        self.llm_provider = os.environ.get("SCAMSHIELD_LLM_PROVIDER", "deterministic-stub")
        self.llm_model = os.environ.get("SCAMSHIELD_LLM_MODEL", "claude-opus-4-8")
        # Read both common key names so `claude`/`openai` work without extra config.
        self.llm_api_key = (os.environ.get("ANTHROPIC_API_KEY")
                            or os.environ.get("OPENAI_API_KEY") or None)
        self.cors_origins = os.environ.get("SCAMSHIELD_CORS_ORIGINS", "*").split(",")

    @property
    def using_postgres(self) -> bool:
        return bool(self.database_url)

    @property
    def using_redis(self) -> bool:
        return bool(self.redis_url)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
