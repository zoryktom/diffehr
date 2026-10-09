from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class ContractError(ValueError):
    """Raised when a clinical counterfactual contract is invalid."""


class BehavioralRelation(str, Enum):
    """Expected behavioral relation between base and variant decisions."""

    MUST_FLIP = "flip"
    MUST_REMAIN_INVARIABLE = "same"

    @classmethod
    def normalize(cls, value: Any) -> "BehavioralRelation":
        if isinstance(value, cls):
            return value
        raw = str(value).strip().lower().replace("-", "_")
        aliases = {
            "must_flip": cls.MUST_FLIP,
            "flip": cls.MUST_FLIP,
            "must_remain_invariable": cls.MUST_REMAIN_INVARIABLE,
            "must_remain_invariant": cls.MUST_REMAIN_INVARIABLE,
            "remain_invariable": cls.MUST_REMAIN_INVARIABLE,
            "remain_invariant": cls.MUST_REMAIN_INVARIABLE,
            "invariant": cls.MUST_REMAIN_INVARIABLE,
            "same": cls.MUST_REMAIN_INVARIABLE,
        }
        if raw not in aliases:
            raise ValueError("relation must be 'flip'/'must_flip' or 'same'/'must_remain_invariable'")
        return aliases[raw]


class ContractType(str, Enum):
    CLINICAL_SENSITIVITY = "clinical_sensitivity"
    NONCLINICAL_INVARIANCE = "nonclinical_invariance"
    TEMPORAL_VALIDITY = "temporal_validity"


def _parse_iso_date(value: Any, field_name: str) -> date:
    if isinstance(value, datetime):
        raise ValueError(f"{field_name} must be an ISO date, not a datetime")
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return date.fromisoformat(value)
        except ValueError as exc:
            raise ValueError(f"{field_name} must be an ISO date in YYYY-MM-DD format") from exc
    raise TypeError(f"{field_name} must be an ISO date string")


class StrictModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        populate_by_name=True,
        str_strip_whitespace=True,
    )


class ClinicalTask(StrictModel):
    description: str = Field(min_length=1)
    clinical_question: str | None = None
    output_format: Literal["structured_json"] = "structured_json"


class TemporalConstraints(StrictModel):
    decision_index_timestamp: date | None = None
    forbid_future_evidence: bool = True

    @field_validator("decision_index_timestamp", mode="before")
    @classmethod
    def parse_decision_index_timestamp(cls, value: Any) -> date | None:
        if value is None:
            return None
        return _parse_iso_date(value, "decision_index_timestamp")


class CounterfactualMutation(StrictModel):
    description: str = Field(default="", description="Controlled change from base chart to variant chart.")
    changed_fields: tuple[str, ...] = ()
    clinical_intent: str | None = None

    @field_validator("changed_fields", mode="before")
    @classmethod
    def normalize_changed_fields(cls, value: Any) -> tuple[str, ...]:
        if value in (None, ""):
            return ()
        if not isinstance(value, (list, tuple)):
            raise TypeError("changed_fields must be a list of field paths")
        return tuple(str(item).strip() for item in value if str(item).strip())


class RecordItem(StrictModel):
    id: str = Field(min_length=1)
    date: date
    type: str = Field(min_length=1)
    text: str = Field(min_length=1)
    fhir: dict[str, Any] | None = None

    @field_validator("date", mode="before")
    @classmethod
    def parse_date(cls, value: Any) -> date:
        return _parse_iso_date(value, "date")

    @property
    def parsed_date(self) -> date:
        return self.date


