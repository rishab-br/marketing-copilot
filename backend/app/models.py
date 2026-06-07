"""Typed contracts shared across agent boundaries.

Every agent input/output is one of these Pydantic models — no free-form strings
cross an agent boundary (see CLAUDE.md §7). Field descriptions are intentional:
they get embedded into JSON schemas used for structured LLM output and repair
prompts, so they double as instructions to the model.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Annotated, ClassVar

from pydantic import BaseModel, Field, field_validator, model_validator

# A rubric dimension is an integer 1–5.
Score1to5 = Annotated[int, Field(ge=1, le=5)]


class Brief(BaseModel):
    """The campaign brief — the system's input."""

    brand: str = Field(..., min_length=1, description="Brand or company name.")
    product: str = Field(..., min_length=1, description="Product or service being promoted.")
    goal: str = Field(..., min_length=1, description="Campaign goal, e.g. 'drive signups'.")
    audience: str = Field(..., min_length=1, description="Target audience description.")
    tone: str = Field(..., min_length=1, description="Desired tone, e.g. 'playful, confident'.")
    platforms: list[str] = Field(
        ..., min_length=1, description="Target platforms, e.g. ['instagram', 'linkedin']."
    )
    brand_guidelines: str | None = Field(
        default=None,
        description="Plain-text brand rules / banned claims to enforce (v1).",
    )

    @field_validator("platforms")
    @classmethod
    def _normalize_platforms(cls, value: list[str]) -> list[str]:
        """Lower-case, strip, and drop empties so downstream keys are consistent."""
        cleaned = [p.strip().lower() for p in value if p and p.strip()]
        if not cleaned:
            raise ValueError("at least one non-empty platform is required")
        return cleaned


class CampaignPlan(BaseModel):
    """Strategist output: the creative direction the copywriter works from."""

    angle: str = Field(..., min_length=1, description="The core campaign angle / big idea.")
    key_messages: list[str] = Field(
        ..., min_length=1, description="Key messages to convey across assets."
    )
    per_platform_direction: dict[str, str] = Field(
        ...,
        description="Per-platform creative direction, keyed by platform name.",
    )


class Asset(BaseModel):
    """A single platform-specific piece of marketing copy."""

    platform: str = Field(..., min_length=1, description="Target platform for this asset.")
    body: str = Field(..., min_length=1, description="Main copy / body text.")
    cta: str = Field(..., min_length=1, description="Call to action.")
    hashtags: list[str] = Field(
        default_factory=list, description="Optional hashtags (without the leading #)."
    )

    @field_validator("platform")
    @classmethod
    def _normalize_platform(cls, value: str) -> str:
        return value.strip().lower()


class GuardrailResult(BaseModel):
    """Brand-safety / schema guardrail outcome for one asset.

    Kept separate from the rubric score: a guardrail failure forces a revision
    regardless of how high the score is (see CLAUDE.md §7).
    """

    passed: bool = Field(..., description="True only if no violations were found.")
    violations: list[str] = Field(
        default_factory=list,
        description="Human-readable violations, e.g. \"unverifiable claim: 'best in world'\".",
    )

    @model_validator(mode="after")
    def _coherent(self) -> GuardrailResult:
        """`passed` and `violations` must agree — guard against an inconsistent judge."""
        if self.violations and self.passed:
            raise ValueError("passed cannot be True when violations are present")
        return self


class EvalScore(BaseModel):
    """Rubric LLM-as-judge score for one asset.

    The judge returns the four 1–5 dimensions and a rationale. ``overall`` is NOT
    trusted from the model — it is computed deterministically from the dimensions
    using documented weights, because this value gates the revision loop.
    """

    # Documented weighting of the rubric dimensions (sums to 1.0).
    WEIGHTS: ClassVar[dict[str, float]] = {
        "clarity": 0.25,
        "cta_strength": 0.30,
        "brand_fit": 0.25,
        "platform_fit": 0.20,
    }

    clarity: Score1to5 = Field(..., description="How clear and easy to understand the copy is.")
    cta_strength: Score1to5 = Field(..., description="How compelling and actionable the CTA is.")
    brand_fit: Score1to5 = Field(..., description="How well it matches brand tone/guidelines.")
    platform_fit: Score1to5 = Field(..., description="How well it fits the target platform.")
    rationale: str = Field(..., min_length=1, description="Brief justification for the scores.")
    overall: float = Field(
        default=0.0,
        description="Weighted overall score (computed; the loop gate compares this).",
    )

    @model_validator(mode="after")
    def _compute_overall(self) -> EvalScore:
        """Always (re)compute ``overall`` from the dimensions; ignore any supplied value."""
        weighted = (
            self.clarity * self.WEIGHTS["clarity"]
            + self.cta_strength * self.WEIGHTS["cta_strength"]
            + self.brand_fit * self.WEIGHTS["brand_fit"]
            + self.platform_fit * self.WEIGHTS["platform_fit"]
        )
        # bypass validation re-entry by setting via __dict__
        object.__setattr__(self, "overall", round(weighted, 2))
        return self

    def meets(self, threshold: float) -> bool:
        """Whether this score passes the eval gate."""
        return self.overall >= threshold


class AssetResult(BaseModel):
    """Everything the human reviewer needs for one asset: copy + checks + score."""

    asset: Asset
    guardrail: GuardrailResult
    score: EvalScore
    iterations: int = Field(
        default=0, ge=0, description="How many copywriter↔critic cycles produced this asset."
    )

    def passed(self, threshold: float) -> bool:
        """An asset passes only if guardrails pass AND the score meets threshold."""
        return self.guardrail.passed and self.score.meets(threshold)


# --------------------------------------------------------------------------- #
# Publishing models (v2)
# --------------------------------------------------------------------------- #


class PostStatus(str, Enum):
    pending = "pending"       # scheduled, awaiting execution
    published = "published"   # live on the platform
    failed = "failed"         # attempt failed
    cancelled = "cancelled"   # cancelled before publication


class PublishRequest(BaseModel):
    """Request body for the publish/schedule endpoint."""

    scheduled_at: datetime | None = Field(
        default=None,
        description="ISO-8601 datetime to publish at. None means publish immediately.",
    )


class PublishResult(BaseModel):
    """Result returned after a publish or schedule action."""

    id: str = Field(..., description="Internal PostRecord ID.")
    platform: str
    post_id: str = Field(..., description="Platform-assigned post ID (or stub ID).")
    url: str | None = Field(default=None, description="Live post URL once published.")
    status: PostStatus
    published_at: datetime | None = None
    scheduled_at: datetime | None = None
    error: str | None = None
