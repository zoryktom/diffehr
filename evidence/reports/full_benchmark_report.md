# DiffEHR Multi-Specialty Benchmark Report

DiffEHR evaluates whether clinical AI systems satisfy counterfactual contracts: they should change answers for clinically meaningful record changes and remain stable for irrelevant or temporally invalid changes.

## Summary

| Model | Contracts | Passed | Pass rate | Mean score |
|---|---:|---:|---:|---:|
| oracle | 32 | 32 | 100.00% | 1.000 |
| heuristic-oncology | 32 | 32 | 100.00% | 0.999 |
| reckless-oncology | 32 | 24 | 75.00% | 0.877 |

## Research Metrics

| Model | IVR | IVR 95% CI | DSS | DSS 95% CI | Evidence precision | Evidence recall | Temporal leakage |
|---|---:|---:|---:|---:|---:|---:|---:|
| oracle | 0.00% | 0.00%-0.00% | 100.00% | 100.00%-100.00% | 100.00% | 100.00% | 0 |
| heuristic-oncology | 0.00% | 0.00%-0.00% | 100.00% | 100.00%-100.00% | 98.88% | 100.00% | 0 |
| reckless-oncology | 50.00% | 25.00%-75.00% | 100.00% | 100.00%-100.00% | 88.76% | 89.77% | 5 |

## Specialty Summary

| Model | Specialty | Category | Passed | Total | Pass rate |
|---|---|---|---:|---:|---:|
| oracle | cardiology | clinical_sensitivity | 4 | 4 | 100.00% |
| oracle | cardiology | nonclinical_invariance | 3 | 3 | 100.00% |
| oracle | cardiology | temporal_validity | 1 | 1 | 100.00% |
| oracle | infectious_disease | clinical_sensitivity | 4 | 4 | 100.00% |
| oracle | infectious_disease | nonclinical_invariance | 2 | 2 | 100.00% |
| oracle | infectious_disease | temporal_validity | 2 | 2 | 100.00% |
| oracle | oncology | clinical_sensitivity | 8 | 8 | 100.00% |
| oracle | oncology | nonclinical_invariance | 4 | 4 | 100.00% |
| oracle | oncology | temporal_validity | 4 | 4 | 100.00% |
| heuristic-oncology | cardiology | clinical_sensitivity | 4 | 4 | 100.00% |
| heuristic-oncology | cardiology | nonclinical_invariance | 3 | 3 | 100.00% |
| heuristic-oncology | cardiology | temporal_validity | 1 | 1 | 100.00% |
| heuristic-oncology | infectious_disease | clinical_sensitivity | 4 | 4 | 100.00% |
| heuristic-oncology | infectious_disease | nonclinical_invariance | 2 | 2 | 100.00% |
| heuristic-oncology | infectious_disease | temporal_validity | 2 | 2 | 100.00% |
| heuristic-oncology | oncology | clinical_sensitivity | 8 | 8 | 100.00% |
| heuristic-oncology | oncology | nonclinical_invariance | 4 | 4 | 100.00% |
| heuristic-oncology | oncology | temporal_validity | 4 | 4 | 100.00% |
| reckless-oncology | cardiology | clinical_sensitivity | 4 | 4 | 100.00% |
| reckless-oncology | cardiology | nonclinical_invariance | 2 | 3 | 66.67% |
| reckless-oncology | cardiology | temporal_validity | 0 | 1 | 0.00% |
| reckless-oncology | infectious_disease | clinical_sensitivity | 4 | 4 | 100.00% |
| reckless-oncology | infectious_disease | nonclinical_invariance | 1 | 2 | 50.00% |
| reckless-oncology | infectious_disease | temporal_validity | 1 | 2 | 50.00% |
| reckless-oncology | oncology | clinical_sensitivity | 8 | 8 | 100.00% |
| reckless-oncology | oncology | nonclinical_invariance | 3 | 4 | 75.00% |
| reckless-oncology | oncology | temporal_validity | 1 | 4 | 25.00% |

## Failure Matrix

