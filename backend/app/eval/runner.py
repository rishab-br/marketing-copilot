"""Calibration runner for the golden set.

``build_report`` is a pure function (testable without any LLM). ``evaluate_case``
runs the real critic for one case; ``run_golden_set`` evaluates the whole set
sequentially and builds the report. ``python -m app.eval.runner`` runs it against
the configured LLM and prints a table — handy as an interview demo.
"""

from __future__ import annotations

import asyncio

from pydantic import BaseModel

from app.agents.critic import run_critic
from app.config import settings
from app.eval.golden import GOLDEN_SET, GoldenCase
from app.llm.client import LLMClient


class CaseResult(BaseModel):
    id: str
    expected_pass: bool
    predicted_pass: bool
    guardrail_passed: bool
    overall: float
    violations: list[str]

    @property
    def correct(self) -> bool:
        return self.predicted_pass == self.expected_pass


class GoldenReport(BaseModel):
    results: list[CaseResult]
    total: int
    correct: int
    accuracy: float
    true_pos: int
    true_neg: int
    false_pos: int
    false_neg: int


def build_report(results: list[CaseResult]) -> GoldenReport:
    """Compute accuracy + confusion counts from case results (pure)."""
    total = len(results)
    correct = sum(1 for r in results if r.correct)
    tp = sum(1 for r in results if r.predicted_pass and r.expected_pass)
    tn = sum(1 for r in results if not r.predicted_pass and not r.expected_pass)
    fp = sum(1 for r in results if r.predicted_pass and not r.expected_pass)
    fn = sum(1 for r in results if not r.predicted_pass and r.expected_pass)
    return GoldenReport(
        results=results,
        total=total,
        correct=correct,
        accuracy=(correct / total) if total else 0.0,
        true_pos=tp,
        true_neg=tn,
        false_pos=fp,
        false_neg=fn,
    )


async def evaluate_case(
    case: GoldenCase,
    *,
    client: LLMClient | None = None,
    threshold: float | None = None,
) -> CaseResult:
    """Run the critic for one case and derive the predicted gate outcome."""
    threshold = settings.eval_threshold if threshold is None else threshold
    guardrail, score = await run_critic(case.asset, case.brief, client=client)
    predicted = guardrail.passed and score.meets(threshold)
    return CaseResult(
        id=case.id,
        expected_pass=case.expected_pass,
        predicted_pass=predicted,
        guardrail_passed=guardrail.passed,
        overall=score.overall,
        violations=guardrail.violations,
    )


async def run_golden_set(
    cases: list[GoldenCase] | None = None,
    *,
    client: LLMClient | None = None,
    threshold: float | None = None,
) -> GoldenReport:
    """Evaluate the whole golden set sequentially and return a report."""
    cases = cases if cases is not None else GOLDEN_SET
    results = [await evaluate_case(case, client=client, threshold=threshold) for case in cases]
    return build_report(results)


def format_report(report: GoldenReport) -> str:
    """Render a human-readable calibration table."""
    lines = [
        f"{'case':<34} {'exp':<5} {'pred':<5} {'overall':<8} {'ok':<3} violations",
        "-" * 88,
    ]
    for r in report.results:
        mark = "ok" if r.correct else "XX"
        viol = "; ".join(r.violations) if r.violations else ""
        lines.append(
            f"{r.id:<34} {str(r.expected_pass):<5} {str(r.predicted_pass):<5} "
            f"{r.overall:<8} {mark:<3} {viol}"
        )
    lines.append("-" * 88)
    lines.append(
        f"accuracy {report.accuracy:.0%} ({report.correct}/{report.total})  "
        f"TP={report.true_pos} TN={report.true_neg} "
        f"FP={report.false_pos} FN={report.false_neg}"
    )
    return "\n".join(lines)


async def _main() -> None:
    report = await run_golden_set()
    print(format_report(report))


if __name__ == "__main__":
    asyncio.run(_main())
