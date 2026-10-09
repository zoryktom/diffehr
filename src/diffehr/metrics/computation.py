from __future__ import annotations

import json
from pathlib import Path
import random
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from diffehr.adapters import ModelAdapter, ModelResponse
from diffehr.core import BehavioralRelation, Contract


class MetricModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class SideScore(MetricModel):
    decision_correct: bool
    citation_correct: bool
    no_future_evidence: bool
    expected_decision: str
    observed_decision: str
    required_citations: tuple[str, ...]
    observed_citations: tuple[str, ...]
    citation_precision: float = Field(ge=0.0, le=1.0)
    citation_recall: float = Field(ge=0.0, le=1.0)
    temporal_leakage_violations: tuple[str, ...] = ()
    score: float = Field(ge=0.0, le=1.0)


class ContractResult(MetricModel):
    contract_id: str
    title: str
    domain: str
    model: str
    contract_type: str
    relation_expected: str
    relation_correct: bool
    base: SideScore
    variant: SideScore
    total_score: float = Field(ge=0.0, le=1.0)
    passed: bool
    base_response: ModelResponse
    variant_response: ModelResponse


class MetricSummary(MetricModel):
    invariance_violation_rate: float = Field(ge=0.0, le=1.0)
    decisive_sensitivity_score: float = Field(ge=0.0, le=1.0)
    evidence_citation_precision: float = Field(ge=0.0, le=1.0)
    evidence_citation_recall: float = Field(ge=0.0, le=1.0)
    temporal_leakage_violations: int = Field(ge=0)
    temporal_leakage_rate: float = Field(ge=0.0, le=1.0)
    must_flip_contracts: int = Field(ge=0)
    must_remain_invariable_contracts: int = Field(ge=0)
    total_observed_citations: int = Field(ge=0)
    total_required_citations: int = Field(ge=0)
    confidence_intervals: dict[str, tuple[float, float]] = Field(default_factory=dict)


def citation_precision_recall(required: tuple[str, ...], observed: tuple[str, ...]) -> tuple[float, float]:
    """Compute citation attribution precision and recall.

    Precision = |observed citation IDs intersect required evidence IDs| / |observed citation IDs|.
    Recall = |observed citation IDs intersect required evidence IDs| / |required evidence IDs|.

    Empty observed and required sets receive precision=1 and recall=1, treating
    the side as a correctly uncited response when no evidence citation is
    required by the contract.
    """
    required_set = set(required)
    observed_set = set(observed)
    true_positive = len(required_set & observed_set)
    if observed_set:
        precision = true_positive / len(observed_set)
    else:
        precision = 1.0 if not required_set else 0.0
    recall = true_positive / len(required_set) if required_set else 1.0
    return round(precision, 4), round(recall, 4)


def score_side(contract: Contract, side: str, response: ModelResponse) -> SideScore:
    patient = contract.patient_for_side(side)
    expected = contract.expected_decision_for_side(side)
    required = contract.expected.required_citations.get(side, ())
    decision_correct = response.decision == expected
    precision, recall = citation_precision_recall(required, response.citations)
    citation_correct = recall == 1.0
    leakage = temporal_leakage_violations(contract, side, response.citations)
    no_future = not leakage
    score = (
        0.55 * float(decision_correct)
        + 0.15 * precision
        + 0.20 * recall
        + 0.10 * float(no_future)
    )
    return SideScore(
        decision_correct=decision_correct,
        citation_correct=citation_correct,
        no_future_evidence=no_future,
        expected_decision=expected,
        observed_decision=response.decision,
        required_citations=required,
        observed_citations=response.citations,
        citation_precision=precision,
        citation_recall=recall,
        temporal_leakage_violations=leakage,
        score=round(score, 4),
    )


def temporal_leakage_violations(contract: Contract, side: str, citations: tuple[str, ...]) -> tuple[str, ...]:
    """Return cited evidence IDs with timestamp greater than decision_t.

    A temporal leakage violation occurs when a model cites chart evidence whose
    effective timestamp is after the side's decision index timestamp. In the
    compact contract format, the patient ``as_of`` date is the decision index.
    """
    if not contract.expected.forbidden_after_as_of or not contract.temporal_constraints.forbid_future_evidence:
        return ()
    patient = contract.patient_for_side(side)
    violations: list[str] = []
    for citation in citations:
        citation_date = patient.citation_date(citation)
        if citation_date and citation_date > patient.as_of:
            violations.append(citation)
    return tuple(violations)


def evaluate_contract(contract: Contract, model: ModelAdapter) -> ContractResult:
    base_response = model.answer(contract, "base")
    variant_response = model.answer(contract, "variant")
    base_score = score_side(contract, "base", base_response)
    variant_score = score_side(contract, "variant", variant_response)
    if contract.expected.relation == BehavioralRelation.MUST_REMAIN_INVARIABLE:
        relation_correct = base_response.decision == variant_response.decision
    else:
        relation_correct = base_response.decision != variant_response.decision
    total = 0.45 * base_score.score + 0.45 * variant_score.score + 0.10 * float(relation_correct)
    total = round(total, 4)
    passed = (
        base_score.decision_correct
        and variant_score.decision_correct
        and relation_correct
        and base_score.citation_correct
        and variant_score.citation_correct
        and base_score.no_future_evidence
        and variant_score.no_future_evidence
    )
    return ContractResult(
        contract_id=contract.id,
        title=contract.title,
        domain=contract.domain,
        model=model.name,
        contract_type=contract.contract_type.value,
        relation_expected=contract.expected.relation.value,
        relation_correct=relation_correct,
        base=base_score,
        variant=variant_score,
        total_score=total,
        passed=passed,
        base_response=base_response,
        variant_response=variant_response,
    )


