"""Environment-driven application settings.

All configuration flows through here. Business logic must never read os.environ
directly or hardcode model strings — import ``settings`` instead.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Repo root is two levels above this file: backend/app/config.py -> repo root.
_REPO_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Typed, env-driven settings. Loaded once and cached."""

    model_config = SettingsConfigDict(
        env_file=_REPO_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ---- LLM provider (kept swappable; see app/llm/client.py) ----
    llm_provider: str = "groq"
    llm_model: str = "llama-3.3-70b-versatile"
    groq_api_key: str = ""
    gemini_api_key: str = ""
    llm_temperature: float = 0.7

    # ---- Orchestration knobs ----
    eval_threshold: float = 4.0
    max_iterations: int = 3

    # ---- Persistence ----
    database_url: str = "sqlite:///./marketing_copilot.db"

    # ---- App ----
    log_level: str = "INFO"

    # ---- Publishing (v2) ----
    # "stub" = simulate publishing locally (default, no API keys needed)
    # "real" = call real platform APIs (falls back to stub if keys absent)
    publishing_mode: str = "stub"

    # Twitter / X credentials (needed when publishing_mode=real)
    twitter_consumer_key: str = ""
    twitter_consumer_secret: str = ""
    twitter_access_token: str = ""
    twitter_access_token_secret: str = ""

    # LinkedIn credentials (needed when publishing_mode=real)
    linkedin_access_token: str = ""
    linkedin_author_urn: str = ""   # e.g. "urn:li:person:XXXXXXXX"


@lru_cache
def get_settings() -> Settings:
    """Return the cached settings singleton."""
    return Settings()


settings = get_settings()
