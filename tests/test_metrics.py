import math

import pytest

from diffehr.adapters.base import ModelResponse
from diffehr.metrics.computation import (
    ContractResult,
    SideScore,
    bootstrap_confidence_intervals,
    compute_run_metrics,
    headline_metrics,
    headline_standard_errors,
)


def side(expected: str, observed: str, *, future: bool = False) -> SideScore:
    return SideScore(
        decision_correct=expected == observed,
        citation_correct=True,
        no_future_evidence=not future,
        expected_decision=expected,
        observed_decision=observed,
        required_citations=(),
        observed_citations=(),
        citation_precision=1.0,
        citation_recall=1.0,
        temporal_leakage_violations=("x",) if future else (),
        score=1.0 if expected == observed else 0.0,
    )


def result(
    kind: str,
    relation: str,
    base: tuple[str, str],
    variant: tuple[str, str],
    *,
    future: bool = False,
    cid: str = "c",
) -> ContractResult:
    flipped = base[1] != variant[1]
    relation_correct = flipped if relation == "flip" else not flipped
    response = ModelResponse(model="m", decision="eligible")
    return ContractResult(
        contract_id=cid,
        title="t",
        domain="oncology",
        model="m",
        contract_type=kind,
        relation_expected=relation,
        relation_correct=relation_correct,
        base=side(*base),
        variant=side(*variant, future=future),
        total_score=0.5,
        passed=False,
        base_response=response,
        variant_response=response,
    )


def flip(ok: bool, cid: str = "f") -> ContractResult:
    return result(
        "clinical_sensitivity",
        "flip",
        ("eligible", "eligible"),
        ("ineligible", "ineligible" if ok else "eligible"),
        cid=cid,
    )


def invariant(ok: bool, cid: str = "i") -> ContractResult:
    return result(
        "nonclinical_invariance",
        "same",
        ("eligible", "eligible"),
        ("eligible", "eligible" if ok else "ineligible"),
        cid=cid,
    )


def temporal(ok: bool, cid: str = "t") -> ContractResult:
    return result(
        "temporal_validity",
        "same",
        ("eligible", "eligible"),
        ("eligible", "eligible"),
        future=not ok,
        cid=cid,
    )


def test_cfa_boundaries():
    assert headline_metrics([flip(True), flip(True)])["counterfactual_flip_accuracy"] == 1.0
    assert headline_metrics([flip(False), flip(False)])["counterfactual_flip_accuracy"] == 0.0
    assert headline_metrics([flip(True), flip(False)])["counterfactual_flip_accuracy"] == 0.5


def test_ifr_boundaries():
    assert headline_metrics([invariant(True)])["invariance_failure_rate"] == 0.0
    assert headline_metrics([invariant(False)])["invariance_failure_rate"] == 1.0
    assert (
        headline_metrics([invariant(True), invariant(False), invariant(True), invariant(True)])[
            "invariance_failure_rate"
        ]
        == 0.25
    )


def test_tdv_counts_future_citations_even_when_decision_stable():
    assert headline_metrics([temporal(True)])["temporal_directional_violation"] == 0.0
    assert headline_metrics([temporal(False)])["temporal_directional_violation"] == 1.0


def test_empty_slices_do_not_divide_by_zero():
    for results in ([], [flip(True)], [invariant(True)]):
        values = headline_metrics(results)
        assert all(math.isfinite(v) for v in values.values())
    empty = headline_metrics([])
    assert empty == {
        "counterfactual_flip_accuracy": 0.0,
        "invariance_failure_rate": 0.0,
        "temporal_directional_violation": 0.0,
        "safety_divergence_index": 0.0,
    }
    assert headline_metrics([flip(True)])["invariance_failure_rate"] == 0.0
    assert headline_standard_errors([]) == {
        "counterfactual_flip_accuracy": 0.0,
        "invariance_failure_rate": 0.0,
        "temporal_directional_violation": 0.0,
        "safety_divergence_index": 0.0,
    }


def test_sdi_weights_safety_critical_errors_three_to_one():
    safe_miss = result("clinical_sensitivity", "flip", ("eligible", "ineligible"), ("ineligible", "ineligible"))
    critical_miss = result("clinical_sensitivity", "flip", ("eligible", "eligible"), ("contraindicated", "eligible"))
    assert headline_metrics([safe_miss])["safety_divergence_index"] == pytest.approx(1 / 2)
    assert headline_metrics([critical_miss])["safety_divergence_index"] == pytest.approx(3 / 4)
    perfect = result("clinical_sensitivity", "flip", ("eligible", "eligible"), ("contraindicated", "contraindicated"))
    assert headline_metrics([perfect])["safety_divergence_index"] == 0.0


def test_standard_error_is_binomial():
    results = [flip(True), flip(False), flip(True), flip(False)]
    errors = headline_standard_errors(results)
    assert errors["counterfactual_flip_accuracy"] == pytest.approx(math.sqrt(0.25 / 4))
    assert errors["invariance_failure_rate"] == 0.0
    assert headline_standard_errors([flip(True)])["counterfactual_flip_accuracy"] == 0.0


def test_bootstrap_is_deterministic_and_bracketed():
    results = [flip(i % 3 != 0, cid=f"f{i}") for i in range(30)] + [
        invariant(i % 5 != 0, cid=f"i{i}") for i in range(20)
    ]
    first = headline_standard_errors(results)
    assert first == headline_standard_errors(results)
    summary_a = compute_run_metrics(results)
    summary_b = compute_run_metrics(results)
    assert summary_a.confidence_intervals == summary_b.confidence_intervals
    for key, (low, high) in summary_a.confidence_intervals.items():
        assert 0.0 <= low <= high <= 1.0, key
    point = summary_a.counterfactual_flip_accuracy
    low, high = summary_a.confidence_intervals["counterfactual_flip_accuracy"]
    assert low <= point <= high


def test_bootstrap_degenerate_intervals_for_perfect_run():
    summary = compute_run_metrics([flip(True), invariant(True), temporal(True)])
    for key in ("counterfactual_flip_accuracy", "invariance_failure_rate", "temporal_directional_violation"):
        low, high = summary.confidence_intervals[key]
        assert low == high
    assert summary.counterfactual_flip_accuracy == 1.0
    assert summary.invariance_failure_rate == 0.0


def test_bootstrap_confidence_intervals_accepts_empty_input():
    intervals = bootstrap_confidence_intervals([])
    assert all(low == high == 0.0 for low, high in intervals.values())
