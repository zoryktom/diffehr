from __future__ import annotations

from dataclasses import dataclass
import json
import os
import re
import urllib.error
import urllib.request

from .contracts import Contract, PatientRecord


@dataclass(frozen=True)
class ModelResponse:
    model: str
    decision: str
    citations: tuple[str, ...]
    rationale: str
    confidence: float
    raw_text: str


class ClinicalAI:
    name = "base"

    def answer(self, contract: Contract, side: str) -> ModelResponse:
        raise NotImplementedError


def parse_model_response(model: str, text: str, allowed: tuple[str, ...]) -> ModelResponse:
    parsed = None
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if match:
            try:
                parsed = json.loads(match.group(0))
            except json.JSONDecodeError:
                parsed = None
    if isinstance(parsed, dict):
        decision = str(parsed.get("decision", "")).lower().strip()
        citations_raw = parsed.get("citations", [])
        if not isinstance(citations_raw, list):
            citations_raw = []
        citations = tuple(str(c) for c in citations_raw)
        rationale = str(parsed.get("rationale", ""))
        try:
            confidence = float(parsed.get("confidence", 0.0))
        except (TypeError, ValueError):
            confidence = 0.0
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
        confidence=max(0.0, min(1.0, confidence)),
        raw_text=text,
    )


class OracleAgent(ClinicalAI):
    name = "oracle"

    def answer(self, contract: Contract, side: str) -> ModelResponse:
        expected = contract.expected.base_decision if side == "base" else contract.expected.variant_decision
        citations = contract.expected.required_citations.get(side, ())
        payload = {
            "decision": expected,
            "citations": list(citations),
            "rationale": "Oracle baseline returns the hidden contract answer for pipeline validation.",
            "confidence": 1.0,
        }
        return ModelResponse(
            model=self.name,
            decision=expected,
            citations=tuple(citations),
            rationale=payload["rationale"],
            confidence=1.0,
            raw_text=json.dumps(payload),
        )


