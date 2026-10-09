from __future__ import annotations

from abc import ABC, abstractmethod
import json
import re
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from diffehr.core import Contract


class ModelResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    model: str = Field(min_length=1)
    decision: str = Field(min_length=1)
    citations: tuple[str, ...] = ()
    rationale: str = ""
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
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


def parse_model_response(model: str, text: str, allowed: tuple[str, ...]) -> ModelResponse:
    parsed = _extract_json_object(text)
    if isinstance(parsed, dict):
        decision = str(parsed.get("decision", "")).lower().strip()
        citations_raw = parsed.get("citations", [])
        if not isinstance(citations_raw, list):
            citations_raw = []
        citations = tuple(str(c).strip() for c in citations_raw if str(c).strip())
        rationale = str(parsed.get("rationale", ""))
        confidence = _clamp_float(parsed.get("confidence", 0.0))
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
    if decision not in allowed:
        decision = "unknown"
    return ModelResponse(
        model=model,
        decision=decision,
        citations=citations,
        rationale=rationale,
        confidence=confidence,
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