def run_evaluation(contracts: list[Contract], model: ModelAdapter) -> dict[str, Any]:
    results = [evaluate_contract(contract, model) for contract in contracts]
    passed = sum(1 for result in results if result.passed)
    mean_score = sum(result.total_score for result in results) / len(results) if results else 0.0
    metrics = compute_run_metrics(results)
    return {
        "schema_version": "0.2",
        "model": model.name,
        "n_contracts": len(results),
        "passed": passed,
        "pass_rate": round(passed / len(results), 4) if results else 0.0,
        "mean_score": round(mean_score, 4),
        "metrics": metrics.model_dump(mode="json"),
        "results": [result_to_dict(result) for result in results],
    }


def compute_run_metrics(results: list[ContractResult]) -> MetricSummary:
    """Compute aggregate DiffEHR research metrics for a model run.

    IVR, the Invariance Violation Rate, is:
    count(unexpected decision flips on invariant pairs) / total invariant pairs.

    DSS, the Decisive Sensitivity Score, is:
    count(expected decision flips on decisive pairs with both side decisions
    correct) / total decisive pairs.

    TLVR, the Temporal Leakage Violation Rate, is:
    count(cited evidence IDs with evidence_t > decision_t) / total cited
    evidence IDs.

    The returned confidence intervals are deterministic percentile bootstrap
    intervals over contracts for IVR and DSS.
    """
    invariance = [result for result in results if result.relation_expected == BehavioralRelation.MUST_REMAIN_INVARIABLE.value]
    must_flip = [result for result in results if result.relation_expected == BehavioralRelation.MUST_FLIP.value]
    invariance_violations = sum(1 for result in invariance if not result.relation_correct)
    decisive_successes = sum(
        1
        for result in must_flip
        if result.relation_correct and result.base.decision_correct and result.variant.decision_correct
    )

    true_positive = 0
    observed_total = 0
    required_total = 0
    leakage_total = 0
    for result in results:
        for side in (result.base, result.variant):
            required = set(side.required_citations)
            observed = set(side.observed_citations)
            true_positive += len(required & observed)
            observed_total += len(observed)
            required_total += len(required)
            leakage_total += len(side.temporal_leakage_violations)

    if observed_total:
        precision = true_positive / observed_total
    else:
        precision = 1.0 if required_total == 0 else 0.0
    recall = true_positive / required_total if required_total else 1.0
    temporal_rate = leakage_total / observed_total if observed_total else 0.0
    confidence_intervals = bootstrap_confidence_intervals(results)
    return MetricSummary(
        invariance_violation_rate=round(invariance_violations / len(invariance), 4) if invariance else 0.0,
        decisive_sensitivity_score=round(decisive_successes / len(must_flip), 4) if must_flip else 0.0,
        evidence_citation_precision=round(precision, 4),
        evidence_citation_recall=round(recall, 4),
        temporal_leakage_violations=leakage_total,
        temporal_leakage_rate=round(temporal_rate, 4),
        must_flip_contracts=len(must_flip),
        must_remain_invariable_contracts=len(invariance),
        total_observed_citations=observed_total,
        total_required_citations=required_total,
        confidence_intervals=confidence_intervals,
    )


def bootstrap_confidence_intervals(
    results: list[ContractResult], *, samples: int = 1000, seed: int = 2025
) -> dict[str, tuple[float, float]]:
    """Return deterministic 95% bootstrap CIs for IVR and DSS.

    Contracts are resampled with replacement. Each bootstrap sample recomputes
    IVR and DSS on the sampled contracts, then the 2.5th and 97.5th percentiles
    are returned. This treats the contract pack as the empirical sampling unit,
    which is appropriate for comparing model behavior across a finite artifact.
    """
    if not results:
        return {
            "invariance_violation_rate": (0.0, 0.0),
            "decisive_sensitivity_score": (0.0, 0.0),
        }
    rng = random.Random(seed)
    ivr_values: list[float] = []
    dss_values: list[float] = []
    n = len(results)
    for _ in range(samples):
        sample = [results[rng.randrange(n)] for _ in range(n)]
        ivr, dss = _relation_rates(sample)
        ivr_values.append(ivr)
        dss_values.append(dss)
    return {
        "invariance_violation_rate": _percentile_interval(ivr_values),
        "decisive_sensitivity_score": _percentile_interval(dss_values),
    }


def _relation_rates(results: list[ContractResult]) -> tuple[float, float]:
    invariance = [result for result in results if result.relation_expected == BehavioralRelation.MUST_REMAIN_INVARIABLE.value]
    must_flip = [result for result in results if result.relation_expected == BehavioralRelation.MUST_FLIP.value]
    invariance_violations = sum(1 for result in invariance if not result.relation_correct)
    decisive_successes = sum(
        1
        for result in must_flip
        if result.relation_correct and result.base.decision_correct and result.variant.decision_correct
    )
    ivr = invariance_violations / len(invariance) if invariance else 0.0
    dss = decisive_successes / len(must_flip) if must_flip else 0.0
    return ivr, dss


def _percentile_interval(values: list[float]) -> tuple[float, float]:
    ordered = sorted(values)
    low_index = max(0, round(0.025 * (len(ordered) - 1)))
    high_index = min(len(ordered) - 1, round(0.975 * (len(ordered) - 1)))
    return round(ordered[low_index], 4), round(ordered[high_index], 4)


def result_to_dict(result: ContractResult) -> dict[str, Any]:
    return result.model_dump(mode="json")


def save_results(payload: dict[str, Any], path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
