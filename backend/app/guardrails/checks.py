"""Deterministic brand-safety checks.

These run with no LLM call and are unit-tested in isolation (CLAUDE.md §9). They
catch absolute / unverifiable / risky claims that should never ship regardless of
how the rubric scores the copy. A non-empty result blocks PASS.

The LLM critic complements this with tone and nuanced brand-guideline judgement;
the two violation lists are merged by the critic agent.
"""

from __future__ import annotations

import re

from app.models import Asset

# Curated absolute / unverifiable / risky-claim patterns. Word-boundaried and
# case-insensitive. Kept conservative to avoid false positives on benign copy.
_BANNED_CLAIM_PATTERNS: list[re.Pattern[str]] = [
    re.compile(p, re.IGNORECASE)
    for p in (
        r"\bguarantee(?:d|s)?\b",
        r"\b100\s?%",
        r"\brisk[-\s]?free\b",
        r"\bzero\s+risk\b",
        r"\bbest\s+in\s+the\s+world\b",
        r"\bworld'?s\s+best\b",
        r"\bnumber\s+one\b",
        r"#1\b",
        r"\bmiracle\b",
        r"\bcure(?:s|d)?\b",
        r"\bnever\s+fails?\b",
        r"\balways\s+works\b",
        r"\bget\s+rich\b",
        r"\bdouble\s+your\s+(?:money|income)\b",
    )
]


def find_banned_claims(text: str) -> list[str]:
    """Return one violation message per distinct banned claim found in ``text``."""
    violations: list[str] = []
    for pattern in _BANNED_CLAIM_PATTERNS:
        for match in pattern.finditer(text):
            matched = match.group(0).strip()
            message = f"unverifiable or absolute claim: '{matched}'"
            if message not in violations:
                violations.append(message)
    return violations


def run_guardrail_checks(
    asset: Asset,
    *,
    extra_banned_terms: list[str] | None = None,
) -> list[str]:
    """Run all deterministic guardrails over one asset; return violation messages.

    ``extra_banned_terms`` lets a brand forbid specific words/phrases beyond the
    built-in list (matched whole-word, case-insensitive).
    """
    text = " ".join([asset.body, asset.cta, *asset.hashtags])
    violations = find_banned_claims(text)

    for term in extra_banned_terms or []:
        term = term.strip()
        if not term:
            continue
        if re.search(rf"\b{re.escape(term)}\b", text, re.IGNORECASE):
            message = f"brand-banned term: '{term}'"
            if message not in violations:
                violations.append(message)

    return violations
