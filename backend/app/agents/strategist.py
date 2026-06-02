"""Strategist agent: Brief -> CampaignPlan.

First node in the graph; its plan steers the copywriter. Platform direction keys
are normalized to lowercase so they line up with normalized Brief/Asset platforms.
"""

from __future__ import annotations

from app.llm.client import LLMClient, get_llm_client
from app.llm.prompts import strategist as prompt
from app.models import Brief, CampaignPlan


async def run_strategist(
    brief: Brief,
    *,
    client: LLMClient | None = None,
) -> CampaignPlan:
    """Produce a schema-validated campaign plan from the brief."""
    client = client or get_llm_client()
    plan = await client.generate_json(
        prompt=prompt.build_prompt(brief, CampaignPlan.model_json_schema()),
        response_model=CampaignPlan,
        system=prompt.SYSTEM,
    )
    # Normalize direction keys to match normalized platform names.
    plan.per_platform_direction = {
        platform.strip().lower(): direction
        for platform, direction in plan.per_platform_direction.items()
    }
    return plan