class HeuristicOncologyAgent(ClinicalAI):
    name = "heuristic-oncology"

    def __init__(self, respect_temporal: bool = True, insurance_bias: bool = False) -> None:
        self.respect_temporal = respect_temporal
        self.insurance_bias = insurance_bias
        if respect_temporal and not insurance_bias:
            self.name = "heuristic-oncology"
        elif not respect_temporal and insurance_bias:
            self.name = "reckless-oncology"
        else:
            self.name = "custom-oncology"

    def answer(self, contract: Contract, side: str) -> ModelResponse:
        patient = contract.base_patient if side == "base" else contract.variant_patient
        items = patient.visible_items() if self.respect_temporal else list(patient.record)
        full = "\n".join(item.text.lower() for item in items)
        citations: list[str] = []

        if self.insurance_bias:
            insurance = str(patient.attributes.get("insurance", "")).lower()
            if "medicaid" in insurance or "uninsured" in insurance:
                return self._response(contract, "ineligible", ["demo_00000000_bias"], "Biased baseline overreacted to payer status.")

        decision = "insufficient"
        rationale = "No decisive chart evidence found."

        if "paclitaxel" in contract.task.lower():
            if "paclitaxel" in full and ("anaphylaxis" in full or "severe infusion reaction" in full):
                decision = "unsafe"
                rationale = "Chart documents a severe paclitaxel reaction."
                citations = self._find(items, ["paclitaxel", "anaphylaxis", "severe infusion reaction"])
            else:
                decision = "safe"
                rationale = "No paclitaxel allergy or severe reaction is documented before the decision date."
                citations = self._find(items, ["allergies", "paclitaxel"])
        elif "alk" in contract.id.lower() or "alta-alk" in contract.task.lower():
            if "alk rearrangement positive" in full or "alk-positive" in full:
                decision = "eligible"
                rationale = "ALK-positive disease is documented."
                citations = self._find(items, ["alk"])
            elif "alk rearrangement negative" in full:
                decision = "ineligible"
                rationale = "ALK rearrangement is documented negative."
                citations = self._find(items, ["alk"])
            else:
                decision = "insufficient"
                rationale = "ALK status is not documented before the decision date."
                citations = self._find(items, ["molecular", "pathology"])
        elif "temporal_leakage" in contract.id.lower():
            if "progressive disease" in full or "progression" in full:
                decision = "ineligible"
                rationale = "Disease progression is documented in available records."
                citations = self._find(items, ["progressive disease", "progression"])
            else:
                decision = "eligible"
                rationale = "No progression is documented before the decision date."
                citations = self._find(items, ["stable disease", "ct"])
        elif "ecog" in contract.id.lower() or "ecog-lung" in contract.task.lower():
            if re.search(r"\becog\s*3\b|\becog performance status is 3\b", full):
                decision = "ineligible"
                rationale = "ECOG performance status exceeds the trial threshold."
                citations = self._find(items, ["ecog"])
            elif re.search(r"\becog\s*[01]\b|\becog performance status is 1\b", full):
                decision = "eligible"
                rationale = "ECOG performance status is within the trial threshold."
                citations = self._find(items, ["ecog"])
        else:
            if "egfr negative" in full or "egfr wild type" in full or "no exon 19 deletion" in full:
                decision = "ineligible"
                rationale = "EGFR sensitizing mutation is not documented."
                citations = self._find(items, ["egfr"])
            elif "egfr exon 19 deletion positive" in full or "egfr-positive" in full:
                decision = "eligible"
                rationale = "EGFR sensitizing mutation is documented."
                citations = self._find(items, ["egfr"])
            elif "egfr pending" in full or "molecular testing pending" in full:
                decision = "insufficient"
                rationale = "Molecular eligibility evidence is pending."
                citations = self._find(items, ["pending", "molecular"])

        return self._response(contract, decision, citations, rationale)

    def _find(self, items, needles: list[str]) -> list[str]:
        hits = []
        for item in items:
            text = item.text.lower()
            if any(needle in text for needle in needles):
                hits.append(item.id)
        return hits[:3]

    def _response(self, contract: Contract, decision: str, citations: list[str], rationale: str) -> ModelResponse:
        payload = {
            "decision": decision,
            "citations": citations,
            "rationale": rationale,
            "confidence": 0.72,
        }
        return parse_model_response(self.name, json.dumps(payload), contract.allowed_decisions)


class OpenAIResponsesModel(ClinicalAI):
    def __init__(self, model_id: str = "gpt-5-mini", timeout: int = 90) -> None:
        self.model_id = model_id
        self.timeout = timeout
        self.name = f"openai:{model_id}"

    def answer(self, contract: Contract, side: str) -> ModelResponse:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is not set")
        base_url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
        url = base_url.rstrip("/") + "/responses"
        payload = {
            "model": self.model_id,
            "input": contract.prompt(side),
            "temperature": 0,
        }
        request = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                data = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"OpenAI API error {exc.code}: {body}") from exc
        text = _extract_response_text(data)
        return parse_model_response(self.name, text, contract.allowed_decisions)


def _extract_response_text(data) -> str:
    if isinstance(data, dict) and isinstance(data.get("output_text"), str):
        return data["output_text"]
    texts: list[str] = []

    def walk(value):
        if isinstance(value, dict):
            if isinstance(value.get("text"), str):
                texts.append(value["text"])
            for child in value.values():
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)

    walk(data)
    return "\n".join(texts) if texts else json.dumps(data)


def make_model(name: str) -> ClinicalAI:
    if name == "oracle":
        return OracleAgent()
    if name in {"heuristic", "heuristic-oncology"}:
        return HeuristicOncologyAgent(respect_temporal=True, insurance_bias=False)
    if name in {"reckless", "reckless-oncology"}:
        return HeuristicOncologyAgent(respect_temporal=False, insurance_bias=True)
    if name.startswith("openai:"):
        return OpenAIResponsesModel(name.split(":", 1)[1])
    raise ValueError(f"Unknown model: {name}")
