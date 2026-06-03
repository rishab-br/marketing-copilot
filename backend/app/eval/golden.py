"""Hand-labeled golden set for eval calibration.

Each case pairs a brief + a candidate asset with the expected gate outcome
(``expected_pass``). The mix is deliberate:

- Some FAILs are decidable by the deterministic guardrail layer alone (banned /
  absolute / medical claims) — these calibrate guardrails with no LLM needed.
- Others depend on the LLM judge: off-tone copy, or weak copy that should score
  below threshold.
- The PASS cases are strong, on-tone, claim-safe assets the judge should clear.

Keep this small and curated (5–10 cases) so it stays a sharp calibration signal.
"""

from __future__ import annotations

from pydantic import BaseModel

from app.models import Asset, Brief


class GoldenCase(BaseModel):
    id: str
    brief: Brief
    asset: Asset
    expected_pass: bool
    note: str  # why this is the expected outcome


_SAAS_BRIEF = Brief(
    brand="TaskFlow",
    product="TaskFlow",
    goal="drive signups",
    audience="busy startup founders",
    tone="confident, friendly",
    platforms=["linkedin"],
    brand_guidelines="No absolute or unverifiable claims. Warm, human tone.",
)

_PLAYFUL_BRIEF = Brief(
    brand="Brewly",
    product="cold brew kit",
    goal="drive online orders",
    audience="Gen-Z coffee lovers",
    tone="playful, witty, emoji-friendly",
    platforms=["instagram"],
    brand_guidelines="Light-hearted. No health claims.",
)

_FINANCE_BRIEF = Brief(
    brand="NestEgg",
    product="robo-investing app",
    goal="drive signups",
    audience="first-time investors",
    tone="trustworthy, plain-spoken",
    platforms=["linkedin"],
    brand_guidelines="Strictly no performance guarantees or get-rich claims.",
)


GOLDEN_SET: list[GoldenCase] = [
    GoldenCase(
        id="pass_saas_linkedin_strong",
        brief=_SAAS_BRIEF,
        asset=Asset(
            platform="linkedin",
            body=(
                "Your team loses hours every week to status updates and context-"
                "switching. TaskFlow keeps work in one place so founders can focus "
                "on what actually moves the business."
            ),
            cta="Start your free 14-day trial",
            hashtags=[],
        ),
        expected_pass=True,
        note="Clear, on-tone, strong CTA, no banned claims — should clear the gate.",
    ),
    GoldenCase(
        id="pass_playful_instagram_strong",
        brief=_PLAYFUL_BRIEF,
        asset=Asset(
            platform="instagram",
            body="POV: it's 7am and your cold brew is already waiting 😎☕ smooth, "
            "not bitter, zero effort.",
            cta="Tap to grab your kit",
            hashtags=["coldbrew", "coffeelover", "brewly"],
        ),
        expected_pass=True,
        note="Witty, on-tone for Gen-Z, clear CTA, safe — should pass.",
    ),
    GoldenCase(
        id="fail_banned_guaranteed",
        brief=_SAAS_BRIEF,
        asset=Asset(
            platform="linkedin",
            body="TaskFlow guarantees you'll save 10 hours a week, every week.",
            cta="Sign up now",
            hashtags=[],
        ),
        expected_pass=False,
        note="'guarantees' is an unverifiable claim — deterministic guardrail blocks it.",
    ),
    GoldenCase(
        id="fail_banned_best_in_world",
        brief=_SAAS_BRIEF,
        asset=Asset(
            platform="linkedin",
            body="The best in the world at keeping teams aligned. Nothing comes close.",
            cta="Try it free",
            hashtags=[],
        ),
        expected_pass=False,
        note="Absolute 'best in the world' claim — deterministic guardrail blocks it.",
    ),
    GoldenCase(
        id="fail_finance_get_rich",
        brief=_FINANCE_BRIEF,
        asset=Asset(
            platform="linkedin",
            body="Double your money risk-free with NestEgg — get rich while you sleep.",
            cta="Open an account",
            hashtags=[],
        ),
        expected_pass=False,
        note="Financial 'double your money', 'risk-free', 'get rich' — guardrail blocks.",
    ),
    GoldenCase(
        id="fail_off_tone_playful_brief",
        brief=_PLAYFUL_BRIEF,
        asset=Asset(
            platform="instagram",
            body=(
                "Brewly Cold Brew Kit. A premium beverage preparation solution "
                "engineered for optimal extraction efficiency and operational "
                "convenience."
            ),
            cta="Purchase now",
            hashtags=[],
        ),
        expected_pass=False,
        note="Dry, corporate copy violates the playful/witty tone — judge should flag.",
    ),
    GoldenCase(
        id="fail_weak_vague_cta",
        brief=_SAAS_BRIEF,
        asset=Asset(
            platform="linkedin",
            body="TaskFlow is a tool. It does things for teams. Pretty useful overall.",
            cta="Learn more maybe",
            hashtags=[],
        ),
        expected_pass=False,
        note="Vague body, weak CTA — should score below threshold even if claim-safe.",
    ),
    GoldenCase(
        id="fail_medical_cure_claim",
        brief=_PLAYFUL_BRIEF,
        asset=Asset(
            platform="instagram",
            body="This cold brew is a miracle cure for tiredness — never fails! ✨",
            cta="Order yours",
            hashtags=["coldbrew"],
        ),
        expected_pass=False,
        note="'miracle cure' + 'never fails' health claims — guardrail blocks.",
    ),
]
