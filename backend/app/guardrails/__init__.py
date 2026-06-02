"""Guardrails — deterministic, independently-testable safety checks.

Schema validation is enforced in the LLM client; this package handles brand-safety
content checks (banned/absolute claims, explicit brand-banned terms). Tone and
nuanced brand-guideline adherence are judged by the LLM critic and merged in.
"""

from app.guardrails.checks import find_banned_claims, run_guardrail_checks

__all__ = ["find_banned_claims", "run_guardrail_checks"]