class PatientRecord(StrictModel):
    id: str = Field(min_length=1)
    as_of: date
    record: tuple[RecordItem, ...] = Field(min_length=1)
    attributes: dict[str, Any] = Field(default_factory=dict)
    fhir: dict[str, Any] | None = None

    @field_validator("as_of", mode="before")
    @classmethod
    def parse_as_of(cls, value: Any) -> date:
        return _parse_iso_date(value, "as_of")

    @model_validator(mode="after")
    def validate_record_ids(self) -> "PatientRecord":
        ids = [item.id for item in self.record]
        if len(ids) != len(set(ids)):
            raise ValueError(f"{self.id}: record item ids must be unique")
        validate_fhir_sanity(self.fhir, owner=self.id)
        for item in self.record:
            validate_fhir_sanity(item.fhir, owner=item.id)
        return self

    @property
    def parsed_as_of(self) -> date:
        return self.as_of

    def visible_items(self) -> list[RecordItem]:
        return [item for item in self.record if item.date <= self.as_of]

    def citation_date(self, citation_id: str) -> date | None:
        for item in self.record:
            if item.id == citation_id:
                return item.date
        return None

    def to_fhir_bundle(self) -> dict[str, Any]:
        """Return a minimal FHIR R4-style Bundle for adapters that expect FHIR JSON."""
        if self.fhir is not None:
            return self.fhir
        entries = [
            {
                "resource": {
                    "resourceType": "DocumentReference",
                    "id": item.id,
                    "date": item.date.isoformat(),
                    "type": {"text": item.type},
                    "description": item.text,
                }
            }
            for item in self.record
        ]
        return {
            "resourceType": "Bundle",
            "type": "collection",
            "id": self.id,
            "timestamp": self.as_of.isoformat(),
            "entry": entries,
        }

    def to_prompt_text(self, include_future: bool = True) -> str:
        items = self.record if include_future else tuple(self.visible_items())
        lines = [
            f"Patient ID: {self.id}",
            f"Decision date: {self.as_of.isoformat()}",
            "Attributes:",
        ]
        for key, value in sorted(self.attributes.items()):
            lines.append(f"- {key}: {value}")
        lines.append("Chart:")
        for item in items:
            lines.append(f"[{item.id}] {item.date.isoformat()} {item.type}: {item.text}")
        return "\n".join(lines)


class RequiredEvidenceCitations(StrictModel):
    base: tuple[str, ...] = ()
    variant: tuple[str, ...] = ()

    @field_validator("base", "variant", mode="before")
    @classmethod
    def normalize_citations(cls, value: Any) -> tuple[str, ...]:
        if value in (None, ""):
            return ()
        if not isinstance(value, (list, tuple, set)):
            raise TypeError("required citations must be a list of record item ids")
        normalized = tuple(str(item).strip() for item in value if str(item).strip())
        if len(normalized) != len(set(normalized)):
            raise ValueError("required citations must not contain duplicates")
        return normalized

    def get(self, side: str, default: tuple[str, ...] = ()) -> tuple[str, ...]:
        if side == "base":
            return self.base
        if side == "variant":
            return self.variant
        return default

    def as_dict(self) -> dict[str, tuple[str, ...]]:
        return {"base": self.base, "variant": self.variant}


class ExpectedBehavior(StrictModel):
    relation: BehavioralRelation
    base_decision: str = Field(min_length=1)
    variant_decision: str = Field(min_length=1)
    required_citations: RequiredEvidenceCitations = Field(default_factory=RequiredEvidenceCitations)
    forbidden_after_as_of: bool = True

    @field_validator("relation", mode="before")
    @classmethod
    def normalize_relation(cls, value: Any) -> BehavioralRelation:
        return BehavioralRelation.normalize(value)

    @field_validator("base_decision", "variant_decision", mode="before")
    @classmethod
    def normalize_decision(cls, value: Any) -> str:
        if not isinstance(value, str):
            raise TypeError("decision values must be strings")
        normalized = value.strip().lower()
        if not normalized:
            raise ValueError("decision values must not be empty")
        return normalized


