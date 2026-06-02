"""Tests for the critic agent — guardrail/score separation and violation merging."""

import pytest

from app.agents.critic import run_critic
from app.models import Asset, Brief


@pytest.fixture
def brief() -> Brief:
    return Brief(
        brand="Acme",
        product="TaskFlow",
        goal="drive signups",
        audience="founders",
        tone="confident, friendly",
        platforms=["instagram"],
        brand_guidelines="No absolute claims.",
    )


def _critic_payload(violations=None, dims=(4, 4, 4, 4), rationale="solid") -> dict:
    c, cta, bf, pf = dims
    return {
        "guardrail_violations": violations or [],
        "score": {
            "clarity": c,
            "cta_strength": cta,
            "brand_fit": bf,
            "platform_fit": pf,
            "rationale": rationale,
        },
    }


async def test_clean_asset_passes_and_scores(make_client, brief):
    asset = Asset(platform="instagram", body="Save two hours a day.", cta="Start free")
    client, _ = make_client([_critic_payload(dims=(5, 4, 4, 4))])

    guardrail, score = await run_critic(asset, brief, client=client)

    assert guardrail.passed is True
    assert guardrail.violations == []
    assert score.overall == round(5 * 0.25 + 4 * 0.30 + 4 * 0.25 + 4 * 0.20, 2)


async def test_deterministic_violation_blocks_even_with_high_score(make_client, brief):
    # LLM reports no guardrail issues and a perfect score, but the copy contains a
    # banned claim -> deterministic layer must still block PASS.
    asset = Asset(platform="instagram", body="Results guaranteed!", cta="Sign up")
    client, _ = make_client([_critic_payload(violations=[], dims=(5, 5, 5, 5))])

    guardrail, score = await run_critic(asset, brief, client=client)

    assert guardrail.passed is False
    assert any("guarantee" in v for v in guardrail.violations)
    assert score.overall == 5.0  # score is independent of the guardrail outcome


async def test_merges_llm_and_deterministic_violations(make_client, brief):
    asset = Asset(platform="instagram", body="Results guaranteed!", cta="Buy")
    client, _ = make_client(
        [_critic_payload(violations=["off-tone: too aggressive"], dims=(2, 2, 2, 2))]
    )

    guardrail, _ = await run_critic(asset, brief, client=client)

    assert guardrail.passed is False
    assert any("guarantee" in v for v in guardrail.violations)  # deterministic
    assert "off-tone: too aggressive" in guardrail.violations  # from the LLM


async def test_llm_only_tone_violation(make_client, brief):
    asset = Asset(platform="instagram", body="Buy now.", cta="Buy")
    client, _ = make_client([_critic_payload(violations=["off-tone: not friendly"])])

    guardrail, _ = await run_critic(asset, brief, client=client)

    assert guardrail.passed is False
    assert guardrail.violations == ["off-tone: not friendly"]


async def test_prompt_includes_tone_and_guidelines(make_client, brief):
    asset = Asset(platform="instagram", body="Hello", cta="Go")
    client, provider = make_client([_critic_payload()])

    await run_critic(asset, brief, client=client)

    sent = provider.prompts[0]
    assert "confident, friendly" in sent  # required tone
    assert "No absolute claims." in sent  # brand guidelines
    assert "critic" in provider.systems[0].lower()
