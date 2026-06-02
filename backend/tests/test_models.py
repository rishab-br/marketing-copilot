"""Tests for the typed agent-boundary contracts in app.models."""

import pytest
from pydantic import ValidationError

from app.models import (
    Asset,
    AssetResult,
    Brief,
    EvalScore,
    GuardrailResult,
)


# --------------------------------------------------------------------------- #
# Brief
# --------------------------------------------------------------------------- #
def test_brief_normalizes_platforms():
    brief = Brief(
        brand="Acme",
        product="Widget",
        goal="drive signups",
        audience="devs",
        tone="playful",
        platforms=["  Instagram ", "LINKEDIN", ""],
    )
    assert brief.platforms == ["instagram", "linkedin"]


def test_brief_rejects_all_empty_platforms():
    with pytest.raises(ValidationError):
        Brief(
            brand="Acme",
            product="Widget",
            goal="g",
            audience="a",
            tone="t",
            platforms=["   ", ""],
        )


# --------------------------------------------------------------------------- #
# EvalScore — overall is computed, not trusted from input
# --------------------------------------------------------------------------- #
def test_overall_computed_from_weights():
    score = EvalScore(
        clarity=4,
        cta_strength=5,
        brand_fit=4,
        platform_fit=3,
        rationale="solid",
    )
    # 4*.25 + 5*.30 + 4*.25 + 3*.20 = 1.0 + 1.5 + 1.0 + 0.6 = 4.1
    assert score.overall == 4.1


def test_overall_ignores_supplied_value():
    score = EvalScore(
        clarity=1,
        cta_strength=1,
        brand_fit=1,
        platform_fit=1,
        rationale="weak",
        overall=5.0,  # the model must ignore this and recompute -> 1.0
    )
    assert score.overall == 1.0


def test_weights_sum_to_one():
    assert round(sum(EvalScore.WEIGHTS.values()), 6) == 1.0


def test_dimension_out_of_range_rejected():
    with pytest.raises(ValidationError):
        EvalScore(clarity=6, cta_strength=3, brand_fit=3, platform_fit=3, rationale="x")


def test_meets_threshold():
    score = EvalScore(clarity=4, cta_strength=4, brand_fit=4, platform_fit=4, rationale="ok")
    assert score.overall == 4.0
    assert score.meets(4.0) is True
    assert score.meets(4.01) is False


# --------------------------------------------------------------------------- #
# GuardrailResult — passed/violations must be coherent
# --------------------------------------------------------------------------- #
def test_guardrail_passed_with_violations_rejected():
    with pytest.raises(ValidationError):
        GuardrailResult(passed=True, violations=["unverifiable claim: 'best in world'"])


def test_guardrail_failed_with_violations_ok():
    gr = GuardrailResult(passed=False, violations=["off-tone"])
    assert gr.passed is False
    assert gr.violations == ["off-tone"]


# --------------------------------------------------------------------------- #
# AssetResult — gate combines guardrail AND score
# --------------------------------------------------------------------------- #
def _asset() -> Asset:
    return Asset(platform="Instagram", body="Hello", cta="Sign up", hashtags=["launch"])


def test_asset_result_passed_requires_both():
    asset = _asset()
    assert asset.platform == "instagram"  # normalized

    strong = EvalScore(clarity=5, cta_strength=5, brand_fit=5, platform_fit=5, rationale="great")
    ok_guard = GuardrailResult(passed=True)
    bad_guard = GuardrailResult(passed=False, violations=["off-tone"])

    assert AssetResult(asset=asset, guardrail=ok_guard, score=strong).passed(4.0) is True
    # guardrail fail blocks pass even with a perfect score
    assert AssetResult(asset=asset, guardrail=bad_guard, score=strong).passed(4.0) is False
