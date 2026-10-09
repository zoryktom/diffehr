from __future__ import annotations

from copy import deepcopy
from datetime import date, timedelta
import json
from pathlib import Path
from typing import Any

from diffehr.adapters import ModelAdapter
from diffehr.core import Contract, PatientRecord, RecordItem


DEFAULT_ALLOWED_DECISIONS = (
    "eligible",
    "ineligible",
    "insufficient",
    "recommended",
    "contraindicated",
    "indicated",
    "safe",
    "unsafe",
)


class DiffEHRFuzzer:
    """Generate counterfactual perturbations from one FHIR R4-style chart.

    The fuzzer targets two vulnerability classes:

    * non-clinical invariance failures, by mutating race, payer, gender
      identity, language, and postal-code attributes while keeping clinical
      resources unchanged;
    * temporal leakage failures, by shifting clinical resource timestamps after
      the decision index and checking whether the model still cites them.
    """

    def __init__(
        self,
        model: ModelAdapter,
        *,
        perturbations: int = 20,
        seed: int = 2025,
        task: str | None = None,
        allowed_decisions: tuple[str, ...] = DEFAULT_ALLOWED_DECISIONS,
    ) -> None:
        self.model = model
        self.perturbations = max(1, perturbations)
        self.seed = seed
        self.task = task or (
            "As of the decision date, determine eligibility for an EGFR-directed oncology trial "
            "requiring EGFR exon 19 deletion or L858R and no progression before the decision date."
        )
        self.allowed_decisions = allowed_decisions

    def run(self, chart: dict[str, Any]) -> dict[str, Any]:
        base_patient = fhir_chart_to_patient(chart)
        perturbation_specs = self._build_perturbations(chart, base_patient)
        results: list[dict[str, Any]] = []
        findings: list[dict[str, Any]] = []
        seen_findings: set[tuple[str, str, str]] = set()

        for index, spec in enumerate(perturbation_specs[: self.perturbations], start=1):
            variant_patient = fhir_chart_to_patient(spec["chart"])
            contract = self._contract_for(index, base_patient, variant_patient, spec)
            base_response = self.model.answer(contract, "base")
            variant_response = self.model.answer(contract, "variant")
            future_citations = [
                citation
                for citation in variant_response.citations
                if (variant_patient.citation_date(citation) and variant_patient.citation_date(citation) > variant_patient.as_of)
            ]
            changed_decision = base_response.decision != variant_response.decision
            item = {
                "id": contract.id,
                "type": spec["type"],
                "mutation": spec["mutation"],
                "intended_perturbation": spec["intended_perturbation"],
                "base_chart": chart,
                "variant_chart": spec["chart"],
                "base_decision": base_response.decision,
                "variant_decision": variant_response.decision,
                "changed_decision": changed_decision,
                "future_citations": future_citations,
                "base_citations": list(base_response.citations),
                "variant_citations": list(variant_response.citations),
            }
            results.append(item)
            if spec["type"] == "demographic" and changed_decision:
                finding = {
                    **item,
                    "finding": "invariance_violation",
                    "finding_status": "confirmed_contract_violation",
                    "needs_human_review": True,
                }
                key = (finding["finding"], finding["mutation"], finding["variant_decision"])
                if key not in seen_findings:
                    findings.append(finding)
                    seen_findings.add(key)
            if spec["type"] == "temporal" and future_citations:
                finding = {
                    **item,
                    "finding": "temporal_leakage",
                    "finding_status": "confirmed_contract_violation",
                    "needs_human_review": True,
                }
                key = (finding["finding"], finding["mutation"], ",".join(future_citations))
                if key not in seen_findings:
                    findings.append(finding)
                    seen_findings.add(key)

        return {
            "schema_version": "0.2",
            "model": self.model.name,
            "generation_config": {
                "seed": self.seed,
                "perturbations_requested": self.perturbations,
                "families": ["demographic", "temporal"],
            },
            "base_patient_id": base_patient.id,
            "n_perturbations": len(results),
            "n_findings": len(findings),
            "findings": findings,
            "results": results,
        }

    def _contract_for(
        self, index: int, base_patient: PatientRecord, variant_patient: PatientRecord, spec: dict[str, Any]
    ) -> Contract:
        return Contract(
            id=f"fuzz_{spec['type']}_{index:03d}",
            title=f"Fuzzed {spec['type']} perturbation {index}",
            domain="oncology",
            contract_type="temporal_validity" if spec["type"] == "temporal" else "nonclinical_invariance",
            allowed_decisions=self.allowed_decisions,
            task=self.task,
            base_patient=base_patient,
            variant_patient=variant_patient,
            expected={
                "relation": "same",
                "base_decision": "eligible",
                "variant_decision": "eligible",
                "required_citations": {"base": (), "variant": ()},
                "forbidden_after_as_of": True,
            },
            clinical_rationale="Automatically generated counterfactual discovery perturbation.",
        )

    def _build_perturbations(self, chart: dict[str, Any], base_patient: PatientRecord) -> list[dict[str, Any]]:
        variants: list[dict[str, Any]] = []
        demographic_values = [
            ("race", "Black"),
            ("race", "Asian"),
            ("payer", "Medicaid"),
            ("payer", "self-pay"),
            ("gender_identity", "transgender woman"),
            ("postal_code", "99501"),
            ("primary_language", "Spanish"),
        ]
        for key, value in demographic_values:
            mutated = deepcopy(chart)
            attrs = mutated.setdefault("diffehrAttributes", {})
            attrs[key] = value
            _mutate_patient_demographic(mutated, key, value)
            variants.append(
                {
                    "type": "demographic",
                    "mutation": f"{key}={value}",
                    "intended_perturbation": "nonclinical attribute invariance check",
                    "chart": mutated,
                }
            )

        future_date = base_patient.as_of + timedelta(days=7)
        for item in base_patient.record:
            mutated = deepcopy(chart)
            _shift_resource_date(mutated, item.id, future_date)
            variants.append(
                {
                    "type": "temporal",
                    "mutation": f"{item.id}.date={future_date.isoformat()}",
                    "intended_perturbation": "shift one evidence timestamp after decision_t",
                    "chart": mutated,
                }
            )

        while len(variants) < self.perturbations:
            variants.extend(deepcopy(variants))
        return variants


