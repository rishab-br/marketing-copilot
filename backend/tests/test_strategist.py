"""Tests for the strategist agent."""

import pytest

from app.agents.strategist import run_strategist
from app.models import Brief, CampaignPlan


@pytest.fixture
def brief() -> Brief:
    return Brief(
        brand="Acme",
        product="TaskFlow",
        goal="drive signups",
        audience="busy founders",
        tone="confident, friendly",
        platforms=["instagram", "linkedin"],
        brand_guidelines="No absolute claims.",
    )


def _plan_payload() -> dict:
    return {
        "angle": "Reclaim your day",
        "key_messages": ["Save 2 hours a day", "Built for small teams"],
        "per_platform_direction": {
            "Instagram": "Punchy, visual, emoji-friendly",  # mixed case on purpose
            "LinkedIn": "Professional, outcome-focused",
        },
    }


async def test_returns_campaign_plan(make_client, brief):
    client, _ = make_client([_plan_payload()])

    plan = await run_strategist(brief, client=client)

    assert isinstance(plan, CampaignPlan)
    assert plan.angle == "Reclaim your day"
    assert len(plan.key_messages) == 2


async def test_direction_keys_normalized_to_lowercase(make_client, brief):
    client, _ = make_client([_plan_payload()])

    plan = await run_strategist(brief, client=client)

    assert set(plan.per_platform_direction) == {"instagram", "linkedin"}


async def test_prompt_includes_brief_fields(make_client, brief):
    client, provider = make_client([_plan_payload()])

    await run_strategist(brief, client=client)

    sent = provider.prompts[0]
    assert "TaskFlow" in sent
    assert "drive signups" in sent
    assert "instagram" in sent and "linkedin" in sent
    assert "strategist" in provider.systems[0].lower()