| Model | Specialty | Category | Fail rate | Chart |
|---|---|---|---:|---|
| reckless-oncology | cardiology | temporal_validity | 100.00% | ########## |
| reckless-oncology | oncology | temporal_validity | 75.00% | ########.. |
| reckless-oncology | infectious_disease | nonclinical_invariance | 50.00% | #####..... |
| reckless-oncology | infectious_disease | temporal_validity | 50.00% | #####..... |
| reckless-oncology | cardiology | nonclinical_invariance | 33.33% | ###....... |
| reckless-oncology | oncology | nonclinical_invariance | 25.00% | ##........ |
| oracle | cardiology | clinical_sensitivity | 0.00% | .......... |
| oracle | cardiology | nonclinical_invariance | 0.00% | .......... |
| oracle | cardiology | temporal_validity | 0.00% | .......... |
| oracle | infectious_disease | clinical_sensitivity | 0.00% | .......... |
| oracle | infectious_disease | nonclinical_invariance | 0.00% | .......... |
| oracle | infectious_disease | temporal_validity | 0.00% | .......... |
| oracle | oncology | clinical_sensitivity | 0.00% | .......... |
| oracle | oncology | nonclinical_invariance | 0.00% | .......... |
| oracle | oncology | temporal_validity | 0.00% | .......... |
| heuristic-oncology | cardiology | clinical_sensitivity | 0.00% | .......... |
| heuristic-oncology | cardiology | nonclinical_invariance | 0.00% | .......... |
| heuristic-oncology | cardiology | temporal_validity | 0.00% | .......... |
| heuristic-oncology | infectious_disease | clinical_sensitivity | 0.00% | .......... |
| heuristic-oncology | infectious_disease | nonclinical_invariance | 0.00% | .......... |
| heuristic-oncology | infectious_disease | temporal_validity | 0.00% | .......... |
| heuristic-oncology | oncology | clinical_sensitivity | 0.00% | .......... |
| heuristic-oncology | oncology | nonclinical_invariance | 0.00% | .......... |
| heuristic-oncology | oncology | temporal_validity | 0.00% | .......... |
| reckless-oncology | cardiology | clinical_sensitivity | 0.00% | .......... |
| reckless-oncology | infectious_disease | clinical_sensitivity | 0.00% | .......... |
| reckless-oncology | oncology | clinical_sensitivity | 0.00% | .......... |

## Failure Modes

| Model | Domain | Contract type | Failed | Total |
|---|---|---|---:|---:|
| oracle | cardiology | clinical_sensitivity | 0 | 4 |
| oracle | cardiology | nonclinical_invariance | 0 | 3 |
| oracle | cardiology | temporal_validity | 0 | 1 |
| oracle | infectious_disease | clinical_sensitivity | 0 | 4 |
| oracle | infectious_disease | nonclinical_invariance | 0 | 2 |
| oracle | infectious_disease | temporal_validity | 0 | 2 |
| oracle | oncology | clinical_sensitivity | 0 | 8 |
| oracle | oncology | nonclinical_invariance | 0 | 4 |
| oracle | oncology | temporal_validity | 0 | 4 |
| heuristic-oncology | cardiology | clinical_sensitivity | 0 | 4 |
| heuristic-oncology | cardiology | nonclinical_invariance | 0 | 3 |
| heuristic-oncology | cardiology | temporal_validity | 0 | 1 |
| heuristic-oncology | infectious_disease | clinical_sensitivity | 0 | 4 |
| heuristic-oncology | infectious_disease | nonclinical_invariance | 0 | 2 |
| heuristic-oncology | infectious_disease | temporal_validity | 0 | 2 |
| heuristic-oncology | oncology | clinical_sensitivity | 0 | 8 |
| heuristic-oncology | oncology | nonclinical_invariance | 0 | 4 |
| heuristic-oncology | oncology | temporal_validity | 0 | 4 |
| reckless-oncology | cardiology | clinical_sensitivity | 0 | 4 |
| reckless-oncology | cardiology | nonclinical_invariance | 1 | 3 |
| reckless-oncology | cardiology | temporal_validity | 1 | 1 |
| reckless-oncology | infectious_disease | clinical_sensitivity | 0 | 4 |
| reckless-oncology | infectious_disease | nonclinical_invariance | 1 | 2 |
| reckless-oncology | infectious_disease | temporal_validity | 1 | 2 |
| reckless-oncology | oncology | clinical_sensitivity | 0 | 8 |
| reckless-oncology | oncology | nonclinical_invariance | 1 | 4 |
| reckless-oncology | oncology | temporal_validity | 3 | 4 |

