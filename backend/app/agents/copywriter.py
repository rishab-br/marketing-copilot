"""Copywriter agent: Brief + CampaignPlan -> one Asset per platform.

On a revision pass it also takes the prior AssetResults (draft + critic feedback)
so it improves rather than regenerating blind (CLAUDE.md §8).
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.llm.client import LLMClient, get_llm_client
from app.llm.prompts import copywriter as prompt
from app.models import Asset, AssetResult, Brief, CampaignPlan


class CopywriterOutput(BaseModel):
    """Transport shape for structured output: a list of assets."""

    assets: list[Asset] = Field(..., description="One asset per target platform.")


async def run_copywriter(
    brief: Brief,
    plan: CampaignPlan,
    *,
    prior_results: list[AssetResult] | None = None,
    client: LLMClient | None = None,
) -> list[Asset]:
    """Draft (or revise) platform-specific assets, schema-validated.

    Returns assets ordered to match ``brief.platforms``; any platform the model
    omitted is simply absent (the critic/graph decide what to do about that).
    """
    client = client or get_llm_client()
    user_prompt = prompt.build_prompt(
        brief=brief,
        plan=plan,
        response_schema=CopywriterOutput.model_json_schema(),
        prior_results=prior_results,
    )
    output = await client.generate_json(
        prompt=user_prompt,
        response_model=CopywriterOutput,
        system=prompt.SYSTEM,
    )
    return _order_by_brief(output.assets, brief.platforms)


def _order_by_brief(assets: list[Asset], platforms: list[str]) -> list[Asset]:
    """Order assets to follow the brief's platform order; keep extras at the end."""
    by_platform: dict[str, Asset] = {a.platform: a for a in assets}
    ordered = [by_platform[p] for p in platforms if p in by_platform]
    extras = [a for a in assets if a.platform not in set(platforms)]
    return ordered + extras
