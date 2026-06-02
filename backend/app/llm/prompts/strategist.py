"""Strategist agent prompt: Brief -> CampaignPlan."""

from __future__ import annotations

import json

from app.models import Brief

SYSTEM = (
    "You are a senior marketing strategist. Given a campaign brief, you produce a "
    "tight campaign plan: a single compelling angle, a few sharp key messages, and "
    "concrete creative direction for EACH target platform. You are specific and "
    "actionable, never generic. Always return valid JSON matching the schema — no "
    "prose, no markdown."
)


def build_prompt(brief: Brief, response_schema: dict) -> str:
    """Build the strategist user prompt."""
    guidelines = brief.brand_guidelines or "(none provided)"
    return "\n".join(
        [
            "Create a campaign plan for the following brief.",
            "",
            "## Campaign brief",
            f"- Brand: {brief.brand}",
            f"- Product: {brief.product}",
            f"- Goal: {brief.goal}",
            f"- Audience: {brief.audience}",
            f"- Tone: {brief.tone}",
            f"- Target platforms: {', '.join(brief.platforms)}",
            f"- Brand guidelines: {guidelines}",
            "",
            "## Requirements",
            "- angle: one sharp, differentiated campaign idea.",
            "- key_messages: 2-4 concise messages that ladder up to the goal.",
            "- per_platform_direction: a concrete direction for EACH target platform, "
            "keyed by the exact lowercase platform name.",
            "",
            "## Output format",
            "Return ONLY a JSON object matching this schema:",
            json.dumps(response_schema, indent=2),
        ]
    )
