"""FastAPI application entrypoint."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import settings
from app.db import init_db
from app.routers import campaigns

logging.basicConfig(level=settings.log_level.upper())


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="Agentic Digital Marketing Copilot",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(campaigns.router)


@app.get("/health")
async def health() -> dict[str, str]:
    """Liveness probe. Reports the configured provider/model (no secrets)."""
    return {
        "status": "ok",
        "provider": settings.llm_provider,
        "model": settings.llm_model,
    }