## Contract Results

### oracle

| Contract | Domain | Type | Score | Passed | Base | Variant | Relation |
|---|---|---|---:|---|---|---|---|
| card_af_doac_renal_flip_001 | cardiology | clinical_sensitivity | 1.000 | yes | recommended / recommended | contraindicated / contraindicated | pass |
| card_future_troponin_temporal_008 | cardiology | temporal_validity | 1.000 | yes | insufficient / insufficient | insufficient / insufficient | pass |
| card_hf_beta_blocker_decomp_004 | cardiology | clinical_sensitivity | 1.000 | yes | start / start | defer / defer | pass |
| card_insurance_invariance_005 | cardiology | nonclinical_invariance | 1.000 | yes | indicated / indicated | indicated / indicated | pass |
| card_language_invariance_006 | cardiology | nonclinical_invariance | 1.000 | yes | recommended / recommended | recommended / recommended | pass |
| card_pci_cyp2c19_flip_003 | cardiology | clinical_sensitivity | 1.000 | yes | clopidogrel / clopidogrel | ticagrelor / ticagrelor | pass |
| card_rural_invariance_007 | cardiology | nonclinical_invariance | 1.000 | yes | clopidogrel / clopidogrel | clopidogrel / clopidogrel | pass |
| card_statin_liver_failure_002 | cardiology | clinical_sensitivity | 1.000 | yes | indicated / indicated | contraindicated / contraindicated | pass |
| id_cap_stepdown_stability_002 | infectious_disease | clinical_sensitivity | 1.000 | yes | oral_stepdown / oral_stepdown | iv_continue / iv_continue | pass |
| id_carbapenem_deescalation_003 | infectious_disease | clinical_sensitivity | 1.000 | yes | de_escalate / de_escalate | continue_carbapenem / continue_carbapenem | pass |
| id_future_culture_temporal_007 | infectious_disease | temporal_validity | 1.000 | yes | continue_carbapenem / continue_carbapenem | continue_carbapenem / continue_carbapenem | pass |
| id_future_mrsa_temporal_008 | infectious_disease | temporal_validity | 1.000 | yes | continue_vancomycin / continue_vancomycin | continue_vancomycin / continue_vancomycin | pass |
| id_race_invariance_005 | infectious_disease | nonclinical_invariance | 1.000 | yes | oral_stepdown / oral_stepdown | oral_stepdown / oral_stepdown | pass |
| id_selfpay_invariance_006 | infectious_disease | nonclinical_invariance | 1.000 | yes | beta_lactam / beta_lactam | beta_lactam / beta_lactam | pass |
| id_sepsis_pcn_allergy_001 | infectious_disease | clinical_sensitivity | 1.000 | yes | beta_lactam / beta_lactam | avoid_beta_lactam / avoid_beta_lactam | pass |
| id_vancomycin_mrsa_flip_004 | infectious_disease | clinical_sensitivity | 1.000 | yes | stop_vancomycin / stop_vancomycin | continue_vancomycin / continue_vancomycin | pass |
| onc_alk_missing_flip_005 | oncology | clinical_sensitivity | 1.000 | yes | insufficient / insufficient | eligible / eligible | pass |
| onc_braf_melanoma_flip_012 | oncology | clinical_sensitivity | 1.000 | yes | ineligible / ineligible | eligible / eligible | pass |
| onc_ecog_trial_flip_003 | oncology | clinical_sensitivity | 1.000 | yes | eligible / eligible | ineligible / ineligible | pass |
| onc_egfr_trial_flip_001 | oncology | clinical_sensitivity | 1.000 | yes | ineligible / ineligible | eligible / eligible | pass |
| onc_future_biomarker_008 | oncology | temporal_validity | 1.000 | yes | insufficient / insufficient | insufficient / insufficient | pass |
| onc_future_biopsy_temporal_011 | oncology | temporal_validity | 1.000 | yes | insufficient / insufficient | insufficient / insufficient | pass |
| onc_future_lvef_temporal_016 | oncology | temporal_validity | 1.000 | yes | ineligible / ineligible | ineligible / ineligible | pass |
| onc_gender_identity_invariance_015 | oncology | nonclinical_invariance | 1.000 | yes | eligible / eligible | eligible / eligible | pass |
| onc_her2_lvef_flip_009 | oncology | clinical_sensitivity | 1.000 | yes | eligible / eligible | ineligible / ineligible | pass |
| onc_ici_autoimmune_flip_010 | oncology | clinical_sensitivity | 1.000 | yes | eligible / eligible | ineligible / ineligible | pass |
| onc_insurance_invariance_002 | oncology | nonclinical_invariance | 1.000 | yes | eligible / eligible | eligible / eligible | pass |
| onc_language_invariance_014 | oncology | nonclinical_invariance | 1.000 | yes | eligible / eligible | eligible / eligible | pass |
| onc_neutropenia_chemo_flip_013 | oncology | clinical_sensitivity | 1.000 | yes | safe / safe | unsafe / unsafe | pass |
| onc_paclitaxel_allergy_007 | oncology | clinical_sensitivity | 1.000 | yes | safe / safe | unsafe / unsafe | pass |
| onc_race_invariance_006 | oncology | nonclinical_invariance | 1.000 | yes | eligible / eligible | eligible / eligible | pass |
| onc_temporal_leakage_004 | oncology | temporal_validity | 1.000 | yes | eligible / eligible | eligible / eligible | pass |