class Contract(StrictModel):
    id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    domain: str = Field(min_length=1)
    task: str = Field(min_length=1)
    contract_type: ContractType
    allowed_decisions: tuple[str, ...] = Field(min_length=1)
    base_patient: PatientRecord
    variant_patient: PatientRecord
    expected: ExpectedBehavior
    clinical_rationale: str = ""
    temporal_constraints: TemporalConstraints = Field(default_factory=TemporalConstraints)
    mutation: CounterfactualMutation | None = None

    @field_validator("allowed_decisions", mode="before")
    @classmethod
    def normalize_allowed_decisions(cls, value: Any) -> tuple[str, ...]:
        if not isinstance(value, (list, tuple, set)):
            raise TypeError("allowed_decisions must be a list of decision strings")
        normalized = tuple(str(item).strip().lower() for item in value if str(item).strip())
        if not normalized:
            raise ValueError("allowed_decisions must not be empty")
        if len(normalized) != len(set(normalized)):
            raise ValueError("allowed_decisions must not contain duplicates")
        return normalized

    @field_validator("contract_type", mode="before")
    @classmethod
    def normalize_contract_type(cls, value: Any) -> str:
        raw = str(value).strip().lower()
        aliases = {
            "must_flip": ContractType.CLINICAL_SENSITIVITY.value,
            "must_remain_invariable": ContractType.NONCLINICAL_INVARIANCE.value,
        }
        return aliases.get(raw, raw)

    @model_validator(mode="after")
    def validate_contract_semantics(self) -> "Contract":
        allowed = set(self.allowed_decisions)
        if self.expected.base_decision not in allowed:
            raise ValueError(f"{self.id}: base_decision is not allowed")
        if self.expected.variant_decision not in allowed:
            raise ValueError(f"{self.id}: variant_decision is not allowed")
        if self.expected.relation == BehavioralRelation.MUST_REMAIN_INVARIABLE:
            if self.expected.base_decision != self.expected.variant_decision:
                raise ValueError(f"{self.id}: same relation requires equal decisions")
        if self.expected.relation == BehavioralRelation.MUST_FLIP:
            if self.expected.base_decision == self.expected.variant_decision:
                raise ValueError(f"{self.id}: flip relation requires different decisions")
        _validate_required_citations(self.id, "base", self.expected.required_citations.base, self.base_patient)
        _validate_required_citations(self.id, "variant", self.expected.required_citations.variant, self.variant_patient)
        if self.temporal_constraints.decision_index_timestamp is not None:
            decision_t = self.temporal_constraints.decision_index_timestamp
            if self.base_patient.as_of != decision_t or self.variant_patient.as_of != decision_t:
                raise ValueError(f"{self.id}: decision_index_timestamp must match both chart as_of dates")
        return self

    @property
    def base_chart(self) -> PatientRecord:
        return self.base_patient

    @property
    def variant_chart(self) -> PatientRecord:
        return self.variant_patient

    @property
    def clinical_task(self) -> ClinicalTask:
        return ClinicalTask(description=self.task)

    def patient_for_side(self, side: str) -> PatientRecord:
        if side == "base":
            return self.base_patient
        if side == "variant":
            return self.variant_patient
        raise ValueError("side must be 'base' or 'variant'")

    def expected_decision_for_side(self, side: str) -> str:
        if side == "base":
            return self.expected.base_decision
        if side == "variant":
            return self.expected.variant_decision
        raise ValueError("side must be 'base' or 'variant'")

    def prompt(self, side: str) -> str:
        patient = self.patient_for_side(side)
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


def validate_fhir_sanity(fhir: dict[str, Any] | None, owner: str) -> None:
    if fhir is None:
        return
    if not isinstance(fhir, dict):
        raise ValueError(f"{owner}: fhir must be a JSON object")
    resource_type = fhir.get("resourceType")
    if not isinstance(resource_type, str) or not resource_type:
        raise ValueError(f"{owner}: fhir must include a resourceType")
    if resource_type == "Bundle":
        entries = fhir.get("entry", [])
        if entries is None:
            return
        if not isinstance(entries, list):
            raise ValueError(f"{owner}: FHIR Bundle.entry must be a list")
        for index, entry in enumerate(entries):
            if not isinstance(entry, dict):
                raise ValueError(f"{owner}: FHIR Bundle.entry[{index}] must be an object")
            resource = entry.get("resource")
            if resource is not None and not isinstance(resource, dict):
                raise ValueError(f"{owner}: FHIR Bundle.entry[{index}].resource must be an object")
            if isinstance(resource, dict) and not isinstance(resource.get("resourceType"), str):
                raise ValueError(f"{owner}: FHIR Bundle.entry[{index}].resource must include resourceType")


def _validate_required_citations(contract_id: str, side: str, citations: tuple[str, ...], patient: PatientRecord) -> None:
    item_ids = {item.id for item in patient.record}
    missing = sorted(set(citations) - item_ids)
    if missing:
        joined = ", ".join(missing)
        raise ValueError(f"{contract_id}: required {side} citation(s) not found in chart: {joined}")
