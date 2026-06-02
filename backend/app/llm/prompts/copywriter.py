"""Copywriter agent prompt.

Kept out of agent logic so prompts can be versioned independently (v2). The
agent imports ``SYSTEM`` and ``build_prompt`` from here.
"""

from __future__ import annotations

import json

from app.models import AssetResult, Brief, CampaignPlan

SYSTEM = (
    "You are an expert direct-response marketing copywriter. You write concise, "
    "on-brand, platform-native copy that drives the campaign goal. You follow the "
    "campaign plan, match the requested tone exactly, and never invent unverifiable "
    "or absolute claims (e.g. 'best in the world', 'guaranteed'). You always return "
    "valid JSON that conforms to the requested schema — no prose, no markdown."
)


def build_prompt(
    brief: Brief,
    plan: CampaignPlan,
    response_schema: dict,
    prior_results: list[AssetResult] | None = None,
) -> str:
    """Build the copywriter user prompt.

    On a revision pass (``prior_results`` provided), the prior draft and the
    critic's feedback are injected per platform so the model improves rather than
    regenerating blind.
    """
    directions = "\n".join(
        f"  - {platform}: {direction}"
        for platform, direction in plan.per_platform_direction.items()
    )
    key_messages = "\n".join(f"  - {m}" for m in plan.key_messages)
    guidelines = brief.brand_guidelines or "(none provided)"

    parts = [
        "Write one marketing asset for EACH of the target platforms below.",
        "",
        "## Campaign brief",
        f"- Brand: {brief.brand}",
        f"- Product: {brief.product}",
        f"- Goal: {brief.goal}",
        f"- Audience: {brief.audience}",
        f"- Tone: {brief.tone}",
        f"- Target platforms: {', '.join(brief.platforms)}",
        f"- Brand guidelines / banned claims: {guidelines}",
        "",
        "## Campaign plan",
        f"- Angle: {plan.angle}",
        "- Key messages:",
        key_messages,
        "- Per-platform direction:",
        directions,
    ]

    if prior_results:
        parts += [
            "",
            "## REVISION PASS — improve the prior drafts using the critic's feedback",
            "Address every violation and raise the weak rubric dimensions. Keep what worked.",
        ]
        for r in prior_results:
            violations = "; ".join(r.guardrail.violations) or "(none)"
            parts += [
                "",
                f"### Prior draft for {r.asset.platform}",
                f"- Body: {r.asset.body}",
                f"- CTA: {r.asset.cta}",
                f"- Hashtags: {', '.join(r.asset.hashtags) or '(none)'}",
                f"- Guardrail violations to fix: {violations}",
                (
                    f"- Scores (1-5): clarity={r.score.clarity}, "
                    f"cta_strength={r.score.cta_strength}, brand_fit={r.score.brand_fit}, "
                    f"platform_fit={r.score.platform_fit}"
                ),
                f"- Critic rationale: {r.score.rationale}",
            ]

    parts += [
        "",
        "## Output format",
        "Return ONLY a JSON object with an `assets` array containing exactly one "
        "object per target platform, matching this JSON schema:",
        json.dumps(response_schema, indent=2),
        "",
        "Rules: write platform-appropriate length and style; make the CTA align with "
        "the goal; include hashtags only where the platform expects them; use the "
        "normalized lowercase platform names from the target platforms list.",
    ]
    return "\n".join(parts)
