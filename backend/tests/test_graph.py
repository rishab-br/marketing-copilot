"""Tests for the orchestration graph: the conditional edge + the full loop."""

import pytest

import app.graph.build as build
from app.graph.build import FINALIZE, REVISE, route_after_critic, run_campaign
from app.graph.state import GraphState
from app.models import (
    Asset,
    AssetResult,
    Brief,
    CampaignPlan,
    EvalScore,
    GuardrailResult,
)


@pytest.fixture
def brief() -> Brief:
    return Brief(
        brand="Acme",
        product="TaskFlow",
        goal="drive signups",
        audience="founders",
        tone="confident",
        platforms=["instagram"],
    )


def _result(*, overall_pass: bool, guardrail_pass: bool = True) -> AssetResult:
    dims = (5, 5, 5, 5) if overall_pass else (2, 2, 2, 2)
    return AssetResult(
        asset=Asset(platform="instagram", body="b", cta="c"),
        guardrail=GuardrailResult(
            passed=guardrail_pass, violations=[] if guardrail_pass else ["x"]
        ),
        score=EvalScore(
            clarity=dims[0],
            cta_strength=dims[1],
            brand_fit=dims[2],
            platform_fit=dims[3],
            rationale="r",
        ),
    )


# --------------------------------------------------------------------------- #
# route_after_critic — the conditional edge (pure function)
# --------------------------------------------------------------------------- #
def test_route_all_pass_finalizes(brief):
    state = GraphState(brief=brief, results=[_result(overall_pass=True)], iteration=1)
    assert route_after_critic(state) == FINALIZE


def test_route_fail_with_iterations_left_revises(brief):
    state = GraphState(
        brief=brief, results=[_result(overall_pass=False)], iteration=1, max_iterations=3
    )
    assert route_after_critic(state) == REVISE


def test_route_fail_out_of_iterations_finalizes(brief):
    state = GraphState(
        brief=brief, results=[_result(overall_pass=False)], iteration=3, max_iterations=3
    )
    assert route_after_critic(state) == FINALIZE


def test_route_guardrail_fail_blocks_even_if_score_ok(brief):
    # high score but a guardrail violation -> not all-pass -> revise
    state = GraphState(
        brief=brief,
        results=[_result(overall_pass=True, guardrail_pass=False)],
        iteration=1,
        max_iterations=3,
    )
    assert route_after_critic(state) == REVISE


def test_route_empty_results_follows_uniform_rule(brief):
    # No special-casing: empty results are "not all-pass". Revise while iterations
    # remain (a retry may produce assets), else finalize (flagged for the human).
    revising = GraphState(brief=brief, results=[], iteration=1, max_iterations=3)
    assert route_after_critic(revising) == REVISE

    exhausted = GraphState(brief=brief, results=[], iteration=3, max_iterations=3)
    assert route_after_critic(exhausted) == FINALIZE


# --------------------------------------------------------------------------- #
# Full graph loop — monkeypatched agents (no LLM)
# --------------------------------------------------------------------------- #
def _patch_agents(monkeypatch, *, copy_quality, critic_for):
    async def fake_strategist(brief, *, client=None):
        return CampaignPlan(
            angle="a", key_messages=["m"], per_platform_direction={"instagram": "d"}
        )

    async def fake_copywriter(brief, plan, *, prior_results=None, client=None):
        return [Asset(platform="instagram", body=copy_quality(prior_results), cta="go")]

    async def fake_critic(asset, brief, *, extra_banned_terms=None, client=None):
        return critic_for(asset)

    monkeypatch.setattr(build, "run_strategist", fake_strategist)
    monkeypatch.setattr(build, "run_copywriter", fake_copywriter)
    monkeypatch.setattr(build, "run_critic", fake_critic)


def _strong():
    return GuardrailResult(passed=True), EvalScore(
        clarity=5, cta_strength=5, brand_fit=5, platform_fit=5, rationale="great"
    )


def _weak():
    return GuardrailResult(passed=True), EvalScore(
        clarity=2, cta_strength=2, brand_fit=2, platform_fit=2, rationale="weak"
    )


async def test_loop_improves_on_revision(monkeypatch, brief):
    # weak on first draft, strong once the copywriter receives prior feedback.
    _patch_agents(
        monkeypatch,
        copy_quality=lambda prior: "good" if prior else "bad",
        critic_for=lambda asset: _strong() if asset.body == "good" else _weak(),
    )

    state = await run_campaign(brief, max_iterations=3)

    assert state.iteration == 2  # one revision was enough
    assert state.needs_human_attention is False
    assert all(r.passed(state.threshold) for r in state.results)
    assert state.results[0].iterations == 2


async def test_loop_gives_up_and_flags_after_max_iterations(monkeypatch, brief):
    # copy never improves -> exhaust iterations -> finalize with the flag set.
    _patch_agents(
        monkeypatch,
        copy_quality=lambda prior: "bad",
        critic_for=lambda asset: _weak(),
    )

    state = await run_campaign(brief, max_iterations=2)

    assert state.iteration == 2  # stopped at the cap
    assert state.needs_human_attention is True
    assert state.results  # best-so-far is still returned


async def test_first_draft_passes_no_revision(monkeypatch, brief):
    _patch_agents(
        monkeypatch,
        copy_quality=lambda prior: "good",
        critic_for=lambda asset: _strong(),
    )

    state = await run_campaign(brief, max_iterations=3)

    assert state.iteration == 1  # passed immediately
    assert state.needs_human_attention is False
