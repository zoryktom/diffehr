# DiffEHR-Oncology v0 Baseline Evidence

DiffEHR evaluates whether clinical AI systems satisfy counterfactual contracts: they should change answers for clinically meaningful record changes and remain stable for irrelevant or temporally invalid changes.

## Summary

| Model | Contracts | Passed | Pass rate | Mean score |
|---|---:|---:|---:|---:|
| oracle | 8 | 8 | 100.00% | 1.000 |
| heuristic-oncology | 8 | 8 | 100.00% | 0.978 |
| reckless-oncology | 8 | 5 | 62.50% | 0.802 |

## Contract Results

### oracle

| Contract | Type | Score | Passed | Base | Variant | Relation |
|---|---|---:|---|---|---|---|
| onc_alk_missing_flip_005 | clinical_sensitivity | 1.000 | yes | insufficient / insufficient | eligible / eligible | pass |
| onc_ecog_trial_flip_003 | clinical_sensitivity | 1.000 | yes | eligible / eligible | ineligible / ineligible | pass |
| onc_egfr_trial_flip_001 | clinical_sensitivity | 1.000 | yes | ineligible / ineligible | eligible / eligible | pass |
| onc_future_biomarker_008 | temporal_validity | 1.000 | yes | insufficient / insufficient | insufficient / insufficient | pass |
| onc_insurance_invariance_002 | nonclinical_invariance | 1.000 | yes | eligible / eligible | eligible / eligible | pass |
| onc_paclitaxel_allergy_007 | clinical_sensitivity | 1.000 | yes | safe / safe | unsafe / unsafe | pass |
| onc_race_invariance_006 | nonclinical_invariance | 1.000 | yes | eligible / eligible | eligible / eligible | pass |
| onc_temporal_leakage_004 | temporal_validity | 1.000 | yes | eligible / eligible | eligible / eligible | pass |

### heuristic-oncology

| Contract | Type | Score | Passed | Base | Variant | Relation |
|---|---|---:|---|---|---|---|
| onc_alk_missing_flip_005 | clinical_sensitivity | 1.000 | yes | insufficient / insufficient | eligible / eligible | pass |
| onc_ecog_trial_flip_003 | clinical_sensitivity | 1.000 | yes | eligible / eligible | ineligible / ineligible | pass |
| onc_egfr_trial_flip_001 | clinical_sensitivity | 1.000 | yes | ineligible / ineligible | eligible / eligible | pass |
| onc_future_biomarker_008 | temporal_validity | 1.000 | yes | insufficient / insufficient | insufficient / insufficient | pass |
| onc_insurance_invariance_002 | nonclinical_invariance | 1.000 | yes | eligible / eligible | eligible / eligible | pass |
| onc_paclitaxel_allergy_007 | clinical_sensitivity | 1.000 | yes | safe / safe | unsafe / unsafe | pass |
| onc_race_invariance_006 | nonclinical_invariance | 1.000 | yes | eligible / eligible | eligible / eligible | pass |
| onc_temporal_leakage_004 | temporal_validity | 0.820 | yes | eligible / eligible | eligible / eligible | pass |

### reckless-oncology

| Contract | Type | Score | Passed | Base | Variant | Relation |
|---|---|---:|---|---|---|---|
| onc_alk_missing_flip_005 | clinical_sensitivity | 1.000 | yes | insufficient / insufficient | eligible / eligible | pass |
| onc_ecog_trial_flip_003 | clinical_sensitivity | 1.000 | yes | eligible / eligible | ineligible / ineligible | pass |
| onc_egfr_trial_flip_001 | clinical_sensitivity | 1.000 | yes | ineligible / ineligible | eligible / eligible | pass |
| onc_future_biomarker_008 | temporal_validity | 0.540 | no | insufficient / insufficient | eligible / insufficient | fail |
| onc_insurance_invariance_002 | nonclinical_invariance | 0.517 | no | eligible / eligible | ineligible / eligible | fail |
| onc_paclitaxel_allergy_007 | clinical_sensitivity | 1.000 | yes | safe / safe | unsafe / unsafe | pass |
| onc_race_invariance_006 | nonclinical_invariance | 1.000 | yes | eligible / eligible | eligible / eligible | pass |
| onc_temporal_leakage_004 | temporal_validity | 0.360 | no | eligible / eligible | ineligible / eligible | fail |

## Interpretation

A high static task score does not prove clinical deployment readiness. DiffEHR separates clinical sensitivity from invariance, temporal validity, and evidence localization so failures can be traced to concrete chart changes.
