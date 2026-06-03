"""LangGraph state object for a campaign run."""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.config import settings
from app.models import Asset, AssetResult, Brief, CampaignPlan


class GraphState(BaseModel):
    """State threaded through the orchestration graph.

    ``iteration`` counts completed copywriter passes (1 after the first draft).
    The loop gate compares each result's overall score against ``threshold`` and
    stops after ``max_iterations`` passes, flagging ``needs_human_attention`` if
    the assets never all passed.
    """

    brief: Brief
    plan: CampaignPlan | None = None
    current_assets: list[Asset] = Field(default_factory=list)
    results: list[AssetResult] = Field(default_factory=list)
    iteration: int = 0
    max_iterations: int = Field(default_factory=lambda: settings.max_iterations)
    threshold: float = Field(default_factory=lambda: settings.eval_threshold)
    needs_human_attention: bool = False
