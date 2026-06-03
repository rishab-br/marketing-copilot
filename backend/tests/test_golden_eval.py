"""Tests for the golden-set eval harness (no real LLM)."""

from app.eval.golden import GOLDEN_SET
from app.eval.runner import CaseResult, build_report, run_golden_set
from app.guardrails.checks import run_guardrail_checks


# --------------------------------------------------------------------------- #
# Dataset hygiene
# --------------------------------------------------------------------------- #
def test_golden_set_wellformed():
    assert 5 <= len(GOLDEN_SET) <= 10
    ids = [c.id for c in GOLDEN_SET]
    assert len(ids) == len(set(ids)), "case ids must be unique"
    labels = {c.expected_pass for c in GOLDEN_SET}
    assert labels == {True, False}, "need both pass and fail cases"


def test_deterministic_failures_are_caught_without_llm():
    """Any case whose copy trips a deterministic guardrail must be labeled fail.

    This proves the guardrail layer alone calibrates the banned-claim cases and
    guards against mislabeling them as expected-pass.
    """
    for case in GOLDEN_SET:
        if run_guardrail_checks(case.asset):
            assert case.expected_pass is False, f"{case.id} trips a guardrail but is labeled pass"


# --------------------------------------------------------------------------- #
# build_report — pure metrics
# --------------------------------------------------------------------------- #
def _cr(id_, expected, predicted) -> CaseResult:
    return CaseResult(
        id=id_,
        expected_pass=expected,
        predicted_pass=predicted,
        guardrail_passed=predicted,
        overall=4.5 if predicted else 2.0,
        violations=[] if predicted else ["x"],
    )


def test_build_report_metrics():
    results = [
        _cr("a", True, True),  # TP
        _cr("b", False, False),  # TN
        _cr("c", False, True),  # FP
        _cr("d", True, False),  # FN
    ]
    report = build_report(results)
    assert report.total == 4
    assert report.correct == 2
    assert report.accuracy == 0.5
    assert (report.true_pos, report.true_neg, report.false_pos, report.false_neg) == (1, 1, 1, 1)


def test_caseresult_correct_property():
    assert _cr("a", True, True).correct is True
    assert _cr("b", True, False).correct is False


# --------------------------------------------------------------------------- #
# run_golden_set with a stubbed judge
# --------------------------------------------------------------------------- #
async def test_run_golden_set_with_lenient_judge(make_client):
    """A judge that always scores high + reports no tone issues still gets the
    deterministic banned-claim cases right (guardrail overrides the score)."""
    lenient = {
        "guardrail_violations": [],
        "score": {
            "clarity": 5,
            "cta_strength": 5,
            "brand_fit": 5,
            "platform_fit": 5,
            "rationale": "great",
        },
    }
    client, _ = make_client([lenient] * len(GOLDEN_SET))

    report = await run_golden_set(client=client)

    by_id = {r.id: r for r in report.results}
    # Cases with banned claims must be predicted-fail despite the perfect score.
    for case in GOLDEN_SET:
        if run_guardrail_checks(case.asset):
            assert by_id[case.id].predicted_pass is False
            assert by_id[case.id].correct is True

    # The lenient judge will (wrongly) pass the tone/weak-CTA cases -> not 100%.
    assert report.total == len(GOLDEN_SET)
    assert 0.0 < report.accuracy <= 1.0