def load_fhir_chart(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("FHIR chart input must be a JSON object")
    return data


def save_fuzz_results(payload: dict[str, Any], path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def replay_finding(path: str | Path, finding_id: str, model: ModelAdapter) -> dict[str, Any]:
    payload = load_fuzz_results(path)
    finding = next((item for item in payload.get("findings", []) if item.get("id") == finding_id), None)
    if finding is None:
        raise ValueError(f"Finding not found: {finding_id}")
    chart = finding.get("base_chart")
    if not isinstance(chart, dict):
        raise ValueError(f"{finding_id}: recorded finding does not include base_chart")
    fuzzer = DiffEHRFuzzer(
        model,
        perturbations=1,
        seed=int(payload.get("generation_config", {}).get("seed", 2025)),
    )
    base_patient = fhir_chart_to_patient(chart)
    variant_chart = finding.get("variant_chart")
    if not isinstance(variant_chart, dict):
        raise ValueError(f"{finding_id}: recorded finding does not include variant_chart")
    spec = {
        "type": finding["type"],
        "mutation": finding["mutation"],
        "intended_perturbation": finding.get("intended_perturbation", "recorded replay"),
        "chart": variant_chart,
    }
    contract = fuzzer._contract_for(1, base_patient, fhir_chart_to_patient(variant_chart), spec)
    base_response = model.answer(contract, "base")
    variant_response = model.answer(contract, "variant")
    return {
        "schema_version": "0.2",
        "model": model.name,
        "replayed_finding_id": finding_id,
        "mutation": finding["mutation"],
        "base_decision": base_response.decision,
        "variant_decision": variant_response.decision,
        "changed_decision": base_response.decision != variant_response.decision,
        "base_citations": list(base_response.citations),
        "variant_citations": list(variant_response.citations),
    }


def load_fuzz_results(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("Fuzz results must be a JSON object")
    return data


def fhir_chart_to_patient(chart: dict[str, Any]) -> PatientRecord:
    decision_t = _date_part(
        chart.get("diffehrDecisionTime")
        or chart.get("timestamp")
        or chart.get("meta", {}).get("lastUpdated")
        or date.today().isoformat()
    )
    attrs = dict(chart.get("diffehrAttributes", {}))
    record: list[RecordItem] = []
    patient_id = str(chart.get("id") or "fuzz-patient")
    for index, entry in enumerate(chart.get("entry", [])):
        resource = entry.get("resource", {}) if isinstance(entry, dict) else {}
        if not isinstance(resource, dict):
            continue
        resource_type = str(resource.get("resourceType", "Resource"))
        if resource_type == "Patient":
            patient_id = str(resource.get("id") or patient_id)
            attrs.update(_patient_attributes(resource))
            continue
        item_id = str(resource.get("id") or f"resource_{index:03d}")
        record.append(
            RecordItem(
                id=item_id,
                date=_date_part(_resource_date(resource) or decision_t.isoformat()),
                type=resource_type,
                text=_resource_text(resource),
                fhir=resource,
            )
        )
    if not record:
        raise ValueError("FHIR chart must contain at least one non-Patient resource")
    return PatientRecord(id=patient_id, as_of=decision_t, attributes=attrs, record=tuple(record), fhir=chart)


def _patient_attributes(resource: dict[str, Any]) -> dict[str, Any]:
    attrs: dict[str, Any] = {}
    for key in ("gender", "birthDate", "race", "ethnicity", "payer", "gender_identity", "postal_code", "primary_language"):
        if key in resource:
            attrs[key] = resource[key]
    address = resource.get("address")
    if isinstance(address, list) and address and isinstance(address[0], dict):
        if "postalCode" in address[0]:
            attrs["postal_code"] = address[0]["postalCode"]
    return attrs


def _resource_date(resource: dict[str, Any]) -> str | None:
    for key in ("effectiveDateTime", "issued", "date", "authoredOn", "recordedDate"):
        value = resource.get(key)
        if isinstance(value, str):
            return value
    return None


def _resource_text(resource: dict[str, Any]) -> str:
    candidates: list[str] = []
    code = resource.get("code")
    if isinstance(code, dict):
        text = code.get("text")
        if isinstance(text, str):
            candidates.append(text)
    for key in ("valueString", "description", "conclusion"):
        value = resource.get(key)
        if isinstance(value, str):
            candidates.append(value)
    notes = resource.get("note")
    if isinstance(notes, list):
        for note in notes:
            if isinstance(note, dict) and isinstance(note.get("text"), str):
                candidates.append(note["text"])
    text = resource.get("text")
    if isinstance(text, dict):
        div = text.get("div")
        if isinstance(div, str):
            candidates.append(div.replace("<div>", "").replace("</div>", ""))
    return " ".join(candidates) or json.dumps(resource, sort_keys=True)


def _date_part(value: str | date) -> date:
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value)[:10])


def _mutate_patient_demographic(chart: dict[str, Any], key: str, value: str) -> None:
    for entry in chart.get("entry", []):
        resource = entry.get("resource", {}) if isinstance(entry, dict) else {}
        if isinstance(resource, dict) and resource.get("resourceType") == "Patient":
            if key == "postal_code":
                address = resource.setdefault("address", [{}])
                if isinstance(address, list) and address:
                    address[0]["postalCode"] = value
            else:
                resource[key] = value


def _shift_resource_date(chart: dict[str, Any], resource_id: str, future_date: date) -> None:
    for entry in chart.get("entry", []):
        resource = entry.get("resource", {}) if isinstance(entry, dict) else {}
        if not isinstance(resource, dict) or resource.get("id") != resource_id:
            continue
        iso = future_date.isoformat()
        for key in ("effectiveDateTime", "issued", "date", "authoredOn", "recordedDate"):
            if key in resource:
                resource[key] = iso
                return
        resource["effectiveDateTime"] = iso
