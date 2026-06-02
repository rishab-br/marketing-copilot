"""Brand-Safety Critic + eval-judge prompt.

The critic does two jobs and must keep them separate in its output (CLAUDE.md §7):
  (a) flag tone / brand-guideline violations -> guardrail_violations
  (b) score the asset on the rubric -> score (EvalScore)

Deterministic banned-claim detection happens separately in guardrails/checks.py
and is merged by the agent; the prompt tells the model to focus on tone and
brand-guideline adherence so the two layers complement rather than duplicate.
"""

from __future__ import annotations

import json

from app.models import Asset, Brief

SYSTEM = (
    "You are a meticulous brand-safety critic and marketing-quality judge. You do "
    "two separate jobs: (1) flag any TONE or BRAND-GUIDELINE violations as short "
    "strings, and (2) score the asset on a 1-5 rubric with a brief rationale. Be "
    "strict but fair. Off-tone copy is a guardrail violation, not merely a low "
    "score. Do not restate generic banned-claim issues; focus on tone and the "
    "brand's stated guidelines. Always return valid JSON matching the schema — no "
    "prose, no markdown."
)


def build_prompt(asset: Asset, brief: Brief, response_schema: dict) -> str:
    """Build the critic user prompt for a single asset."""
    guidelines = brief.brand_guidelines or "(none provided)"
    hashtags = ", ".join(asset.hashtags) or "(none)"

    return "\n".join(
        [
            "Evaluate the following marketing asset against the brief.",
            "",
            "## Brief context",
            f"- Brand: {brief.brand}",
            f"- Product: {brief.product}",
            f"- Goal: {brief.goal}",
            f"- Audience: {brief.audience}",
            f"- Required tone: {brief.tone}",
            f"- Brand guidelines: {guidelines}",
            "",
            "## Asset under review",
            f"- Platform: {asset.platform}",
            f"- Body: {asset.body}",
            f"- CTA: {asset.cta}",
            f"- Hashtags: {hashtags}",
            "",
            "## Your two jobs",
            "1. guardrail_violations: list short strings for any TONE mismatch or "
            "BRAND-GUIDELINE breach. Empty list if none.",
            "2. score: rate clarity, cta_strength, brand_fit, platform_fit (each "
            "1-5) and give a one-sentence rationale.",
            "",
            "## Output format",
            "Return ONLY a JSON object matching this schema:",
            json.dumps(response_schema, indent=2),
        ]
    )
