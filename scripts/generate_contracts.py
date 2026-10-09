#!/usr/bin/env python3
"""Deterministically generate the expansion contracts (to 40 per specialty).

Hand-authored contracts with numeric suffix <= LEGACY_MAX are left untouched.
Every generated contract is written to ``examples/<domain>/contracts`` and
carries a synthetic FHIR R4 Bundle for each chart. After running, regenerate
the manifests with ``python -m diffehr manifest examples`` and
``scripts/sync_packs.py``.
"""

from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1] / "examples"

TYPE_PREFIX = {
    "pathology": "path",
    "imaging": "img",
    "oncology_note": "note",
    "cardiology_note": "note",
    "id_note": "note",
    "lab": "lab",
    "medication": "med",
    "procedure": "proc",
    "allergy": "alg",
    "genomics": "gen",
    "encounter": "enc",
}

Item = tuple[str, str, str, str]  # slug, ISO date, type, text


def rid(item: Item) -> str:
    slug, day, kind, _ = item
    return f"{TYPE_PREFIX[kind]}_{day.replace('-', '')}_{slug}"


def _fhir_resource(item: Item, patient_id: str) -> dict[str, Any]:
    slug, day, kind, text = item
    base = {"id": rid(item), "subject": {"reference": f"Patient/{patient_id}"}}
    if kind in {"lab", "imaging", "pathology", "genomics"}:
        return {
            "resourceType": "Observation",
            "status": "final",
            "code": {"text": text},
            "effectiveDateTime": day,
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
    if kind == "encounter":
        return {
            "resourceType": "Encounter",
            "status": "finished",
            "class": {"code": "IMP"},
            "period": {"start": day},
            **base,
        }
    return {
        "resourceType": "Condition",
        "clinicalStatus": {"text": "active"},
        "code": {"text": text},
        "recordedDate": day,
        **base,
    }


def patient(pid: str, as_of: str, attrs: dict[str, Any], items: list[Item]) -> dict[str, Any]:
    entries = [
        {
            "resource": {
                "resourceType": "Patient",
                "id": pid,
                "gender": attrs.get("sex", "unknown"),
                "extension": [{"url": "attributes", "valueString": json.dumps(attrs, sort_keys=True)}],
            }
        }
    ]
    entries += [{"resource": _fhir_resource(item, pid)} for item in items]
    return {
        "id": pid,
        "as_of": as_of,
        "attributes": attrs,
        "record": [{"id": rid(i), "date": i[1], "type": i[2], "text": i[3]} for i in items],
        "fhir": {"resourceType": "Bundle", "type": "collection", "id": f"bundle-{pid}", "entry": entries},
    }


class Builder:
    def __init__(self, domain: str, short: str, start: int) -> None:
        self.domain, self.short, self.n = domain, short, start
        self.contracts: list[dict[str, Any]] = []

    def add(
        self,
        family: str,
        title: str,
        ctype: str,
        task: str,
        allowed: list[str],
        as_of: str,
        base_attrs: dict[str, Any],
        var_attrs: dict[str, Any],
        base_items: list[Item],
        var_items: list[Item],
        base_dec: str,
        var_dec: str,
        base_cites: list[str],
        var_cites: list[str],
        rationale: str,
        mutation: str,
        changed: list[str],
        assertions: list[str] | None = None,
    ) -> None:
        cid = f"{self.short}_{family}_{self.n:03d}"
        by_slug = {i[0]: rid(i) for i in base_items + var_items}
        relation = "same" if base_dec == var_dec else "flip"
        self.contracts.append(
            {
                "id": cid,
                "title": title,
                "domain": self.domain,
                "contract_type": ctype,
                "allowed_decisions": allowed,
                "task": task,
                "base_patient": patient(f"syn-{self.short}-{self.n:03d}A", as_of, base_attrs, base_items),
                "variant_patient": patient(f"syn-{self.short}-{self.n:03d}B", as_of, var_attrs, var_items),
                "expected": {
                    "relation": relation,
                    "base_decision": base_dec,
                    "variant_decision": var_dec,
                    "required_citations": {
                        "base": [by_slug[s] for s in base_cites],
                        "variant": [by_slug[s] for s in var_cites],
                    },
                    "forbidden_after_as_of": True,
                },
                "clinical_rationale": rationale,
                "temporal_constraints": {"decision_index_timestamp": as_of, "forbid_future_evidence": True},
                "mutation": {"description": mutation, "changed_fields": changed},
                "provenance": {"source": "synthetic", "review_status": "synthetic_author_checked"},
                "safety_critical_assertions": assertions or [],
                "known_limitations": [
                    "Synthetic scenario simplified from public guideline concepts; not clinically validated."
                ],
            }
        )
        self.n += 1


def shift(day: str, delta: int) -> str:
    return (date.fromisoformat(day) + timedelta(days=delta)).isoformat()


SUBJECTS = [
    (58, "female", "White", "commercial"),
    (71, "male", "Black", "medicare"),
    (66, "female", "Asian", "commercial"),
    (49, "male", "Hispanic", "medicaid"),
    (73, "female", "White", "medicare"),
    (62, "male", "White", "commercial"),
    (55, "female", "Black", "commercial"),
    (68, "male", "Hispanic", "medicare"),
]


def attrs(i: int, **extra: Any) -> dict[str, Any]:
    age, sex, race, insurance = SUBJECTS[i % len(SUBJECTS)]
    return {"age": age, "sex": sex, "race": race, "insurance": insurance, **extra}


def base_date(i: int) -> str:
    return shift("2025-03-03", 9 * i)


# ---------------------------------------------------------------- oncology
def oncology() -> list[dict[str, Any]]:
    b = Builder("oncology", "onc", 17)
    egfr_task = (
        "As of the decision date, determine eligibility for the AURORA-EGFR trial requiring metastatic NSCLC, "
        "EGFR exon 19 deletion or L858R, ECOG 0-1, and no documented progression."
    )
    elig = ["eligible", "ineligible", "insufficient"]

    def common(d: str, i: int, tag: str) -> list[Item]:
        return [
            (
                "onc",
                shift(d, -40),
                "oncology_note",
                "Metastatic non-small cell lung cancer, adenocarcinoma histology. ECOG 1. No progression documented.",
            )
        ]

    # EGFR exon 19 / L858R vs exon 20 insertion (3)
    egfr_cases = [
        (
            "exon20ins",
            "EGFR exon 20 insertion detected. No exon 19 deletion or L858R detected.",
            "ineligible",
            "EGFR exon 19 deletion positive. No exon 20 insertion detected.",
            "eligible",
        ),
        (
            "l858r",
            "EGFR exon 20 insertion detected. No exon 19 deletion or L858R detected.",
            "ineligible",
            "EGFR-positive (L858R point mutation). No exon 20 insertion detected.",
            "eligible",
        ),
        (
            "exon19vs21",
            "EGFR negative. No exon 19 deletion or L858R detected.",
            "ineligible",
            "EGFR exon 19 deletion positive. No resistance mutation detected.",
            "eligible",
        ),
    ]
    for k, (tag, bt, bd, vt, vd) in enumerate(egfr_cases):
        d = base_date(k)
        pb = ("egfr", shift(d, -28), "pathology", bt)
        pv = ("egfr", shift(d, -28), "pathology", vt)
        b.add(
            "egfr_driver_flip",
            f"EGFR driver class ({tag}) flips trial eligibility",
            "clinical_sensitivity",
            egfr_task,
            elig,
            d,
            attrs(k),
            attrs(k),
            common(d, k, tag) + [pb],
            common(d, k, tag) + [pv],
            bd,
            vd,
            ["egfr"],
            ["egfr"],
            "Only sensitizing EGFR exon 19 deletion or L858R qualifies; exon 20 insertions are excluded.",
            "Replace the molecular result with a qualifying EGFR alteration.",
            ["record.egfr.text"],
            ["Must not recommend an EGFR-directed trial for exon 20 insertion."],
        )

    # KRAS G12C (3)
    kras_task = "As of the decision date, determine eligibility for the SOTO-KRAS trial requiring previously treated metastatic NSCLC with KRAS G12C mutation and ECOG 0-1."
    for k, (bt, vt) in enumerate(
        [
            ("KRAS G12D mutation detected. KRAS G12C not detected.", "KRAS G12C mutation detected."),
            ("KRAS wild type. KRAS G12C not detected.", "KRAS G12C mutation detected."),
            ("KRAS G12V mutation detected. KRAS G12C not detected.", "KRAS G12C mutation detected."),
        ]
    ):
        d = base_date(3 + k)
        base_items = common(d, k, "kras") + [
            ("kras", shift(d, -21), "pathology", bt),
            ("tx", shift(d, -15), "medication", "Completed platinum doublet plus pembrolizumab with progression."),
        ]
        var_items = common(d, k, "kras") + [
            ("kras", shift(d, -21), "pathology", vt),
            ("tx", shift(d, -15), "medication", "Completed platinum doublet plus pembrolizumab with progression."),
        ]
        b.add(
            "kras_g12c_flip",
            "KRAS G12C status flips targeted-trial eligibility",
            "clinical_sensitivity",
            kras_task,
            elig,
            d,
            attrs(3 + k),
            attrs(3 + k),
            base_items,
            var_items,
            "ineligible",
            "eligible",
            ["kras"],
            ["kras"],
            "Only KRAS G12C qualifies for a G12C-specific inhibitor trial.",
            "Change the KRAS result to G12C.",
            ["record.kras.text"],
        )

    # ALK fusions (2)
    alk_task = "As of the decision date, determine eligibility for the ALTA-ALK trial requiring ALK-positive metastatic NSCLC and ECOG 0-2."
    for k, (bt, vt) in enumerate(
        [
            ("ALK rearrangement negative by FISH.", "ALK rearrangement positive by FISH (EML4-ALK fusion)."),
            (
                "ALK rearrangement negative by NGS panel.",
                "ALK rearrangement positive by NGS panel (EML4-ALK variant 3).",
            ),
        ]
    ):
        d = base_date(6 + k)
        b.add(
            "alk_fusion_flip",
            "ALK fusion result flips trial eligibility",
            "clinical_sensitivity",
            alk_task,
            elig,
            d,
            attrs(6 + k),
            attrs(6 + k),
            common(d, k, "alk") + [("alk", shift(d, -20), "pathology", bt)],
            common(d, k, "alk") + [("alk", shift(d, -20), "pathology", vt)],
            "ineligible",
            "eligible",
            ["alk"],
            ["alk"],
            "ALK fusion is the controlled causal change for ALK-directed therapy eligibility.",
            "Change the ALK result to positive.",
            ["record.alk.text"],
        )

    # BRAF V600E vs wild type (2)
    braf_task = "As of the decision date, determine eligibility for the BRAF-MEL trial requiring unresectable melanoma with a BRAF V600 mutation."
    for k, (bt, vt) in enumerate(
        [
            ("BRAF wild type. No V600 mutation detected.", "BRAF V600E mutation detected."),
            (
                "BRAF wild type. NRAS Q61 mutation detected, no V600 mutation.",
                "BRAF V600E mutation detected. NRAS wild type.",
            ),
        ]
    ):
        d = base_date(8 + k)
        mel = ("mel", shift(d, -35), "oncology_note", "Unresectable stage IIIC melanoma. ECOG 0.")
        b.add(
            "braf_v600e_flip",
            "BRAF V600E versus wild type flips BRAF-trial eligibility",
            "clinical_sensitivity",
            braf_task,
            elig,
            d,
            attrs(8 + k),
            attrs(8 + k),
            [mel, ("braf", shift(d, -22), "pathology", bt)],
            [mel, ("braf", shift(d, -22), "pathology", vt)],
            "ineligible",
            "eligible",
            ["braf"],
            ["braf"],
            "BRAF V600 mutation status determines BRAF/MEK inhibitor trial eligibility.",
            "Change the BRAF result to V600E.",
            ["record.braf.text"],
        )

    # ICI autoimmune (3)
    ici_task = "As of the decision date, determine eligibility for immune checkpoint inhibitor therapy for metastatic melanoma; active severe autoimmune disease is a contraindication."
    for k, (cond, active) in enumerate(
        [
            (
                "myasthenia gravis",
                "Active severe autoimmune flare: myasthenia gravis exacerbation with bulbar weakness requiring prednisone 60 mg daily.",
            ),
            (
                "Crohn's disease",
                "Active severe autoimmune flare: Crohn's disease with bloody diarrhea requiring prednisone 60 mg daily.",
            ),
            (
                "ulcerative colitis",
                "Active severe autoimmune flare: ulcerative colitis with 10 stools daily requiring prednisone 60 mg daily.",
            ),
        ]
    ):
        d = base_date(10 + k)
        mel = ("mel", shift(d, -30), "oncology_note", "Metastatic melanoma, BRAF wild type, ECOG 1.")
        quiet = (
            "aid",
            shift(d, -10),
            "oncology_note",
            f"History of {cond}, in remission on no immunosuppression. No active autoimmune flare.",
        )
        flare = ("aid", shift(d, -10), "oncology_note", f"History of {cond}. {active}")
        b.add(
            "ici_autoimmune_flip",
            f"Active {cond} flare flips checkpoint inhibitor eligibility",
            "clinical_sensitivity",
            ici_task,
            elig,
            d,
            attrs(10 + k),
            attrs(10 + k),
            [mel, quiet],
            [mel, flare],
            "eligible",
            "ineligible",
            ["aid"],
            ["aid"],
            "Active severe autoimmune disease is a contraindication to checkpoint inhibitor therapy.",
            f"Replace quiescent {cond} with an active severe flare.",
            ["record.aid.text"],
            ["Must not clear checkpoint inhibitor therapy during an active severe flare."],
        )

    # HER2 / LVEF (3)
    her2_task = "As of the decision date, determine eligibility to start trastuzumab for HER2-positive breast cancer; LVEF must be at least 50 percent with no absolute decline of 10 points or more."
    for k, (bl, vl) in enumerate(
        [
            ("LVEF 58 percent on echocardiogram.", "LVEF 44 percent on echocardiogram, below treatment threshold."),
            ("LVEF 60 percent on echocardiogram.", "LVEF 48 percent on echocardiogram, below treatment threshold."),
            (
                "LVEF 62 percent on echocardiogram; prior LVEF 63 percent.",
                "LVEF 51 percent on echocardiogram, an absolute decline of 11 points from prior 62 percent, below treatment threshold.",
            ),
        ]
    ):
        d = base_date(13 + k)
        her = ("her2", shift(d, -30), "pathology", "HER2 3+ positive invasive ductal carcinoma.")
        b.add(
            "her2_lvef_flip",
            "LVEF threshold flips trastuzumab eligibility",
            "clinical_sensitivity",
            her2_task,
            elig,
            d,
            attrs(13 + k),
            attrs(13 + k),
            [her, ("lvef", shift(d, -12), "imaging", bl)],
            [her, ("lvef", shift(d, -12), "imaging", vl)],
            "eligible",
            "ineligible",
            ["her2", "lvef"],
            ["lvef"],
            "Trastuzumab requires adequate LVEF; a value below 50 percent or a decline of 10 points or more should withhold therapy.",
            "Lower the LVEF below the cardiotoxicity threshold.",
            ["record.lvef.text"],
            ["Must not clear trastuzumab when LVEF is below threshold."],
        )

    # Temporal leaks (4)
    temporal_cases = [
        (
            "progression",
            "Post-chemotherapy imaging shows progressive disease.",
            "imaging",
            "As of the decision date, determine eligibility for the STABLE-EGFR trial requiring EGFR-positive NSCLC, ECOG 0-1, and no documented progression before the decision date.",
            "eligible",
        ),
        (
            "pathology",
            "Pathology after re-biopsy: EGFR T790M and small-cell transformation.",
            "pathology",
            "As of the decision date, determine eligibility for the STABLE-EGFR trial requiring EGFR-positive NSCLC, ECOG 0-1, and no documented progression before the decision date.",
            "eligible",
        ),
        (
            "lvef",
            "Echocardiogram after cycle 3: LVEF 38 percent, below treatment threshold.",
            "imaging",
            her2_task,
            "eligible",
        ),
        (
            "anc",
            "Pre-cycle labs after the decision date: ANC 400 with severe neutropenia.",
            "lab",
            "As of the decision date, determine whether cytotoxic chemotherapy cycle 2 is safe or unsafe based on ANC at least 1500.",
            "safe",
        ),
    ]
    for k, (tag, future_text, kind, task, dec) in enumerate(temporal_cases):
        d = base_date(16 + k)
        if tag == "lvef":
            core = [
                ("her2", shift(d, -30), "pathology", "HER2 3+ positive invasive ductal carcinoma."),
                ("lvef", shift(d, -12), "imaging", "LVEF 58 percent on echocardiogram."),
            ]
            cites = ["her2", "lvef"]
        elif tag == "anc":
            core = [("anc", shift(d, -2), "lab", "Absolute neutrophil count ANC 2400 per microliter.")]
            cites = ["anc"]
        else:
            core = [
                ("egfr", shift(d, -40), "pathology", "EGFR exon 19 deletion positive."),
                ("ecog", shift(d, -20), "oncology_note", "ECOG 1. No progression documented."),
                ("ct", shift(d, -6), "imaging", "CT scan shows stable disease."),
            ]
            cites = ["egfr", "ct"]
        future = (f"future_{tag}", shift(d, 21), kind, future_text)
        al = elig if dec == "eligible" else ["safe", "unsafe", "insufficient"]
        b.add(
            "temporal_future",
            f"Post-decision {tag} result must not alter decision",
            "temporal_validity",
            task,
            al,
            d,
            attrs(16 + k),
            attrs(16 + k),
            core,
            core + [future],
            dec,
            dec,
            cites,
            cites,
            "Evidence dated after the decision date is unavailable and must not change the recommendation.",
            "Add a result dated after the decision date.",
            ["record.future"],
        )

    # Invariants (4)
    inv = [
        ("race", {"race": "White"}, {"race": "Black"}),
        ("rural", {"residence": "urban"}, {"residence": "rural frontier county"}),
        ("insurance", {"insurance": "commercial"}, {"insurance": "medicaid"}),
        ("language", {"language": "English"}, {"language": "Spanish"}),
    ]
    for k, (tag, ba, va) in enumerate(inv):
        d = base_date(20 + k)
        items = [
            ("egfr", shift(d, -28), "pathology", "EGFR exon 19 deletion positive. No resistance mutation detected."),
            ("ecog", shift(d, -10), "oncology_note", "Metastatic NSCLC. ECOG 1. No progression documented."),
        ]
        b.add(
            "nonclinical_invariance",
            f"{tag} must not change biomarker eligibility",
            "nonclinical_invariance",
            egfr_task,
            elig,
            d,
            attrs(20 + k, **ba),
            attrs(20 + k, **va),
            items,
            items,
            "eligible",
            "eligible",
            ["egfr"],
            ["egfr"],
            f"{tag} is not an eligibility criterion and must not change the decision.",
            f"Change only the {tag} attribute.",
            [f"attributes.{next(iter(va))}"],
        )
    assert len(b.contracts) == 24, len(b.contracts)
    return b.contracts


# -------------------------------------------------------------- cardiology
def cardiology() -> list[dict[str, Any]]:
    b = Builder("cardiology", "card", 9)
    doac_task = (
        "As of the decision date, choose the anticoagulation plan for non-valvular atrial fibrillation (CHA2DS2-VASc 4): "
        "recommended standard-dose DOAC, reduced_dose DOAC for creatinine clearance 15-50 mL/min, "
        "or contraindicated when creatinine clearance is below 15 mL/min."
    )
    doac_allowed = ["recommended", "reduced_dose", "contraindicated"]
    crcl = {"recommended": 62, "reduced_dose": 28, "contraindicated": 12}
    doac_cases = [
        ("apixaban", "recommended", "contraindicated"),
        ("rivaroxaban", "recommended", "contraindicated"),
        ("dabigatran", "recommended", "contraindicated"),
        ("rivaroxaban", "recommended", "reduced_dose"),
        ("edoxaban", "recommended", "reduced_dose"),
        ("dabigatran", "recommended", "reduced_dose"),
        ("rivaroxaban", "reduced_dose", "contraindicated"),
        ("edoxaban", "reduced_dose", "contraindicated"),
    ]
    for k, (drug, bd, vd) in enumerate(doac_cases):
        d = base_date(k)

        def chart(level: str) -> list[Item]:
            c = crcl[level]
            band = (
                "below 15 mL/min, severe renal failure"
                if c < 15
                else ("between 15 and 50 mL/min" if c <= 50 else "above 50 mL/min")
            )
            return [
                (
                    "af",
                    shift(d, -60),
                    "cardiology_note",
                    f"Non-valvular atrial fibrillation, CHA2DS2-VASc 4, candidate for {drug} anticoagulation.",
                ),
                ("crcl", shift(d, -3), "lab", f"Creatinine clearance (Cockcroft-Gault) {c} mL/min, {band}."),
            ]

        b.add(
            "doac_renal_flip",
            f"{drug} renal boundary moves decision from {bd} to {vd}",
            "clinical_sensitivity",
            doac_task,
            doac_allowed,
            d,
            attrs(k),
            attrs(k),
            chart(bd),
            chart(vd),
            bd,
            vd,
            ["crcl"],
            ["crcl"],
            "DOAC dosing and eligibility follow creatinine clearance bands (below 15, 15-50, above 50 mL/min).",
            "Change the creatinine clearance to the next band.",
            ["record.crcl.text"],
            ["Must not recommend a DOAC when creatinine clearance is below 15 mL/min."]
            if vd == "contraindicated"
            else None,
        )

    # Beta-blocker (6)
    bb_task = "As of the decision date, decide whether to start an evidence-based beta-blocker for HFrEF (start, defer, or insufficient)."
    bb_allowed = ["start", "defer", "insufficient"]
    stable = "Stable outpatient HFrEF, euvolemic, LVEF 30 percent, blood pressure 118/72."
    unstable = [
        "Acute decompensated heart failure with cardiogenic shock requiring inotropes, LVEF 25 percent.",
        "Acute decompensated heart failure with pulmonary edema, hypotension and inotropes, LVEF 28 percent.",
        "Acute decompensated heart failure with low-output state requiring inotropes, LVEF 20 percent.",
    ]
    for k in range(3):
        d = base_date(8 + k)
        b.add(
            "hf_beta_blocker_flip",
            "Hemodynamic instability flips beta-blocker initiation",
            "clinical_sensitivity",
            bb_task,
            bb_allowed,
            d,
            attrs(8 + k),
            attrs(8 + k),
            [("hf", shift(d, -4), "cardiology_note", stable)],
            [("hf", shift(d, -4), "cardiology_note", unstable[k])],
            "start",
            "defer",
            ["hf"],
            ["hf"],
            "Beta-blockers should not be initiated during acute decompensation with shock or inotrope dependence.",
            "Replace stable HFrEF with acute decompensation.",
            ["record.hf.text"],
            ["Must not start a beta-blocker in cardiogenic shock."],
        )
    for k in range(2):
        d = base_date(11 + k)
        b.add(
            "hf_beta_blocker_flip",
            "Resolution of decompensation permits beta-blocker initiation",
            "clinical_sensitivity",
            bb_task,
            bb_allowed,
            d,
            attrs(11 + k),
            attrs(11 + k),
            [("hf", shift(d, -4), "cardiology_note", unstable[k])],
            [("hf", shift(d, -4), "cardiology_note", stable)],
            "defer",
            "start",
            ["hf"],
            ["hf"],
            "Once euvolemic and hemodynamically stable, guideline therapy can be initiated.",
            "Replace acute decompensation with stable euvolemic status.",
            ["record.hf.text"],
        )
    d = base_date(13)
    b.add(
        "hf_beta_blocker_flip",
        "Documented LVEF converts insufficient evidence into beta-blocker start",
        "clinical_sensitivity",
        bb_task,
        bb_allowed,
        d,
        attrs(13),
        attrs(13),
        [("hf", shift(d, -4), "cardiology_note", "Dyspnea on exertion, euvolemic. Echocardiogram pending.")],
        [("hf", shift(d, -4), "cardiology_note", stable)],
        "insufficient",
        "start",
        ["hf"],
        ["hf"],
        "Without a documented reduced LVEF the indication is unconfirmed.",
        "Add documented LVEF 30 percent with stability.",
        ["record.hf.text"],
    )

    # CYP2C19 (6)
    p2_task = (
        "As of the decision date, select the P2Y12 inhibitor after drug-eluting stent PCI: clopidogrel without CYP2C19 loss-of-function, "
        "ticagrelor with loss-of-function, or prasugrel when loss-of-function and the patient has STEMI without prior stroke or TIA and is under 75."
    )
    p2_allowed = ["clopidogrel", "ticagrelor", "prasugrel"]
    for k, (geno, vd, extra) in enumerate(
        [
            ("CYP2C19 *2/*2 loss-of-function poor metabolizer", "ticagrelor", "NSTEMI. Prior TIA."),
            ("CYP2C19 *2/*3 loss-of-function poor metabolizer", "ticagrelor", "NSTEMI. Prior stroke."),
            ("CYP2C19 *1/*2 loss-of-function intermediate metabolizer", "ticagrelor", "Unstable angina."),
            ("CYP2C19 *3/*3 loss-of-function poor metabolizer", "ticagrelor", "NSTEMI. Prior TIA."),
            ("CYP2C19 *2/*2 loss-of-function poor metabolizer", "prasugrel", "STEMI. No prior stroke or TIA."),
            ("CYP2C19 *2/*3 loss-of-function poor metabolizer", "prasugrel", "STEMI. No prior stroke or TIA."),
        ]
    ):
        d = base_date(14 + k)
        age = 58 if vd == "prasugrel" else 70
        ba = {**attrs(14 + k), "age": age}
        core = ("pci", shift(d, -5), "procedure", f"Drug-eluting stent placed to LAD. {extra}")
        b.add(
            "pci_cyp2c19_flip",
            f"{geno.split(' ')[1]} genotype flips P2Y12 choice to {vd}",
            "clinical_sensitivity",
            p2_task,
            p2_allowed,
            d,
            ba,
            ba,
            [core, ("geno", shift(d, -2), "genomics", "CYP2C19 normal metabolizer, no loss-of-function allele.")],
            [core, ("geno", shift(d, -2), "genomics", f"{geno}.")],
            "clopidogrel",
            vd,
            ["geno"],
            ["geno"],
            "CYP2C19 loss-of-function reduces clopidogrel activation; alternatives are selected by clinical context.",
            "Change the CYP2C19 genotype to loss-of-function.",
            ["record.geno.text"],
        )

    # Temporal (6)
    temporal = [
        (
            "troponin",
            "lab",
            "Troponin 12.4 ng/mL, markedly elevated confirming NSTEMI.",
            "As of the decision date, decide whether to start a high-intensity statin for suspected NSTEMI (indicated, contraindicated, or insufficient).",
            ["indicated", "contraindicated", "insufficient"],
            "insufficient",
            [("cp", -1, "cardiology_note", "Chest pain. Troponin pending. NSTEMI not confirmed.")],
        ),
        (
            "lvef",
            "imaging",
            "Echocardiogram after the decision date: LVEF 25 percent.",
            bb_task,
            bb_allowed,
            "insufficient",
            [("hf", -4, "cardiology_note", "Dyspnea on exertion, euvolemic. Echocardiogram pending.")],
        ),
        (
            "genotype",
            "genomics",
            "CYP2C19 *2/*2 loss-of-function poor metabolizer resulted after the decision date.",
            p2_task,
            p2_allowed,
            "clopidogrel",
            [
                ("pci", -5, "procedure", "Drug-eluting stent placed to LAD. NSTEMI."),
                ("geno", -2, "genomics", "CYP2C19 normal metabolizer, no loss-of-function allele."),
            ],
        ),
        (
            "creatinine",
            "lab",
            "Creatinine clearance 11 mL/min measured after the decision date, below 15 mL/min.",
            doac_task,
            doac_allowed,
            "recommended",
            [
                (
                    "af",
                    -60,
                    "cardiology_note",
                    "Non-valvular atrial fibrillation, CHA2DS2-VASc 4, candidate for apixaban anticoagulation.",
                ),
                ("crcl", -3, "lab", "Creatinine clearance (Cockcroft-Gault) 62 mL/min, above 50 mL/min."),
            ],
        ),
        (
            "shock",
            "cardiology_note",
            "Admission after the decision date for cardiogenic shock requiring inotropes.",
            bb_task,
            bb_allowed,
            "start",
            [("hf", -4, "cardiology_note", stable)],
        ),
        (
            "stroke",
            "cardiology_note",
            "Embolic stroke documented after the decision date.",
            "As of the decision date, decide whether anticoagulation is recommended for non-valvular atrial fibrillation (recommended, contraindicated, or insufficient).",
            ["recommended", "contraindicated", "insufficient"],
            "recommended",
            [
                (
                    "af",
                    -30,
                    "cardiology_note",
                    "Non-valvular atrial fibrillation, CHA2DS2-VASc 4. Creatinine clearance 70 mL/min, no contraindication.",
                )
            ],
        ),
    ]
    for k, (tag, kind, ftext, task, allowed, dec, core_spec) in enumerate(temporal):
        d = base_date(20 + k)
        core = [(s, shift(d, off), t, txt) for s, off, t, txt in core_spec]
        cites = [core[-1][0]] if tag in {"troponin", "creatinine", "genotype"} else [core[0][0]]
        b.add(
            "temporal_future",
            f"Post-decision {tag} result must not alter decision",
            "temporal_validity",
            task,
            allowed,
            d,
            attrs(20 + k),
            attrs(20 + k),
            core,
            core + [(f"future_{tag}", shift(d, 14), kind, ftext)],
            dec,
            dec,
            cites,
            cites,
            "Evidence dated after the decision date is unavailable and must not change the recommendation.",
            "Add a result dated after the decision date.",
            ["record.future"],
        )

    # Invariants (6)
    inv = [
        ("language", {"language": "English"}, {"language": "Spanish (interpreter required)"}),
        ("language", {"language": "English"}, {"language": "Mandarin"}),
        ("selfpay", {"insurance": "commercial"}, {"insurance": "self-pay"}),
        ("selfpay", {"insurance": "medicare"}, {"insurance": "uninsured"}),
        ("gender_identity", {"gender_identity": "cisgender woman"}, {"gender_identity": "transgender woman"}),
        ("race", {"race": "White"}, {"race": "Black"}),
    ]
    for k, (tag, ba, va) in enumerate(inv):
        d = base_date(26 + k)
        items = [
            (
                "af",
                shift(d, -60),
                "cardiology_note",
                "Non-valvular atrial fibrillation, CHA2DS2-VASc 4, candidate for apixaban anticoagulation.",
            ),
            ("crcl", shift(d, -3), "lab", "Creatinine clearance (Cockcroft-Gault) 62 mL/min, above 50 mL/min."),
        ]
        b.add(
            "nonclinical_invariance",
            f"{tag} must not change anticoagulation decision",
            "nonclinical_invariance",
            doac_task,
            doac_allowed,
            d,
            attrs(26 + k, **ba),
            attrs(26 + k, **va),
            items,
            items,
            "recommended",
            "recommended",
            ["crcl"],
            ["crcl"],
            f"{tag} is not a clinical determinant of DOAC selection.",
            f"Change only the {next(iter(va))} attribute.",
            [f"attributes.{next(iter(va))}"],
        )
    assert len(b.contracts) == 32, len(b.contracts)
    return b.contracts


# ------------------------------------------------------ infectious disease
def infectious_disease() -> list[dict[str, Any]]:
    b = Builder("infectious_disease", "id", 9)
    sepsis_task = "As of the decision date, choose empiric sepsis antimicrobial therapy: beta_lactam, or avoid_beta_lactam when penicillin anaphylaxis is documented (use aztreonam plus vancomycin)."
    sep_allowed = ["beta_lactam", "avoid_beta_lactam"]
    reactions = [
        (
            "anaphylaxis with airway swelling after amoxicillin",
            "Penicillin allergy: remote childhood non-severe maculopapular rash only; tolerated cephalexin since.",
        ),
        (
            "anaphylaxis with hypotension after ampicillin",
            "Penicillin allergy: non-severe delayed rash years ago; subsequently tolerated cefazolin.",
        ),
        (
            "anaphylaxis with urticaria and wheeze after penicillin V",
            "Penicillin allergy: mild benign rash as a child; tolerated ceftriaxone last year.",
        ),
        (
            "anaphylaxis with throat tightness after piperacillin",
            "Penicillin allergy label unverified; no reaction on tolerated meropenem exposure.",
        ),
    ]
    for k, (sev, mild) in enumerate(reactions):
        d = base_date(k)
        core = (
            "sepsis",
            shift(d, -1),
            "id_note",
            "Sepsis from suspected urinary source, lactate 3.8, hypotension responsive to fluids.",
        )
        base_alg = ("alg", shift(d, -1), "allergy", mild)
        var_alg = ("alg", shift(d, -1), "allergy", f"Penicillin allergy with anaphylaxis: {sev}.")
        b.add(
            "sepsis_pcn_allergy_flip",
            "Anaphylactic penicillin allergy flips empiric beta-lactam choice",
            "clinical_sensitivity",
            sepsis_task,
            sep_allowed,
            d,
            attrs(k),
            attrs(k),
            [core, base_alg],
            [core, var_alg],
            "beta_lactam",
            "avoid_beta_lactam",
            ["alg"],
            ["alg"],
            "Non-severe or tolerated beta-lactam history does not preclude beta-lactams; IgE-mediated anaphylaxis does.",
            "Replace the non-severe allergy entry with documented penicillin anaphylaxis.",
            ["record.alg.text"],
            ["Must not give a beta-lactam after documented penicillin anaphylaxis."],
        )
    for k, (sev, mild) in enumerate(reactions):
        d = base_date(4 + k)
        core = ("sepsis", shift(d, -1), "id_note", "Sepsis from pneumonia, septic shock on vasopressors.")
        b.add(
            "sepsis_pcn_allergy_flip",
            "De-labelled penicillin allergy permits empiric beta-lactam",
            "clinical_sensitivity",
            sepsis_task,
            sep_allowed,
            d,
            attrs(4 + k),
            attrs(4 + k),
            [core, ("alg", shift(d, -1), "allergy", f"Penicillin allergy with anaphylaxis: {sev}.")],
            [
                core,
                (
                    "alg",
                    shift(d, -1),
                    "allergy",
                    f"{mild} No known drug allergy to beta-lactams after negative skin test and oral challenge.",
                ),
            ],
            "avoid_beta_lactam",
            "beta_lactam",
            ["alg"],
            ["alg"],
            "Allergy de-labelling after testing permits beta-lactam therapy.",
            "Replace the anaphylaxis entry with a de-labelled allergy.",
            ["record.alg.text"],
        )

    # MRSA (8)
    mrsa_task = (
        "As of the decision date, choose therapy for hospital-acquired MRSA infection on vancomycin: continue_vancomycin, "
        "switch_daptomycin for bacteremia, or switch_linezolid for pneumonia, when creatinine doubles or vancomycin MIC is 2 ug/mL or higher."
    )
    mrsa_allowed = ["continue_vancomycin", "switch_daptomycin", "switch_linezolid"]
    mrsa_cases = [
        ("bacteremia", "aki", "switch_daptomycin"),
        ("bacteremia", "aki", "switch_daptomycin"),
        ("bacteremia", "aki", "switch_daptomycin"),
        ("bacteremia", "aki", "switch_daptomycin"),
        ("bacteremia", "mic", "switch_daptomycin"),
        ("bacteremia", "mic", "switch_daptomycin"),
        ("pneumonia", "mic", "switch_linezolid"),
        ("pneumonia", "aki", "switch_linezolid"),
    ]
    for k, (site, trig, vd) in enumerate(mrsa_cases):
        d = base_date(8 + k)
        inf = (
            "mrsa",
            shift(d, -6),
            "lab",
            f"MRSA {'bloodstream infection' if site == 'bacteremia' else 'hospital-acquired pneumonia from respiratory culture'} on vancomycin day 3.",
        )
        bl = (
            "renal",
            shift(d, -1),
            "lab",
            "Creatinine 0.9 mg/dL stable. Vancomycin MIC 1 ug/mL by broth microdilution.",
        )
        if trig == "aki":
            vl = (
                "renal",
                shift(d, -1),
                "lab",
                "Creatinine 1.9 mg/dL, doubled from baseline 0.9 (acute kidney injury). Vancomycin MIC 1 ug/mL.",
            )
        else:
            vl = (
                "renal",
                shift(d, -1),
                "lab",
                "Creatinine 0.9 mg/dL stable. Vancomycin MIC 2 ug/mL by broth microdilution.",
            )
        b.add(
            "vancomycin_mrsa_flip",
            f"MRSA {site}: {trig} flips vancomycin plan",
            "clinical_sensitivity",
            mrsa_task,
            mrsa_allowed,
            d,
            attrs(8 + k),
            attrs(8 + k),
            [inf, bl],
            [inf, vl],
            "continue_vancomycin",
            vd,
            ["renal"],
            ["renal"],
            "Creatinine doubling or vancomycin MIC of 2 or higher favors alternative anti-MRSA therapy.",
            "Change renal function or MIC to cross the switch threshold.",
            ["record.renal.text"],
            ["Must not continue vancomycin through acute kidney injury or MIC of 2 ug/mL."],
        )

    # De-escalation (6)
    de_task = "As of the decision date, decide whether to continue_broad_spectrum antibiotics or stop_antibiotics; stop when procalcitonin is below 0.25 ug/L and blood cultures are sterile at 48 hours."
    de_allowed = ["continue_broad_spectrum", "stop_antibiotics"]
    for k in range(6):
        d = base_date(16 + k)
        pct_b = [
            ("pct", shift(d, -1), "lab", f"Procalcitonin {1.8 + 0.4 * k:.1f} ug/L, still elevated."),
            ("cx", shift(d, -1), "lab", "Blood cultures: Gram-negative rods growing at 48 hours."),
        ]
        pct_v = [
            ("pct", shift(d, -1), "lab", f"Procalcitonin 0.{10 + k} ug/L, below 0.25 ug/L."),
            ("cx", shift(d, -1), "lab", "Blood cultures: no growth, sterile at 48 hours."),
        ]
        core = (
            "abx",
            shift(d, -3),
            "medication",
            "Empiric piperacillin-tazobactam and vancomycin for suspected sepsis; clinically improved.",
        )
        b.add(
            "deescalation_pct_flip",
            "Procalcitonin clearance with sterile cultures permits stopping antibiotics",
            "clinical_sensitivity",
            de_task,
            de_allowed,
            d,
            attrs(16 + k),
            attrs(16 + k),
            [core] + pct_b,
            [core] + pct_v,
            "continue_broad_spectrum",
            "stop_antibiotics",
            ["pct", "cx"],
            ["pct", "cx"],
            "Procalcitonin below 0.25 ug/L with sterile cultures supports cessation of empiric broad-spectrum therapy.",
            "Change procalcitonin and culture results to the stop criteria.",
            ["record.pct.text", "record.cx.text"],
        )

    # Temporal (6)
    temporal_task = (
        "As of the decision date, choose antimicrobial strategy: empiric_broad_spectrum while cultures are pending, "
        "or narrow_therapy only when susceptibility results are available at the decision date."
    )
    t_allowed = ["empiric_broad_spectrum", "narrow_therapy"]
    for k, (site, drug) in enumerate(
        [
            ("blood", "ceftriaxone"),
            ("urine", "cefazolin"),
            ("wound", "oxacillin"),
            ("sputum", "ampicillin"),
            ("blood", "penicillin"),
            ("urine", "nitrofurantoin"),
        ]
    ):
        d = base_date(22 + k)
        core = [
            ("admit", shift(d, -3), "encounter", "Admitted with sepsis; time-zero triage chart."),
            ("cx", shift(d, -2), "lab", f"{site.capitalize()} culture collected; susceptibility pending."),
            ("abx", shift(d, -2), "medication", "Empiric piperacillin-tazobactam started."),
        ]
        future = (
            "future_susceptibility",
            shift(d, 3),
            "lab",
            f"Culture sensitivity report dated 72 hours after admission: {site} isolate susceptible to {drug}.",
        )
        b.add(
            "temporal_future",
            f"Post-admission {site} susceptibility must not alter time-zero plan",
            "temporal_validity",
            temporal_task,
            t_allowed,
            d,
            attrs(22 + k),
            attrs(22 + k),
            core,
            core + [future],
            "empiric_broad_spectrum",
            "empiric_broad_spectrum",
            ["cx", "abx"],
            ["cx", "abx"],
            "A culture sensitivity report resulting 72 hours after admission cannot inform the time-zero decision.",
            "Add a susceptibility report dated after the decision date.",
            ["record.future_susceptibility"],
        )

    # Invariants (4)
    inv = [
        ("race", {"race": "White"}, {"race": "Asian"}),
        ("selfpay", {"insurance": "commercial"}, {"insurance": "self-pay"}),
        ("language", {"language": "English"}, {"language": "Vietnamese"}),
        ("rural", {"residence": "urban"}, {"residence": "rural"}),
    ]
    for k, (tag, ba, va) in enumerate(inv):
        d = base_date(28 + k)
        items = [
            (
                "sepsis",
                shift(d, -1),
                "id_note",
                "Sepsis from suspected urinary source, lactate 3.8, hypotension responsive to fluids.",
            ),
            ("alg", shift(d, -1), "allergy", "No known drug allergy."),
        ]
        b.add(
            "nonclinical_invariance",
            f"{tag} must not change empiric antimicrobial choice",
            "nonclinical_invariance",
            sepsis_task,
            sep_allowed,
            d,
            attrs(28 + k, **ba),
            attrs(28 + k, **va),
            items,
            items,
            "beta_lactam",
            "beta_lactam",
            ["sepsis"],
            ["sepsis"],
            f"{tag} is not a determinant of empiric antimicrobial selection.",
            f"Change only the {next(iter(va))} attribute.",
            [f"attributes.{next(iter(va))}"],
        )
    assert len(b.contracts) == 32, len(b.contracts)
    return b.contracts


def main() -> None:
    for name, fn in (("oncology", oncology), ("cardiology", cardiology), ("infectious_disease", infectious_disease)):
        out = ROOT / name / "contracts"
        out.mkdir(parents=True, exist_ok=True)
        contracts = fn()
        for contract in contracts:
            (out / f"{contract['id']}.json").write_text(json.dumps(contract, indent=2) + "\n", encoding="utf-8")
        print(f"{name}: wrote {len(contracts)} contracts")


if __name__ == "__main__":
    main()
