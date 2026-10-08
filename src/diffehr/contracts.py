from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import json
from pathlib import Path
from typing import Any


class ContractError(ValueError):
    """Raised when a clinical counterfactual contract is invalid."""


@dataclass(frozen=True)
class RecordItem:
    id: str
    date: str
    type: str
    text: str

    @property
    def parsed_date(self) -> date:
        return date.fromisoformat(self.date)


@dataclass(frozen=True)
class PatientRecord:
    id: str
    as_of: str
    record: tuple[RecordItem, ...]
    attributes: dict[str, Any]

    @property
    def parsed_as_of(self) -> date:
        return date.fromisoformat(self.as_of)

    def visible_items(self) -> list[RecordItem]:
        return [item for item in self.record if item.parsed_date <= self.parsed_as_of]

    def citation_date(self, citation_id: str) -> date | None:
        for item in self.record:
            if item.id == citation_id:
                return item.parsed_date
        return None

    def to_prompt_text(self, include_future: bool = True) -> str:
        items = self.record if include_future else tuple(self.visible_items())
        lines = [
            f"Patient ID: {self.id}",
            f"Decision date: {self.as_of}",
            "Attributes:",
        ]
        for key, value in sorted(self.attributes.items()):
            lines.append(f"- {key}: {value}")
        lines.append("Chart:")
        for item in items:
            lines.append(f"[{item.id}] {item.date} {item.type}: {item.text}")
        return "\n".join(lines)


@dataclass(frozen=True)
class ExpectedBehavior:
    relation: str
    base_decision: str
    variant_decision: str
    required_citations: dict[str, tuple[str, ...]]
    forbidden_after_as_of: bool = True


@dataclass(frozen=True)
class Contract:
    id: str
    title: str
    domain: str
    task: str
    contract_type: str
    allowed_decisions: tuple[str, ...]
    base_patient: PatientRecord
    variant_patient: PatientRecord
    expected: ExpectedBehavior
    clinical_rationale: str

    def prompt(self, side: str) -> str:
        patient = self.base_patient if side == "base" else self.variant_patient
        allowed = ", ".join(self.allowed_decisions)
        return (
            "You are evaluating a synthetic patient chart for a clinical AI "
            "benchmark. This is not medical advice and no real patient data is "
            "included.\n\n"
            f"Task: {self.task}\n\n"
            f"{patient.to_prompt_text(include_future=True)}\n\n"
            "Return strict JSON with these fields:\n"
            f'- "decision": one of [{allowed}]\n'
            '- "citations": a list of chart item IDs supporting the decision\n'
            '- "rationale": one concise paragraph grounded only in the chart\n'
            '- "confidence": a number from 0 to 1\n'
        )


def _require(data: dict[str, Any], field: str) -> Any:
    if field not in data:
        raise ContractError(f"Missing required field: {field}")
    return data[field]


def _patient_from_dict(data: dict[str, Any]) -> PatientRecord:
    record = []
    for raw in _require(data, "record"):
        record.append(
            RecordItem(
                id=str(_require(raw, "id")),
                date=str(_require(raw, "date")),
                type=str(_require(raw, "type")),
                text=str(_require(raw, "text")),
            )
        )
    return PatientRecord(
        id=str(_require(data, "id")),
        as_of=str(_require(data, "as_of")),
        record=tuple(record),
        attributes=dict(data.get("attributes", {})),
    )


def contract_from_dict(data: dict[str, Any]) -> Contract:
    expected_raw = _require(data, "expected")
    required = expected_raw.get("required_citations", {})
    expected = ExpectedBehavior(
        relation=str(_require(expected_raw, "relation")),
        base_decision=str(_require(expected_raw, "base_decision")).lower(),
        variant_decision=str(_require(expected_raw, "variant_decision")).lower(),
        required_citations={
            "base": tuple(required.get("base", [])),
            "variant": tuple(required.get("variant", [])),
        },
        forbidden_after_as_of=bool(expected_raw.get("forbidden_after_as_of", True)),
    )
    contract = Contract(
        id=str(_require(data, "id")),
        title=str(_require(data, "title")),
        domain=str(_require(data, "domain")),
        task=str(_require(data, "task")),
        contract_type=str(_require(data, "contract_type")),
        allowed_decisions=tuple(str(x).lower() for x in _require(data, "allowed_decisions")),
        base_patient=_patient_from_dict(_require(data, "base_patient")),
        variant_patient=_patient_from_dict(_require(data, "variant_patient")),
        expected=expected,
        clinical_rationale=str(data.get("clinical_rationale", "")),
    )
    validate_contract(contract)
    return contract


def load_contract(path: str | Path) -> Contract:
    path = Path(path)
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    return contract_from_dict(data)


def load_contracts(path: str | Path) -> list[Contract]:
    root = Path(path)
    if root.is_file():
        return [load_contract(root)]
    files = sorted(root.glob("*.json"))
    return [load_contract(file) for file in files]


def validate_contract(contract: Contract) -> None:
    if contract.expected.base_decision not in contract.allowed_decisions:
        raise ContractError(f"{contract.id}: base_decision is not allowed")
    if contract.expected.variant_decision not in contract.allowed_decisions:
        raise ContractError(f"{contract.id}: variant_decision is not allowed")
    if contract.expected.relation not in {"flip", "same"}:
        raise ContractError(f"{contract.id}: relation must be 'flip' or 'same'")
    if contract.expected.relation == "same":
        if contract.expected.base_decision != contract.expected.variant_decision:
            raise ContractError(f"{contract.id}: same relation requires equal decisions")
    if contract.expected.relation == "flip":
        if contract.expected.base_decision == contract.expected.variant_decision:
            raise ContractError(f"{contract.id}: flip relation requires different decisions")

