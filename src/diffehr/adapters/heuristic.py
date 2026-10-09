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
            insurance = str(patient.attributes.get("insurance", patient.attributes.get("payer", ""))).lower()
            if (
                "medicaid" in insurance
                or "uninsured" in insurance
                or "self-pay" in insurance
                or "self pay" in insurance
            ):
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
        if contract.domain == "cardiology":
            decision, citations, rationale = self._answer_cardiology(contract, items, full)
        elif contract.domain == "infectious_disease":
            decision, citations, rationale = self._answer_infectious_disease(contract, items, full)
        elif "paclitaxel" in task:
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
            decision, citations, rationale = self._answer_oncology_general(contract, items, full)

        return self._response(contract, decision, citations, rationale)

    def _answer_cardiology(self, contract: Contract, items: list[RecordItem], full: str) -> tuple[str, list[str], str]:
        task = contract.task.lower()
        if "doac" in task or "anticoagulation" in task:
            if re.search(r"crcl|creatinine clearance", full) and re.search(r"\b1[0-4]\b|below 15|severe renal", full):
                return (
                    "contraindicated",
                    self._find(items, ["creatinine clearance", "below 15", "severe renal", "crcl"]),
                    "Severe renal failure below the DOAC threshold is documented.",
                )
            if "atrial fibrillation" in full or "non-valvular" in full:
                return (
                    "recommended",
                    self._find(items, ["atrial fibrillation", "creatinine clearance", "doac", "cha2ds2"]),
                    "Atrial fibrillation anticoagulation criteria are met without severe renal contraindication.",
                )
        if "statin" in task:
            if "troponin pending" in full or "nstemi not confirmed" in full:
                if "markedly elevated" in full or "confirming nstemi" in full:
                    return (
                        "indicated",
                        self._find(items, ["troponin", "nstemi", "elevated"]),
                        "NSTEMI is confirmed by available troponin evidence.",
                    )
                return (
                    "insufficient",
                    self._find(items, ["troponin pending", "nstemi not confirmed", "chest pain"]),
                    "NSTEMI is not confirmed by evidence available at the decision date.",
                )
            if "acute liver failure" in full or "active transaminitis" in full or re.search(r"ast\s*9|alt\s*11", full):
                return (
                    "contraindicated",
                    self._find(items, ["acute liver failure", "active transaminitis", "ast", "alt"]),
                    "Active liver failure or severe transaminitis is documented.",
                )
            if "nstemi" in full or "myocardial infarction" in full:
                return (
                    "indicated",
                    self._find(items, ["nstemi", "myocardial infarction", "statin", "ast", "alt"]),
                    "Post-MI secondary prevention statin therapy is indicated.",
                )
        if "p2y12" in task or "antiplatelet" in task or "cyp2c19" in task:
            if "normal metabolizer" in full or "no loss-of-function" in full:
                return (
                    "clopidogrel",
                    self._find(items, ["stent", "drug-eluting", "cyp2c19", "normal metabolizer"]),
                    "No CYP2C19 loss-of-function allele is documented.",
                )
            if "loss-of-function" in full or "poor metabolizer" in full:
                return (
                    "ticagrelor",
                    self._find(items, ["cyp2c19", "loss-of-function", "poor metabolizer"]),
                    "CYP2C19 loss-of-function supports avoiding clopidogrel.",
                )
        if "beta-blocker" in task or "hfrEF".lower() in task:
            has_decompensation = (
                "cardiogenic shock" in full
                or "inotropes" in full
                or ("acute decompensated" in full and "no acute decompensated" not in full)
            )
            if has_decompensation:
                return (
                    "defer",
                    self._find(items, ["cardiogenic shock", "acute decompensated", "inotropes"]),
                    "Acute decompensated heart failure warrants deferring initiation.",
                )
            if ("lvef 30" in full or "ejection fraction 30" in full) and ("stable" in full or "euvolemic" in full):
                return (
                    "start",
                    self._find(items, ["lvef 30", "ejection fraction 30", "stable", "euvolemic"]),
                    "Stable HFrEF with reduced LVEF supports beta-blocker initiation.",
                )
        return "insufficient", [], "No decisive cardiology evidence found."

    def _answer_infectious_disease(
        self, contract: Contract, items: list[RecordItem], full: str
    ) -> tuple[str, list[str], str]:
        task = contract.task.lower()
        if "sepsis" in task or "beta-lactam" in task:
            if "penicillin allergy with anaphylaxis" in full or ("anaphylaxis" in full and "penicillin" in full):
                return (
                    "avoid_beta_lactam",
                    self._find(items, ["penicillin", "anaphylaxis", "airway swelling"]),
                    "Anaphylactic penicillin allergy is documented.",
                )
            if "sepsis" in full or "septic shock" in full:
                return (
                    "beta_lactam",
                    self._find(items, ["sepsis", "septic shock", "beta-lactam", "no known drug allergy"]),
                    "Sepsis evidence supports empiric beta-lactam therapy without anaphylactic allergy.",
                )
        if "step down" in task or "step-down" in task or "community-acquired pneumonia" in task:
            if "vasopressors" in full or "hypotension" in full or "88 percent" in full or "high-flow" in full:
                return (
                    "iv_continue",
                    self._find(items, ["hypotension", "vasopressors", "high-flow", "88 percent"]),
                    "Hemodynamic or oxygenation instability requires continuing IV therapy.",
                )
            if "hemodynamically stable" in full or "blood pressure stable" in full or "tolerating oral" in full:
                return (
                    "oral_stepdown",
                    self._find(items, ["community-acquired pneumonia", "stable", "tolerating oral", "room air"]),
                    "Stability criteria for oral step-down are documented.",
                )
        if "carbapenem" in task or "de-escalate" in task:
            if "susceptibility pending" in full and not ("ceftriaxone susceptible" in full or "no esbl" in full):
                return (
                    "continue_carbapenem",
                    self._find(items, ["meropenem", "susceptibility pending", "gram-negative rods"]),
                    "Susceptibility is pending, so de-escalation is not yet supported.",
                )
            if "esbl positive" in full or "resistant to ceftriaxone" in full:
                return (
                    "continue_carbapenem",
                    self._find(items, ["esbl", "resistant to ceftriaxone", "meropenem"]),
                    "ESBL resistance supports continuing carbapenem therapy.",
                )
            if "ceftriaxone susceptible" in full or "no esbl" in full:
                return (
                    "de_escalate",
                    self._find(items, ["ceftriaxone susceptible", "no esbl", "susceptible"]),
                    "Culture susceptibility supports narrowing from carbapenem therapy.",
                )
        if "vancomycin" in task or "mrsa" in task:
            if "mrsa nasal pcr negative" in full:
                return (
                    "stop_vancomycin",
                    self._find(items, ["mrsa nasal pcr negative", "pcr negative"]),
                    "Negative MRSA nasal PCR supports stopping empiric vancomycin.",
                )
            if "mrsa nasal pcr positive" in full:
                return (
                    "continue_vancomycin",
                    self._find(items, ["mrsa nasal pcr positive", "pcr positive"]),
                    "Positive MRSA nasal PCR supports continuing vancomycin.",
                )
            if "vancomycin" in full and "pending" in full:
                return (
                    "continue_vancomycin",
                    self._find(items, ["vancomycin", "pending"]),
                    "MRSA testing is pending, so empiric vancomycin remains supported.",
                )
        return "insufficient", [], "No decisive infectious disease evidence found."

    def _answer_oncology_general(
        self, contract: Contract, items: list[RecordItem], full: str
    ) -> tuple[str, list[str], str]:
        task = contract.task.lower()
        if "trastuzumab" in task or "her2" in task:
            if "recovered to 55" in full:
                return (
                    "eligible",
                    self._find(items, ["her2", "recovered to 55", "lvef"]),
                    "Available evidence documents HER2 positivity and recovered LVEF.",
                )
            if "lvef 38" in full or "lvef 40" in full or "below 45" in full or "below treatment threshold" in full:
                return (
                    "ineligible",
                    self._find(items, ["lvef 38", "lvef 40", "below 45", "below treatment threshold"]),
                    "Baseline LVEF is below the eligibility threshold.",
                )
            if "her2 3+ positive" in full and ("lvef 58" in full or "lvef 60" in full):
                return (
                    "eligible",
                    self._find(items, ["her2 3+ positive", "lvef 58", "lvef 60"]),
                    "HER2 positivity and adequate LVEF are documented.",
                )
            if "pending" in full:
                return (
                    "insufficient",
                    self._find(items, ["pending", "her2 testing"]),
                    "HER2 eligibility evidence is pending at the decision date.",
                )
        if "immune checkpoint" in task or "checkpoint inhibitor" in task:
            if "active severe autoimmune flare" in full or "prednisone 60" in full:
                return (
                    "ineligible",
                    self._find(items, ["active severe autoimmune flare", "prednisone 60"]),
                    "Active severe autoimmune flare is documented.",
                )
            if "remission" in full or "no active autoimmune flare" in full:
                return (
                    "eligible",
                    self._find(items, ["metastatic melanoma", "remission", "no active autoimmune"]),
                    "No active autoimmune contraindication is documented.",
                )
        if "braf" in task:
            if "wild type" in full or "not detected" in full:
                return (
                    "ineligible",
                    self._find(items, ["braf", "wild type", "not detected"]),
                    "BRAF V600 mutation is not documented.",
                )
            if "v600e mutation detected" in full or "braf v600 mutation" in full:
                return (
                    "eligible",
                    self._find(items, ["braf", "v600e", "mutation detected"]),
                    "BRAF V600 mutation is documented.",
                )
        if "cytotoxic chemotherapy" in task or "anc" in task:
            if "anc 400" in full or "severe neutropenia" in full:
                return (
                    "unsafe",
                    self._find(items, ["anc 400", "severe neutropenia"]),
                    "Severe neutropenia is documented.",
                )
            if "anc 2400" in full:
                return (
                    "safe",
                    self._find(items, ["anc 2400", "absolute neutrophil"]),
                    "ANC is above the chemotherapy threshold.",
                )
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
        else:
            decision = "insufficient"
            rationale = "No decisive oncology evidence found."
            citations = []
        return decision, citations, rationale

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
