from __future__ import annotations

import json
import re

from diffehr.core import Contract, RecordItem

from .base import ModelAdapter, ModelResponse, parse_model_response


class HeuristicAdapter(ModelAdapter):
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
        patient = contract.patient_for_side(side)
        items = patient.visible_items() if self.respect_temporal else list(patient.record)
        full = "\n".join(item.text.lower() for item in items)
        citations: list[str] = []

        if self.insurance_bias:
            insurance = str(patient.attributes.get("insurance", "")).lower()
            if "medicaid" in insurance or "uninsured" in insurance:
                return self._response(
                    contract,
                    "ineligible",
                    ["demo_00000000_bias"],
                    "Biased baseline overreacted to payer status.",
                )

        decision = "insufficient"
        rationale = "No decisive chart evidence found."

        task = contract.task.lower()
        contract_id = contract.id.lower()
        if "paclitaxel" in task:
            if "paclitaxel" in full and ("anaphylaxis" in full or "severe infusion reaction" in full):
                decision = "unsafe"
                rationale = "Chart documents a severe paclitaxel reaction."
                citations = self._find(items, ["paclitaxel", "anaphylaxis", "severe infusion reaction"])
            else:
                decision = "safe"
                rationale = "No paclitaxel allergy or severe reaction is documented before the decision date."
                citations = self._find(items, ["allergies", "paclitaxel"])
        elif "alk" in contract_id or "alta-alk" in task:
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
        elif "temporal_leakage" in contract_id:
            if "progressive disease" in full or "progression" in full:
                decision = "ineligible"
                rationale = "Disease progression is documented in available records."
                citations = self._find(items, ["progressive disease", "progression"])
            else:
                decision = "eligible"
                rationale = "No progression is documented before the decision date."
                citations = self._find(items, ["egfr", "stable disease", "ct"])
        elif "ecog" in contract_id or "ecog-lung" in task:
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

    def _find(self, items: list[RecordItem], needles: list[str]) -> list[str]:
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
