"""Tests for deterministic guardrail checks (no LLM)."""

import pytest

from app.guardrails.checks import find_banned_claims, run_guardrail_checks
from app.models import Asset


@pytest.mark.parametrize(
    "text",
    [
        "Results guaranteed!",
        "The best in the world.",
        "We are number one.",
        "100% effective",
        "A risk-free trial",
        "This miracle cure works",
        "Double your money fast",
    ],
)
def test_flags_banned_claims(text):
    assert find_banned_claims(text), f"expected a violation for: {text!r}"


@pytest.mark.parametrize(
    "text",
    [
        "Save two hours a day with TaskFlow.",
        "Built for small teams who care about their time.",
        "Join thousands of happy founders.",
    ],
)
def test_clean_copy_has_no_violations(text):
    assert find_banned_claims(text) == []


def test_case_insensitive():
    assert find_banned_claims("GUARANTEED savings")


def test_run_guardrail_checks_scans_body_cta_hashtags():
    asset = Asset(
        platform="instagram",
        body="Totally normal body",
        cta="Get your risk-free trial",  # violation in CTA
        hashtags=["guaranteed"],  # violation in hashtag
    )
    violations = run_guardrail_checks(asset)
    assert any("risk-free" in v for v in violations)
    assert any("guarantee" in v for v in violations)


def test_extra_banned_terms():
    asset = Asset(platform="linkedin", body="Try our synergy platform", cta="Buy")
    violations = run_guardrail_checks(asset, extra_banned_terms=["synergy"])
    assert any("synergy" in v for v in violations)


def test_no_duplicate_messages():
    asset = Asset(platform="x", body="guaranteed guaranteed guaranteed", cta="go")
    violations = run_guardrail_checks(asset)
    assert len(violations) == 1
