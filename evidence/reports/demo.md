# DiffEHR Oncology Demo Report

DiffEHR evaluates whether clinical AI systems satisfy counterfactual contracts: they should change answers for clinically meaningful record changes and remain stable for irrelevant or temporally invalid changes.

## Summary

| Model | Contracts | Passed | Pass rate | Mean score |
|---|---:|---:|---:|---:|
| oracle | 8 | 8 | 100.00% | 1.000 |
| heuristic-oncology | 8 | 8 | 100.00% | 1.000 |
| reckless-oncology | 8 | 5 | 62.50% | 0.815 |

## Research Metrics

| Model | IVR | DSS | Evidence precision | Evidence recall | Temporal leakage |
|---|---:|---:|---:|---:|---:|
| oracle | 0.00% | 100.00% | 100.00% | 100.00% | 0 |
| heuristic-oncology | 0.00% | 100.00% | 100.00% | 100.00% | 0 |
| reckless-oncology | 75.00% | 100.00% | 83.33% | 83.33% | 2 |

## Failure Modes

| Model | Domain | Contract type | Failed | Total |
|---|---|---|---:|---:|
| oracle | oncology | clinical_sensitivity | 0 | 4 |
| oracle | oncology | nonclinical_invariance | 0 | 2 |
| oracle | oncology | temporal_validity | 0 | 2 |
| heuristic-oncology | oncology | clinical_sensitivity | 0 | 4 |
| heuristic-oncology | oncology | nonclinical_invariance | 0 | 2 |
| heuristic-oncology | oncology | temporal_validity | 0 | 2 |
| reckless-oncology | oncology | clinical_sensitivity | 0 | 4 |
| reckless-oncology | oncology | nonclinical_invariance | 1 | 2 |
| reckless-oncology | oncology | temporal_validity | 2 | 2 |

## Contract Results

### oracle

| Contract | Domain | Type | Score | Passed | Base | Variant | Relation |
|---|---|---|---:|---|---|---|---|
| onc_alk_missing_flip_005 | oncology | clinical_sensitivity | 1.000 | yes | insufficient / insufficient | eligible / eligible | pass |
| onc_ecog_trial_flip_003 | oncology | clinical_sensitivity | 1.000 | yes | eligible / eligible | ineligible / ineligible | pass |
| onc_egfr_trial_flip_001 | oncology | clinical_sensitivity | 1.000 | yes | ineligible / ineligible | eligible / eligible | pass |
| onc_future_biomarker_008 | oncology | temporal_validity | 1.000 | yes | insufficient / insufficient | insufficient / insufficient | pass |
| onc_insurance_invariance_002 | oncology | nonclinical_invariance | 1.000 | yes | eligible / eligible | eligible / eligible | pass |
| onc_paclitaxel_allergy_007 | oncology | clinical_sensitivity | 1.000 | yes | safe / safe | unsafe / unsafe | pass |
| onc_race_invariance_006 | oncology | nonclinical_invariance | 1.000 | yes | eligible / eligible | eligible / eligible | pass |
| onc_temporal_leakage_004 | oncology | temporal_validity | 1.000 | yes | eligible / eligible | eligible / eligible | pass |

### heuristic-oncology

| Contract | Domain | Type | Score | Passed | Base | Variant | Relation |
|---|---|---|---:|---|---|---|---|
| onc_alk_missing_flip_005 | oncology | clinical_sensitivity | 1.000 | yes | insufficient / insufficient | eligible / eligible | pass |
| onc_ecog_trial_flip_003 | oncology | clinical_sensitivity | 1.000 | yes | eligible / eligible | ineligible / ineligible | pass |
| onc_egfr_trial_flip_001 | oncology | clinical_sensitivity | 1.000 | yes | ineligible / ineligible | eligible / eligible | pass |
| onc_future_biomarker_008 | oncology | temporal_validity | 1.000 | yes | insufficient / insufficient | insufficient / insufficient | pass |
| onc_insurance_invariance_002 | oncology | nonclinical_invariance | 1.000 | yes | eligible / eligible | eligible / eligible | pass |
| onc_paclitaxel_allergy_007 | oncology | clinical_sensitivity | 1.000 | yes | safe / safe | unsafe / unsafe | pass |
| onc_race_invariance_006 | oncology | nonclinical_invariance | 1.000 | yes | eligible / eligible | eligible / eligible | pass |
| onc_temporal_leakage_004 | oncology | temporal_validity | 1.000 | yes | eligible / eligible | eligible / eligible | pass |

### reckless-oncology

| Contract | Domain | Type | Score | Passed | Base | Variant | Relation |
|---|---|---|---:|---|---|---|---|
| onc_alk_missing_flip_005 | oncology | clinical_sensitivity | 1.000 | yes | insufficient / insufficient | eligible / eligible | pass |
| onc_ecog_trial_flip_003 | oncology | clinical_sensitivity | 1.000 | yes | eligible / eligible | ineligible / ineligible | pass |
| onc_egfr_trial_flip_001 | oncology | clinical_sensitivity | 1.000 | yes | ineligible / ineligible | eligible / eligible | pass |
| onc_future_biomarker_008 | oncology | temporal_validity | 0.574 | no | insufficient / insufficient | eligible / insufficient | fail |
| onc_insurance_invariance_002 | oncology | nonclinical_invariance | 0.495 | no | eligible / eligible | ineligible / eligible | fail |
| onc_paclitaxel_allergy_007 | oncology | clinical_sensitivity | 1.000 | yes | safe / safe | unsafe / unsafe | pass |
| onc_race_invariance_006 | oncology | nonclinical_invariance | 1.000 | yes | eligible / eligible | eligible / eligible | pass |
| onc_temporal_leakage_004 | oncology | temporal_validity | 0.450 | no | eligible / eligible | ineligible / eligible | fail |

## Interpretation

A high static task score does not prove clinical deployment readiness. DiffEHR separates clinical sensitivity from invariance, temporal validity, and evidence localization so failures can be traced to concrete chart changes.