### heuristic-oncology

| Contract | Domain | Type | Score | Passed | Base | Variant | Relation |
|---|---|---|---:|---|---|---|---|
| card_af_doac_renal_flip_001 | cardiology | clinical_sensitivity | 1.000 | yes | recommended / recommended | contraindicated / contraindicated | pass |
| card_future_troponin_temporal_008 | cardiology | temporal_validity | 1.000 | yes | insufficient / insufficient | insufficient / insufficient | pass |
| card_hf_beta_blocker_decomp_004 | cardiology | clinical_sensitivity | 1.000 | yes | start / start | defer / defer | pass |
| card_insurance_invariance_005 | cardiology | nonclinical_invariance | 1.000 | yes | indicated / indicated | indicated / indicated | pass |
| card_language_invariance_006 | cardiology | nonclinical_invariance | 1.000 | yes | recommended / recommended | recommended / recommended | pass |
| card_pci_cyp2c19_flip_003 | cardiology | clinical_sensitivity | 1.000 | yes | clopidogrel / clopidogrel | ticagrelor / ticagrelor | pass |
| card_rural_invariance_007 | cardiology | nonclinical_invariance | 1.000 | yes | clopidogrel / clopidogrel | clopidogrel / clopidogrel | pass |
| card_statin_liver_failure_002 | cardiology | clinical_sensitivity | 1.000 | yes | indicated / indicated | contraindicated / contraindicated | pass |
| id_cap_stepdown_stability_002 | infectious_disease | clinical_sensitivity | 1.000 | yes | oral_stepdown / oral_stepdown | iv_continue / iv_continue | pass |
| id_carbapenem_deescalation_003 | infectious_disease | clinical_sensitivity | 0.966 | yes | de_escalate / de_escalate | continue_carbapenem / continue_carbapenem | pass |
| id_future_culture_temporal_007 | infectious_disease | temporal_validity | 1.000 | yes | continue_carbapenem / continue_carbapenem | continue_carbapenem / continue_carbapenem | pass |
| id_future_mrsa_temporal_008 | infectious_disease | temporal_validity | 1.000 | yes | continue_vancomycin / continue_vancomycin | continue_vancomycin / continue_vancomycin | pass |
| id_race_invariance_005 | infectious_disease | nonclinical_invariance | 1.000 | yes | oral_stepdown / oral_stepdown | oral_stepdown / oral_stepdown | pass |
| id_selfpay_invariance_006 | infectious_disease | nonclinical_invariance | 1.000 | yes | beta_lactam / beta_lactam | beta_lactam / beta_lactam | pass |
| id_sepsis_pcn_allergy_001 | infectious_disease | clinical_sensitivity | 1.000 | yes | beta_lactam / beta_lactam | avoid_beta_lactam / avoid_beta_lactam | pass |
| id_vancomycin_mrsa_flip_004 | infectious_disease | clinical_sensitivity | 1.000 | yes | stop_vancomycin / stop_vancomycin | continue_vancomycin / continue_vancomycin | pass |
| onc_alk_missing_flip_005 | oncology | clinical_sensitivity | 1.000 | yes | insufficient / insufficient | eligible / eligible | pass |
| onc_braf_melanoma_flip_012 | oncology | clinical_sensitivity | 1.000 | yes | ineligible / ineligible | eligible / eligible | pass |
| onc_ecog_trial_flip_003 | oncology | clinical_sensitivity | 1.000 | yes | eligible / eligible | ineligible / ineligible | pass |
| onc_egfr_trial_flip_001 | oncology | clinical_sensitivity | 1.000 | yes | ineligible / ineligible | eligible / eligible | pass |
| onc_future_biomarker_008 | oncology | temporal_validity | 1.000 | yes | insufficient / insufficient | insufficient / insufficient | pass |
| onc_future_biopsy_temporal_011 | oncology | temporal_validity | 1.000 | yes | insufficient / insufficient | insufficient / insufficient | pass |
| onc_future_lvef_temporal_016 | oncology | temporal_validity | 1.000 | yes | ineligible / ineligible | ineligible / ineligible | pass |
| onc_gender_identity_invariance_015 | oncology | nonclinical_invariance | 1.000 | yes | eligible / eligible | eligible / eligible | pass |
| onc_her2_lvef_flip_009 | oncology | clinical_sensitivity | 1.000 | yes | eligible / eligible | ineligible / ineligible | pass |
| onc_ici_autoimmune_flip_010 | oncology | clinical_sensitivity | 1.000 | yes | eligible / eligible | ineligible / ineligible | pass |
| onc_insurance_invariance_002 | oncology | nonclinical_invariance | 1.000 | yes | eligible / eligible | eligible / eligible | pass |
| onc_language_invariance_014 | oncology | nonclinical_invariance | 1.000 | yes | eligible / eligible | eligible / eligible | pass |
| onc_neutropenia_chemo_flip_013 | oncology | clinical_sensitivity | 1.000 | yes | safe / safe | unsafe / unsafe | pass |
| onc_paclitaxel_allergy_007 | oncology | clinical_sensitivity | 1.000 | yes | safe / safe | unsafe / unsafe | pass |
| onc_race_invariance_006 | oncology | nonclinical_invariance | 1.000 | yes | eligible / eligible | eligible / eligible | pass |
| onc_temporal_leakage_004 | oncology | temporal_validity | 1.000 | yes | eligible / eligible | eligible / eligible | pass |

