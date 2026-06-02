"""Brand-Safety Critic agent.

Combines two layers into the critic's two separate outputs (CLAUDE.md §7):
  - GuardrailResult: deterministic banned-claim checks (guardrails/checks.py)
    MERGED with the LLM's tone / brand-guideline violations.
  - EvalScore: the LLM rubric judge's per-dimension scores + rationale.

A guardrail failure must force a revision regardless of score, so the gate
treats these independently (see AssetResult.passed).
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.guardrails.checks import run_guardrail_checks
from app.llm.client import LLMClient, get_llm_client
from app.llm.prompts import critic as prompt
from app.models import Asset, Brief, EvalScore, GuardrailResult


class CriticOutput(BaseModel):
    """Structured critic output — guardrail and score kept separate."""

    guardrail_violations: list[str] = Field(
        default_factory=list,
        description="Tone / brand-guideline violations. Empty if none.",
    )
    score: EvalScore = Field(..., description="Rubric scores + rationale for the asset.")


async def run_critic(
    asset: Asset,
    brief: Brief,
    *,
    extra_banned_terms: list[str] | None = None,
    client: LLMClient | None = None,
) -> tuple[GuardrailResult, EvalScore]:
    """Critique one asset. Returns (GuardrailResult, EvalScore) as separate outputs."""
    client = client or get_llm_client()

    # Layer 1: deterministic, no LLM.
    deterministic = run_guardrail_checks(asset, extra_banned_terms=extra_banned_terms)

    # Layer 2: LLM judge (tone/guideline violations + rubric score).
    output = await client.generate_json(
        prompt=prompt.build_prompt(asset, brief, CriticOutput.model_json_schema()),
        response_model=CriticOutput,
        system=prompt.SYSTEM,
    )

    # Merge violation lists (dedupe, preserve order); deterministic ones first.
    violations: list[str] = list(deterministic)
    for v in output.guardrail_violations:
        if v and v not in violations:
            violations.append(v)

    guardrail = GuardrailResult(passed=not violations, violations=violations)
    return guardrail, output.score
