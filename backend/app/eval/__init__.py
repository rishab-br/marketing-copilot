"""Eval harness: a hand-labeled golden set + a calibration runner.

Lets us show the eval itself is calibrated (CLAUDE.md §10) — run the critic over
labeled briefs/assets and compare predicted pass/fail to expectations.
"""

from app.eval.golden import GOLDEN_SET, GoldenCase
from app.eval.runner import CaseResult, GoldenReport, build_report, run_golden_set

__all__ = [
    "GOLDEN_SET",
    "GoldenCase",
    "CaseResult",
    "GoldenReport",
    "build_report",
    "run_golden_set",
]