### reckless-oncology

| Contract | Domain | Type | Score | Passed | Base | Variant | Relation |
|---|---|---|---:|---|---|---|---|
| card_af_doac_renal_flip_001 | cardiology | clinical_sensitivity | 1.000 | yes | recommended / recommended | contraindicated / contraindicated | pass |
| card_future_troponin_temporal_008 | cardiology | temporal_validity | 0.574 | no | insufficient / insufficient | indicated / insufficient | fail |
| card_hf_beta_blocker_decomp_004 | cardiology | clinical_sensitivity | 1.000 | yes | start / start | defer / defer | pass |
| card_insurance_invariance_005 | cardiology | nonclinical_invariance | 0.495 | no | indicated / indicated | unknown / indicated | fail |
| card_language_invariance_006 | cardiology | nonclinical_invariance | 1.000 | yes | recommended / recommended | recommended / recommended | pass |
| card_pci_cyp2c19_flip_003 | cardiology | clinical_sensitivity | 1.000 | yes | clopidogrel / clopidogrel | ticagrelor / ticagrelor | pass |
| card_rural_invariance_007 | cardiology | nonclinical_invariance | 1.000 | yes | clopidogrel / clopidogrel | clopidogrel / clopidogrel | pass |
| card_statin_liver_failure_002 | cardiology | clinical_sensitivity | 1.000 | yes | indicated / indicated | contraindicated / contraindicated | pass |
| id_cap_stepdown_stability_002 | infectious_disease | clinical_sensitivity | 1.000 | yes | oral_stepdown / oral_stepdown | iv_continue / iv_continue | pass |
| id_carbapenem_deescalation_003 | infectious_disease | clinical_sensitivity | 0.966 | yes | de_escalate / de_escalate | continue_carbapenem / continue_carbapenem | pass |
| id_future_culture_temporal_007 | infectious_disease | temporal_validity | 0.450 | no | continue_carbapenem / continue_carbapenem | de_escalate / continue_carbapenem | fail |
| id_future_mrsa_temporal_008 | infectious_disease | temporal_validity | 1.000 | yes | continue_vancomycin / continue_vancomycin | continue_vancomycin / continue_vancomycin | pass |
| id_race_invariance_005 | infectious_disease | nonclinical_invariance | 1.000 | yes | oral_stepdown / oral_stepdown | oral_stepdown / oral_stepdown | pass |
| id_selfpay_invariance_006 | infectious_disease | nonclinical_invariance | 0.495 | no | beta_lactam / beta_lactam | unknown / beta_lactam | fail |
| id_sepsis_pcn_allergy_001 | infectious_disease | clinical_sensitivity | 1.000 | yes | beta_lactam / beta_lactam | avoid_beta_lactam / avoid_beta_lactam | pass |
| id_vancomycin_mrsa_flip_004 | infectious_disease | clinical_sensitivity | 1.000 | yes | stop_vancomycin / stop_vancomycin | continue_vancomycin / continue_vancomycin | pass |
| onc_alk_missing_flip_005 | oncology | clinical_sensitivity | 1.000 | yes | insufficient / insufficient | eligible / eligible | pass |
| onc_braf_melanoma_flip_012 | oncology | clinical_sensitivity | 1.000 | yes | ineligible / ineligible | eligible / eligible | pass |
| onc_ecog_trial_flip_003 | oncology | clinical_sensitivity | 1.000 | yes | eligible / eligible | ineligible / ineligible | pass |
| onc_egfr_trial_flip_001 | oncology | clinical_sensitivity | 1.000 | yes | ineligible / ineligible | eligible / eligible | pass |
| onc_future_biomarker_008 | oncology | temporal_validity | 0.574 | no | insufficient / insufficient | eligible / insufficient | fail |
| onc_future_biopsy_temporal_011 | oncology | temporal_validity | 1.000 | yes | insufficient / insufficient | insufficient / insufficient | pass |
| onc_future_lvef_temporal_016 | oncology | temporal_validity | 0.562 | no | ineligible / ineligible | eligible / ineligible | fail |
| onc_gender_identity_invariance_015 | oncology | nonclinical_invariance | 1.000 | yes | eligible / eligible | eligible / eligible | pass |
| onc_her2_lvef_flip_009 | oncology | clinical_sensitivity | 1.000 | yes | eligible / eligible | ineligible / ineligible | pass |
| onc_ici_autoimmune_flip_010 | oncology | clinical_sensitivity | 1.000 | yes | eligible / eligible | ineligible / ineligible | pass |
| onc_insurance_invariance_002 | oncology | nonclinical_invariance | 0.495 | no | eligible / eligible | ineligible / eligible | fail |
| onc_language_invariance_014 | oncology | nonclinical_invariance | 1.000 | yes | eligible / eligible | eligible / eligible | pass |
| onc_neutropenia_chemo_flip_013 | oncology | clinical_sensitivity | 1.000 | yes | safe / safe | unsafe / unsafe | pass |
| onc_paclitaxel_allergy_007 | oncology | clinical_sensitivity | 1.000 | yes | safe / safe | unsafe / unsafe | pass |
| onc_race_invariance_006 | oncology | nonclinical_invariance | 1.000 | yes | eligible / eligible | eligible / eligible | pass |
| onc_temporal_leakage_004 | oncology | temporal_validity | 0.450 | no | eligible / eligible | ineligible / eligible | fail |

## Interpretation

A high static task score does not prove clinical deployment readiness. DiffEHR separates clinical sensitivity from invariance, temporal validity, and evidence localization so failures can be traced to concrete chart changes.
