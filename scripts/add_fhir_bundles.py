"""Materialize a FHIR R4 Bundle for hand-authored contracts that only carry flat record items.

Idempotent: charts that already embed a Bundle are left untouched. Run
`python -m diffehr manifest examples` afterwards to refresh checksums.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OBSERVATION_TYPES = {"laboratory", "pathology", "imaging", "genomics", "echocardiogram", "vitals", "microbiology"}


def resource_for(item: dict[str, Any], patient_id: str) -> dict[str, Any]:
    base = {"id": item["id"], "subject": {"reference": f"Patient/{patient_id}"}}
    kind, day, text = item["type"], item["date"], item["text"]
    if kind in OBSERVATION_TYPES:
        return {
            "resourceType": "Observation",
            "status": "final",
            "code": {"text": kind},
            "effectiveDateTime": day,
            "valueString": text,
            **base,
        }
    if kind == "medication":
        return {
            "resourceType": "MedicationRequest",
            "status": "active",
            "intent": "order",
            "medicationCodeableConcept": {"text": text},
            "authoredOn": day,
            **base,
        }
    if kind == "procedure":
        return {
            "resourceType": "Procedure",
            "status": "completed",
            "code": {"text": text},
            "performedDateTime": day,
            **base,
        }
    if kind == "allergy":
        return {"resourceType": "AllergyIntolerance", "code": {"text": text}, "recordedDate": day, **base}
    return {
        "resourceType": "DocumentReference",
        "status": "current",
        "type": {"text": kind},
        "date": day,
        "description": text,
        **base,
    }


def bundle_for(chart: dict[str, Any]) -> dict[str, Any]:
    pid = chart["id"]
    attrs = chart.get("attributes", {})
    patient = {
        "resourceType": "Patient",
        "id": pid,
        "gender": str(attrs.get("sex", "unknown")),
        "extension": [{"url": "attributes", "valueString": json.dumps(attrs, sort_keys=True)}],
    }
    entries = [{"resource": patient}] + [{"resource": resource_for(i, pid)} for i in chart["record"]]
    return {"resourceType": "Bundle", "type": "collection", "id": f"bundle-{pid}", "entry": entries}


def main() -> None:
    changed = 0
    for path in sorted((ROOT / "examples").glob("*/contracts/*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        touched = False
        for side in ("base_patient", "variant_patient"):
            if not data[side].get("fhir"):
                data[side]["fhir"] = bundle_for(data[side])
                touched = True
        if touched:
            path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
            changed += 1
    print(f"Added FHIR bundles to {changed} contract(s).")


if __name__ == "__main__":
    main()
