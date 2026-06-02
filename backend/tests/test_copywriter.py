"""Tests for the copywriter agent."""

import pytest

from app.agents.copywriter import run_copywriter
from app.models import Asset, AssetResult, Brief, CampaignPlan, EvalScore, GuardrailResult


@pytest.fixture
def brief() -> Brief:
    return Brief(
        brand="Acme",
        product="TaskFlow",
        goal="drive signups",
        audience="busy founders",
        tone="confident, friendly",
        platforms=["instagram", "linkedin"],
        brand_guidelines="No absolute claims. Avoid 'guaranteed'.",
    )


@pytest.fixture
def plan() -> CampaignPlan:
    return CampaignPlan(
        angle="Reclaim your day",
        key_messages=["Save 2 hours a day", "Built for small teams"],
        per_platform_direction={
            "instagram": "Punchy, visual, emoji-friendly",
            "linkedin": "Professional, outcome-focused",
        },
    )


def _assets_payload() -> dict:
    return {
        "assets": [
            {
                "platform": "linkedin",
                "body": "Reclaim two hours a day with TaskFlow.",
                "cta": "Start free",
                "hashtags": [],
            },
            {
                "platform": "instagram",
                "body": "Your day, back in your hands ✨",
                "cta": "Sign up",
                "hashtags": ["taskflow", "productivity"],
            },
        ]
    }


async def test_produces_one_asset_per_platform(make_client, brief, plan):
    client, _ = make_client([_assets_payload()])

    assets = await run_copywriter(brief, plan, client=client)

    assert [a.platform for a in assets] == ["instagram", "linkedin"]  # ordered by brief
    assert all(isinstance(a, Asset) for a in assets)


async def test_system_prompt_and_plan_passed_through(make_client, brief, plan):
    client, provider = make_client([_assets_payload()])

    await run_copywriter(brief, plan, client=client)

    assert "copywriter" in provider.systems[0].lower()
    sent = provider.prompts[0]
    assert "Reclaim your day" in sent  # angle
    assert "Save 2 hours a day" in sent  # key message
    assert "instagram" in sent and "linkedin" in sent


async def test_revision_pass_injects_critic_feedback(make_client, brief, plan):
    prior = [
        AssetResult(
            asset=Asset(platform="instagram", body="ok", cta="go", hashtags=[]),
            guardrail=GuardrailResult(
                passed=False, violations=["unverifiable claim: 'guaranteed results'"]
            ),
            score=EvalScore(
                clarity=2, cta_strength=2, brand_fit=2, platform_fit=3, rationale="too weak"
            ),
            iterations=1,
        )
    ]
    client, provider = make_client([_assets_payload()])

    await run_copywriter(brief, plan, prior_results=prior, client=client)

    sent = provider.prompts[0]
    assert "REVISION PASS" in sent
    assert "guaranteed results" in sent  # the violation is fed back
    assert "too weak" in sent  # the critic rationale is fed back


async def test_extra_unrequested_platform_kept_at_end(make_client, brief, plan):
    payload = _assets_payload()
    payload["assets"].append({"platform": "tiktok", "body": "extra", "cta": "go", "hashtags": []})
    client, _ = make_client([payload])

    assets = await run_copywriter(brief, plan, client=client)

    assert [a.platform for a in assets] == ["instagram", "linkedin", "tiktok"]
