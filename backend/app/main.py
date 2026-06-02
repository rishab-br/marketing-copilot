"""FastAPI application entrypoint.

v1 exposes ``GET /health`` as the first route; agent + campaign routes are added
in later build steps.
"""

from __future__ import annotations

import logging

from fastapi import FastAPI

from app.config import settings

logging.basicConfig(level=settings.log_level.upper())

app = FastAPI(title="Agentic Digital Marketing Copilot", version="0.1.0")


@app.get("/health")
async def health() -> dict[str, str]:
    """Liveness probe. Reports the configured provider/model (no secrets)."""
    return {
        "status": "ok",
        "provider": settings.llm_provider,
        "model": settings.llm_model,
    }
