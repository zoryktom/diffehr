from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from diffehr.core import Contract


class ClinicalPrediction(BaseModel):
    """Structured model output schema requested from every adapter."""

    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    decision: str = Field(min_length=1)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    contraindication_flagged: bool = False
    clinical_rationale: str = ""
    citations: list[str] = Field(default_factory=list)

    @field_validator("decision", mode="before")
    @classmethod
    def normalize_decision(cls, value: Any) -> str:
        return str(value).strip().lower()

    @field_validator("confidence", mode="before")
    @classmethod
    def clamp_confidence(cls, value: Any) -> float:
        return _clamp_float(value)


class ModelResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    model: str = Field(min_length=1)
    decision: str = Field(min_length=1)
    citations: tuple[str, ...] = ()
    rationale: str = ""
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    contraindication_flagged: bool = False
    raw_text: str = ""

    @field_validator("decision", mode="before")
    @classmethod
    def normalize_decision(cls, value: Any) -> str:
        return str(value).strip().lower()

    @field_validator("citations", mode="before")
    @classmethod
    def normalize_citations(cls, value: Any) -> tuple[str, ...]:
        if value in (None, ""):
            return ()
        if not isinstance(value, (list, tuple, set)):
            return ()
        return tuple(str(item).strip() for item in value if str(item).strip())


class ModelAdapter(ABC):
    name = "base"

    @abstractmethod
    def answer(self, contract: Contract, side: str) -> ModelResponse:
        """Return a structured answer for one side of a contract."""


def build_clinical_prompt(contract: Contract, side: str) -> str:
    """Render a chart as an instruction prompt: chronological note summary, FHIR JSON narrative and output schema."""
    patient = contract.patient_for_side(side)
    allowed = ", ".join(contract.allowed_decisions)
    parts = [
        "You are evaluating a synthetic patient chart for a clinical AI benchmark. "
        "This is not medical advice and no real patient data is included.",
        f"Task: {contract.task}",
        "Chronological clinical summary:",
        patient.to_prompt_text(include_future=True),
    ]
    if patient.fhir is not None:
        parts += ["Structured FHIR R4 Bundle (JSON):", json.dumps(patient.fhir, separators=(",", ":"), sort_keys=True)]
    parts += [
        "Respond with a single JSON object and nothing else, with exactly these keys:",
        f'"decision" (one of [{allowed}]), "confidence" (number 0-1), '
        '"contraindication_flagged" (true/false), "clinical_rationale" (one concise paragraph grounded only in the chart), '
        '"citations" (list of chart item IDs supporting the decision).',
    ]
    return "\n\n".join(parts)


def parse_model_response(model: str, text: str, allowed: tuple[str, ...]) -> ModelResponse:
    parsed = _extract_json_object(text)
    if isinstance(parsed, dict):
        decision = str(parsed.get("decision", "")).lower().strip()
        citations_raw = parsed.get("citations", [])
        if not isinstance(citations_raw, list):
            citations_raw = []
        citations = tuple(str(c).strip() for c in citations_raw if str(c).strip())
        rationale = str(parsed.get("rationale", parsed.get("clinical_rationale", "")))
        confidence = _clamp_float(parsed.get("confidence", 0.0))
        flagged = parsed.get("contraindication_flagged", False)
        contraindication_flagged = flagged if isinstance(flagged, bool) else str(flagged).strip().lower() == "true"
    else:
        lower = text.lower()
        decision = "unknown"
        for option in allowed:
            if re.search(rf"\b{re.escape(option)}\b", lower):
                decision = option
                break
        citations = tuple(sorted(set(re.findall(r"\b[a-z]+_[0-9]{8}_[a-z0-9_]+\b", text))))
        rationale = text.strip()
        confidence = 0.0
        contraindication_flagged = bool(re.search(r"contraindicat", lower))
    if decision not in allowed:
        decision = "unknown"
    return ModelResponse(
        model=model,
        decision=decision,
        citations=citations,
        rationale=rationale,
        confidence=confidence,
        contraindication_flagged=contraindication_flagged,
        raw_text=text,
    )


def _extract_json_object(text: str) -> dict[str, Any] | None:
    cleaned = _strip_code_fence(text.strip())
    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        parsed = None
    if isinstance(parsed, dict):
        return parsed
    decoder = json.JSONDecoder()
    for match in re.finditer(r"\{", text):
        try:
            candidate, _ = decoder.raw_decode(text[match.start() :])
        except json.JSONDecodeError:
            continue
        if isinstance(candidate, dict):
            return candidate
    return None


def _strip_code_fence(text: str) -> str:
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```$", "", text)
    return text


def _clamp_float(value: Any) -> float:
    try:
        confidence = float(value)
    except (TypeError, ValueError):
        confidence = 0.0
    return max(0.0, min(1.0, confidence))
