from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Any

from .contracts import Contract
from .models import ClinicalAI, ModelResponse


@dataclass(frozen=True)
class SideScore:
    decision_correct: bool
    citation_correct: bool
    no_future_evidence: bool
    expected_decision: str
    observed_decision: str
    required_citations: tuple[str, ...]
    observed_citations: tuple[str, ...]
    score: float


@dataclass(frozen=True)
class ContractResult:
    contract_id: str
    title: str
    model: str
    contract_type: str
    relation_expected: str
    relation_correct: bool
    base: SideScore
    variant: SideScore
    total_score: float
    passed: bool
    base_response: ModelResponse
    variant_response: ModelResponse


def score_side(contract: Contract, side: str, response: ModelResponse) -> SideScore:
    patient = contract.base_patient if side == "base" else contract.variant_patient
    expected = contract.expected.base_decision if side == "base" else contract.expected.variant_decision
    required = contract.expected.required_citations.get(side, ())
    decision_correct = response.decision == expected
    citation_correct = all(citation in response.citations for citation in required)
    if not required:
        citation_correct = True
    no_future = True
    if contract.expected.forbidden_after_as_of:
        for citation in response.citations:
            citation_date = patient.citation_date(citation)
            if citation_date and citation_date > patient.parsed_as_of:
                no_future = False
    score = (
        0.65 * float(decision_correct)
        + 0.2 * float(citation_correct)
        + 0.15 * float(no_future)
    )
    return SideScore(
        decision_correct=decision_correct,
        citation_correct=citation_correct,
        no_future_evidence=no_future,
        expected_decision=expected,
        observed_decision=response.decision,
        required_citations=required,
        observed_citations=response.citations,
        score=round(score, 4),
    )


def evaluate_contract(contract: Contract, model: ClinicalAI) -> ContractResult:
    base_response = model.answer(contract, "base")
    variant_response = model.answer(contract, "variant")
    base_score = score_side(contract, "base", base_response)
    variant_score = score_side(contract, "variant", variant_response)
    if contract.expected.relation == "same":
        relation_correct = base_response.decision == variant_response.decision
    else:
        relation_correct = base_response.decision != variant_response.decision
    total = 0.45 * base_score.score + 0.45 * variant_score.score + 0.1 * float(relation_correct)
    total = round(total, 4)
    return ContractResult(
        contract_id=contract.id,
        title=contract.title,
        model=model.name,
        contract_type=contract.contract_type,
        relation_expected=contract.expected.relation,
        relation_correct=relation_correct,
        base=base_score,
        variant=variant_score,
        total_score=total,
        passed=total >= 0.8,
        base_response=base_response,
        variant_response=variant_response,
    )


def run_evaluation(contracts: list[Contract], model: ClinicalAI) -> dict[str, Any]:
    results = [evaluate_contract(contract, model) for contract in contracts]
    passed = sum(1 for result in results if result.passed)
    mean_score = sum(result.total_score for result in results) / len(results) if results else 0.0
    return {
        "model": model.name,
        "n_contracts": len(results),
        "passed": passed,
        "pass_rate": round(passed / len(results), 4) if results else 0.0,
        "mean_score": round(mean_score, 4),
        "results": [result_to_dict(result) for result in results],
    }


def result_to_dict(result: ContractResult) -> dict[str, Any]:
    data = asdict(result)
    return data


def save_results(payload: dict[str, Any], path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)

