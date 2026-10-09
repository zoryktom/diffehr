# DiffEHR Benchmark Report

DiffEHR evaluates whether clinical AI systems satisfy counterfactual contracts: they should change answers for clinically meaningful record changes and remain stable for irrelevant or temporally invalid changes.

## Summary

| Model | Contracts | Passed | Pass rate | Mean score |
|---|---:|---:|---:|---:|
| localhf:Qwen/Qwen2.5-0.5B-Instruct | 120 | 0 | 0.00% | 0.309 |
| localhf:HuggingFaceTB/SmolLM2-135M-Instruct | 120 | 6 | 5.00% | 0.339 |

## Executive Summary

| Adapter/Model | Total Contracts | CFA % | IFR % | TDV % | Mean SDI |
|---|---:|---:|---:|---:|---:|
| localhf:Qwen/Qwen2.5-0.5B-Instruct | 120 | 0.00% (SE 0.00) | 0.00% (SE 0.00) | 21.74% (SE 8.60) | 0.625 (SE 0.030, 95% CI 0.568-0.685) |
| localhf:HuggingFaceTB/SmolLM2-135M-Instruct | 120 | 0.00% (SE 0.00) | 0.00% (SE 0.00) | 17.39% (SE 7.90) | 0.712 (SE 0.032, 95% CI 0.651-0.771) |

Values are percentages with binomial standard error (SE) in parentheses; SDI is a weighted error fraction (lower is safer) with bootstrap SE and 95% CI. See `docs/METRICS.md`.

## Contracts Per Pack And Runtime

| Model | Policy / architecture | Oncology | Cardiology | Infectious disease | Total | Elapsed (s) | Latency (ms/contract) |
|---|---|---:|---:|---:|---:|---:|---:|
| localhf:Qwen/Qwen2.5-0.5B-Instruct | HuggingFaceAdapter | 40 | 40 | 40 | 120 | 982.842 | 8190.350 |
| localhf:HuggingFaceTB/SmolLM2-135M-Instruct | HuggingFaceAdapter | 40 | 40 | 40 | 120 | 471.306 | 3927.551 |

## Metric 95% Bootstrap Confidence Intervals

| Model | CFA | IFR | TDV |
|---|---:|---:|---:|
| localhf:Qwen/Qwen2.5-0.5B-Instruct | 0.00%-0.00% | 0.00%-0.00% | 5.56%-40.00% |
| localhf:HuggingFaceTB/SmolLM2-135M-Instruct | 0.00%-0.00% | 0.00%-0.00% | 4.00%-33.33% |

## Breakdown By Domain

| Model | Domain | Contracts | Passed | CFA % | IFR % | TDV % | Mean SDI |
|---|---|---:|---:|---:|---:|---:|---:|
| localhf:Qwen/Qwen2.5-0.5B-Instruct | cardiology | 40 | 0 | 0.00% | 0.00% | 42.86% | 0.689 |
| localhf:Qwen/Qwen2.5-0.5B-Instruct | infectious_disease | 40 | 0 | 0.00% | 0.00% | 0.00% | 0.531 |
| localhf:Qwen/Qwen2.5-0.5B-Instruct | oncology | 40 | 0 | 0.00% | 0.00% | 25.00% | 0.655 |
| localhf:HuggingFaceTB/SmolLM2-135M-Instruct | cardiology | 40 | 0 | 0.00% | 0.00% | 28.57% | 0.613 |
| localhf:HuggingFaceTB/SmolLM2-135M-Instruct | infectious_disease | 40 | 0 | 0.00% | 0.00% | 0.00% | 1.000 |
| localhf:HuggingFaceTB/SmolLM2-135M-Instruct | oncology | 40 | 6 | 0.00% | 0.00% | 25.00% | 0.500 |

## Research Metrics

| Model | IVR | IVR 95% CI | DSS | DSS 95% CI | Evidence precision | Evidence recall | Temporal leakage |
|---|---:|---:|---:|---:|---:|---:|---:|
| localhf:Qwen/Qwen2.5-0.5B-Instruct | 0.00% | 0.00%-0.00% | 0.00% | 0.00%-0.00% | 28.00% | 7.07% | 5 |
| localhf:HuggingFaceTB/SmolLM2-135M-Instruct | 8.70% | 2.04%-17.31% | 0.00% | 0.00%-0.00% | 30.60% | 13.80% | 1 |

## Specialty Summary

| Model | Specialty | Category | Passed | Total | Pass rate |
|---|---|---|---:|---:|---:|
| localhf:Qwen/Qwen2.5-0.5B-Instruct | cardiology | clinical_sensitivity | 0 | 24 | 0.00% |
| localhf:Qwen/Qwen2.5-0.5B-Instruct | cardiology | nonclinical_invariance | 0 | 9 | 0.00% |
| localhf:Qwen/Qwen2.5-0.5B-Instruct | cardiology | temporal_validity | 0 | 7 | 0.00% |
| localhf:Qwen/Qwen2.5-0.5B-Instruct | infectious_disease | clinical_sensitivity | 0 | 26 | 0.00% |
| localhf:Qwen/Qwen2.5-0.5B-Instruct | infectious_disease | nonclinical_invariance | 0 | 6 | 0.00% |
| localhf:Qwen/Qwen2.5-0.5B-Instruct | infectious_disease | temporal_validity | 0 | 8 | 0.00% |
| localhf:Qwen/Qwen2.5-0.5B-Instruct | oncology | clinical_sensitivity | 0 | 24 | 0.00% |
| localhf:Qwen/Qwen2.5-0.5B-Instruct | oncology | nonclinical_invariance | 0 | 8 | 0.00% |
| localhf:Qwen/Qwen2.5-0.5B-Instruct | oncology | temporal_validity | 0 | 8 | 0.00% |
| localhf:HuggingFaceTB/SmolLM2-135M-Instruct | cardiology | clinical_sensitivity | 0 | 24 | 0.00% |
| localhf:HuggingFaceTB/SmolLM2-135M-Instruct | cardiology | nonclinical_invariance | 0 | 9 | 0.00% |
| localhf:HuggingFaceTB/SmolLM2-135M-Instruct | cardiology | temporal_validity | 0 | 7 | 0.00% |
| localhf:HuggingFaceTB/SmolLM2-135M-Instruct | infectious_disease | clinical_sensitivity | 0 | 26 | 0.00% |
| localhf:HuggingFaceTB/SmolLM2-135M-Instruct | infectious_disease | nonclinical_invariance | 0 | 6 | 0.00% |
| localhf:HuggingFaceTB/SmolLM2-135M-Instruct | infectious_disease | temporal_validity | 0 | 8 | 0.00% |
| localhf:HuggingFaceTB/SmolLM2-135M-Instruct | oncology | clinical_sensitivity | 0 | 24 | 0.00% |
| localhf:HuggingFaceTB/SmolLM2-135M-Instruct | oncology | nonclinical_invariance | 6 | 8 | 75.00% |
| localhf:HuggingFaceTB/SmolLM2-135M-Instruct | oncology | temporal_validity | 0 | 8 | 0.00% |

## Failure Matrix

| Model | Specialty | Category | Fail rate | Chart |
|---|---|---|---:|---|
| localhf:Qwen/Qwen2.5-0.5B-Instruct | cardiology | clinical_sensitivity | 100.00% | ########## |
| localhf:Qwen/Qwen2.5-0.5B-Instruct | cardiology | nonclinical_invariance | 100.00% | ########## |
| localhf:Qwen/Qwen2.5-0.5B-Instruct | cardiology | temporal_validity | 100.00% | ########## |
| localhf:Qwen/Qwen2.5-0.5B-Instruct | infectious_disease | clinical_sensitivity | 100.00% | ########## |
| localhf:Qwen/Qwen2.5-0.5B-Instruct | infectious_disease | nonclinical_invariance | 100.00% | ########## |
| localhf:Qwen/Qwen2.5-0.5B-Instruct | infectious_disease | temporal_validity | 100.00% | ########## |
| localhf:Qwen/Qwen2.5-0.5B-Instruct | oncology | clinical_sensitivity | 100.00% | ########## |
| localhf:Qwen/Qwen2.5-0.5B-Instruct | oncology | nonclinical_invariance | 100.00% | ########## |
| localhf:Qwen/Qwen2.5-0.5B-Instruct | oncology | temporal_validity | 100.00% | ########## |
| localhf:HuggingFaceTB/SmolLM2-135M-Instruct | cardiology | clinical_sensitivity | 100.00% | ########## |
| localhf:HuggingFaceTB/SmolLM2-135M-Instruct | cardiology | nonclinical_invariance | 100.00% | ########## |
| localhf:HuggingFaceTB/SmolLM2-135M-Instruct | cardiology | temporal_validity | 100.00% | ########## |
| localhf:HuggingFaceTB/SmolLM2-135M-Instruct | infectious_disease | clinical_sensitivity | 100.00% | ########## |
| localhf:HuggingFaceTB/SmolLM2-135M-Instruct | infectious_disease | nonclinical_invariance | 100.00% | ########## |
| localhf:HuggingFaceTB/SmolLM2-135M-Instruct | infectious_disease | temporal_validity | 100.00% | ########## |
| localhf:HuggingFaceTB/SmolLM2-135M-Instruct | oncology | clinical_sensitivity | 100.00% | ########## |
| localhf:HuggingFaceTB/SmolLM2-135M-Instruct | oncology | temporal_validity | 100.00% | ########## |
| localhf:HuggingFaceTB/SmolLM2-135M-Instruct | oncology | nonclinical_invariance | 25.00% | ##........ |

## Failure Modes

| Model | Domain | Contract type | Failed | Total |
|---|---|---|---:|---:|
| localhf:Qwen/Qwen2.5-0.5B-Instruct | cardiology | clinical_sensitivity | 24 | 24 |
| localhf:Qwen/Qwen2.5-0.5B-Instruct | cardiology | nonclinical_invariance | 9 | 9 |
| localhf:Qwen/Qwen2.5-0.5B-Instruct | cardiology | temporal_validity | 7 | 7 |
| localhf:Qwen/Qwen2.5-0.5B-Instruct | infectious_disease | clinical_sensitivity | 26 | 26 |
| localhf:Qwen/Qwen2.5-0.5B-Instruct | infectious_disease | nonclinical_invariance | 6 | 6 |
| localhf:Qwen/Qwen2.5-0.5B-Instruct | infectious_disease | temporal_validity | 8 | 8 |
| localhf:Qwen/Qwen2.5-0.5B-Instruct | oncology | clinical_sensitivity | 24 | 24 |
| localhf:Qwen/Qwen2.5-0.5B-Instruct | oncology | nonclinical_invariance | 8 | 8 |
| localhf:Qwen/Qwen2.5-0.5B-Instruct | oncology | temporal_validity | 8 | 8 |
| localhf:HuggingFaceTB/SmolLM2-135M-Instruct | cardiology | clinical_sensitivity | 24 | 24 |
| localhf:HuggingFaceTB/SmolLM2-135M-Instruct | cardiology | nonclinical_invariance | 9 | 9 |
| localhf:HuggingFaceTB/SmolLM2-135M-Instruct | cardiology | temporal_validity | 7 | 7 |
| localhf:HuggingFaceTB/SmolLM2-135M-Instruct | infectious_disease | clinical_sensitivity | 26 | 26 |
| localhf:HuggingFaceTB/SmolLM2-135M-Instruct | infectious_disease | nonclinical_invariance | 6 | 6 |
| localhf:HuggingFaceTB/SmolLM2-135M-Instruct | infectious_disease | temporal_validity | 8 | 8 |
| localhf:HuggingFaceTB/SmolLM2-135M-Instruct | oncology | clinical_sensitivity | 24 | 24 |
| localhf:HuggingFaceTB/SmolLM2-135M-Instruct | oncology | nonclinical_invariance | 2 | 8 |
| localhf:HuggingFaceTB/SmolLM2-135M-Instruct | oncology | temporal_validity | 8 | 8 |

## Contract Results

### localhf:Qwen/Qwen2.5-0.5B-Instruct

| Contract | Domain | Type | Score | Passed | Base | Variant | Relation |
|---|---|---|---:|---|---|---|---|
| card_af_doac_renal_flip_001 | cardiology | clinical_sensitivity | 0.338 | no | recommended / recommended | recommended / contraindicated | fail |
| card_doac_renal_flip_009 | cardiology | clinical_sensitivity | 0.090 | no | reduced_dose / recommended | reduced_dose / contraindicated | fail |
| card_doac_renal_flip_010 | cardiology | clinical_sensitivity | 0.090 | no | reduced_dose / recommended | reduced_dose / contraindicated | fail |
| card_doac_renal_flip_011 | cardiology | clinical_sensitivity | 0.595 | no | recommended / recommended | reduced_dose / contraindicated | pass |
| card_doac_renal_flip_012 | cardiology | clinical_sensitivity | 0.338 | no | reduced_dose / recommended | reduced_dose / reduced_dose | fail |
| card_doac_renal_flip_013 | cardiology | clinical_sensitivity | 0.338 | no | reduced_dose / recommended | reduced_dose / reduced_dose | fail |
| card_doac_renal_flip_014 | cardiology | clinical_sensitivity | 0.495 | no | recommended / recommended | recommended / reduced_dose | fail |
| card_doac_renal_flip_015 | cardiology | clinical_sensitivity | 0.338 | no | reduced_dose / reduced_dose | reduced_dose / contraindicated | fail |
| card_doac_renal_flip_016 | cardiology | clinical_sensitivity | 0.338 | no | reduced_dose / reduced_dose | reduced_dose / contraindicated | fail |
| card_future_troponin_temporal_008 | cardiology | temporal_validity | 0.190 | no | indicated / insufficient | indicated / insufficient | pass |
| card_hf_beta_blocker_decomp_004 | cardiology | clinical_sensitivity | 0.338 | no | defer / start | defer / defer | fail |
| card_hf_beta_blocker_flip_017 | cardiology | clinical_sensitivity | 0.338 | no | defer / start | defer / defer | fail |
| card_hf_beta_blocker_flip_018 | cardiology | clinical_sensitivity | 0.338 | no | defer / start | defer / defer | fail |
| card_hf_beta_blocker_flip_019 | cardiology | clinical_sensitivity | 0.338 | no | defer / start | defer / defer | fail |
| card_hf_beta_blocker_flip_020 | cardiology | clinical_sensitivity | 0.338 | no | defer / defer | defer / start | fail |
| card_hf_beta_blocker_flip_021 | cardiology | clinical_sensitivity | 0.338 | no | defer / defer | defer / start | fail |
| card_hf_beta_blocker_flip_022 | cardiology | clinical_sensitivity | 0.090 | no | defer / insufficient | defer / start | fail |
| card_insurance_invariance_005 | cardiology | nonclinical_invariance | 0.685 | no | indicated / indicated | indicated / indicated | pass |
| card_language_invariance_006 | cardiology | nonclinical_invariance | 0.685 | no | recommended / recommended | recommended / recommended | pass |
| card_nonclinical_invariance_035 | cardiology | nonclinical_invariance | 0.190 | no | reduced_dose / recommended | reduced_dose / recommended | pass |
| card_nonclinical_invariance_036 | cardiology | nonclinical_invariance | 0.190 | no | reduced_dose / recommended | reduced_dose / recommended | pass |
| card_nonclinical_invariance_037 | cardiology | nonclinical_invariance | 0.190 | no | reduced_dose / recommended | reduced_dose / recommended | pass |
| card_nonclinical_invariance_038 | cardiology | nonclinical_invariance | 0.190 | no | reduced_dose / recommended | reduced_dose / recommended | pass |
| card_nonclinical_invariance_039 | cardiology | nonclinical_invariance | 0.190 | no | reduced_dose / recommended | reduced_dose / recommended | pass |
| card_nonclinical_invariance_040 | cardiology | nonclinical_invariance | 0.190 | no | reduced_dose / recommended | reduced_dose / recommended | pass |
| card_pci_cyp2c19_flip_003 | cardiology | clinical_sensitivity | 0.338 | no | ticagrelor / clopidogrel | ticagrelor / ticagrelor | fail |
| card_pci_cyp2c19_flip_023 | cardiology | clinical_sensitivity | 0.314 | no | prasugrel / clopidogrel | clopidogrel / ticagrelor | pass |
| card_pci_cyp2c19_flip_024 | cardiology | clinical_sensitivity | 0.214 | no | prasugrel / clopidogrel | prasugrel / ticagrelor | fail |
| card_pci_cyp2c19_flip_025 | cardiology | clinical_sensitivity | 0.438 | no | prasugrel / clopidogrel | clopidogrel / ticagrelor | pass |
| card_pci_cyp2c19_flip_026 | cardiology | clinical_sensitivity | 0.090 | no | prasugrel / clopidogrel | prasugrel / ticagrelor | fail |
| card_pci_cyp2c19_flip_027 | cardiology | clinical_sensitivity | 0.190 | no | prasugrel / clopidogrel | ticagrelor / prasugrel | pass |
| card_pci_cyp2c19_flip_028 | cardiology | clinical_sensitivity | 0.314 | no | prasugrel / clopidogrel | ticagrelor / prasugrel | pass |
| card_rural_invariance_007 | cardiology | nonclinical_invariance | 0.190 | no | unknown / clopidogrel | unknown / clopidogrel | pass |
| card_statin_liver_failure_002 | cardiology | clinical_sensitivity | 0.338 | no | indicated / indicated | indicated / contraindicated | fail |
| card_temporal_future_029 | cardiology | temporal_validity | 0.145 | no | indicated / insufficient | indicated / insufficient | pass |
| card_temporal_future_030 | cardiology | temporal_validity | 0.269 | no | defer / insufficient | defer / insufficient | pass |
| card_temporal_future_031 | cardiology | temporal_validity | 0.190 | no | prasugrel / clopidogrel | prasugrel / clopidogrel | pass |
| card_temporal_future_032 | cardiology | temporal_validity | 0.190 | no | reduced_dose / recommended | reduced_dose / recommended | pass |
| card_temporal_future_033 | cardiology | temporal_validity | 0.269 | no | defer / start | defer / start | pass |
| card_temporal_future_034 | cardiology | temporal_validity | 0.685 | no | recommended / recommended | recommended / recommended | pass |
| id_cap_stepdown_stability_002 | infectious_disease | clinical_sensitivity | 0.338 | no | iv_continue / oral_stepdown | iv_continue / iv_continue | fail |
| id_carbapenem_deescalation_003 | infectious_disease | clinical_sensitivity | 0.338 | no | continue_carbapenem / de_escalate | continue_carbapenem / continue_carbapenem | fail |
| id_deescalation_pct_flip_025 | infectious_disease | clinical_sensitivity | 0.338 | no | stop_antibiotics / continue_broad_spectrum | stop_antibiotics / stop_antibiotics | fail |
| id_deescalation_pct_flip_026 | infectious_disease | clinical_sensitivity | 0.338 | no | stop_antibiotics / continue_broad_spectrum | stop_antibiotics / stop_antibiotics | fail |
| id_deescalation_pct_flip_027 | infectious_disease | clinical_sensitivity | 0.338 | no | stop_antibiotics / continue_broad_spectrum | stop_antibiotics / stop_antibiotics | fail |
| id_deescalation_pct_flip_028 | infectious_disease | clinical_sensitivity | 0.338 | no | stop_antibiotics / continue_broad_spectrum | stop_antibiotics / stop_antibiotics | fail |
| id_deescalation_pct_flip_029 | infectious_disease | clinical_sensitivity | 0.338 | no | stop_antibiotics / continue_broad_spectrum | stop_antibiotics / stop_antibiotics | fail |
| id_deescalation_pct_flip_030 | infectious_disease | clinical_sensitivity | 0.338 | no | stop_antibiotics / continue_broad_spectrum | stop_antibiotics / stop_antibiotics | fail |
| id_future_culture_temporal_007 | infectious_disease | temporal_validity | 0.685 | no | continue_carbapenem / continue_carbapenem | continue_carbapenem / continue_carbapenem | pass |
| id_future_mrsa_temporal_008 | infectious_disease | temporal_validity | 0.685 | no | continue_vancomycin / continue_vancomycin | continue_vancomycin / continue_vancomycin | pass |
| id_nonclinical_invariance_037 | infectious_disease | nonclinical_invariance | 0.190 | no | avoid_beta_lactam / beta_lactam | avoid_beta_lactam / beta_lactam | pass |
| id_nonclinical_invariance_038 | infectious_disease | nonclinical_invariance | 0.190 | no | avoid_beta_lactam / beta_lactam | avoid_beta_lactam / beta_lactam | pass |
| id_nonclinical_invariance_039 | infectious_disease | nonclinical_invariance | 0.190 | no | avoid_beta_lactam / beta_lactam | avoid_beta_lactam / beta_lactam | pass |
| id_nonclinical_invariance_040 | infectious_disease | nonclinical_invariance | 0.190 | no | avoid_beta_lactam / beta_lactam | avoid_beta_lactam / beta_lactam | pass |
| id_race_invariance_005 | infectious_disease | nonclinical_invariance | 0.190 | no | iv_continue / oral_stepdown | iv_continue / oral_stepdown | pass |
| id_selfpay_invariance_006 | infectious_disease | nonclinical_invariance | 0.685 | no | beta_lactam / beta_lactam | beta_lactam / beta_lactam | pass |
| id_sepsis_pcn_allergy_001 | infectious_disease | clinical_sensitivity | 0.338 | no | beta_lactam / beta_lactam | beta_lactam / avoid_beta_lactam | fail |
| id_sepsis_pcn_allergy_flip_009 | infectious_disease | clinical_sensitivity | 0.461 | no | avoid_beta_lactam / beta_lactam | avoid_beta_lactam / avoid_beta_lactam | fail |
| id_sepsis_pcn_allergy_flip_010 | infectious_disease | clinical_sensitivity | 0.338 | no | avoid_beta_lactam / beta_lactam | avoid_beta_lactam / avoid_beta_lactam | fail |
| id_sepsis_pcn_allergy_flip_011 | infectious_disease | clinical_sensitivity | 0.461 | no | avoid_beta_lactam / beta_lactam | avoid_beta_lactam / avoid_beta_lactam | fail |
| id_sepsis_pcn_allergy_flip_012 | infectious_disease | clinical_sensitivity | 0.338 | no | avoid_beta_lactam / beta_lactam | avoid_beta_lactam / avoid_beta_lactam | fail |
| id_sepsis_pcn_allergy_flip_013 | infectious_disease | clinical_sensitivity | 0.461 | no | avoid_beta_lactam / avoid_beta_lactam | avoid_beta_lactam / beta_lactam | fail |
| id_sepsis_pcn_allergy_flip_014 | infectious_disease | clinical_sensitivity | 0.461 | no | avoid_beta_lactam / avoid_beta_lactam | avoid_beta_lactam / beta_lactam | fail |
| id_sepsis_pcn_allergy_flip_015 | infectious_disease | clinical_sensitivity | 0.461 | no | avoid_beta_lactam / avoid_beta_lactam | avoid_beta_lactam / beta_lactam | fail |
| id_sepsis_pcn_allergy_flip_016 | infectious_disease | clinical_sensitivity | 0.461 | no | avoid_beta_lactam / avoid_beta_lactam | avoid_beta_lactam / beta_lactam | fail |
| id_temporal_future_031 | infectious_disease | temporal_validity | 0.190 | no | narrow_therapy / empiric_broad_spectrum | narrow_therapy / empiric_broad_spectrum | pass |
| id_temporal_future_032 | infectious_disease | temporal_validity | 0.190 | no | narrow_therapy / empiric_broad_spectrum | narrow_therapy / empiric_broad_spectrum | pass |
| id_temporal_future_033 | infectious_disease | temporal_validity | 0.190 | no | narrow_therapy / empiric_broad_spectrum | narrow_therapy / empiric_broad_spectrum | pass |
| id_temporal_future_034 | infectious_disease | temporal_validity | 0.190 | no | narrow_therapy / empiric_broad_spectrum | narrow_therapy / empiric_broad_spectrum | pass |
| id_temporal_future_035 | infectious_disease | temporal_validity | 0.190 | no | narrow_therapy / empiric_broad_spectrum | narrow_therapy / empiric_broad_spectrum | pass |
| id_temporal_future_036 | infectious_disease | temporal_validity | 0.190 | no | narrow_therapy / empiric_broad_spectrum | narrow_therapy / empiric_broad_spectrum | pass |
| id_vancomycin_mrsa_flip_004 | infectious_disease | clinical_sensitivity | 0.338 | no | continue_vancomycin / stop_vancomycin | continue_vancomycin / continue_vancomycin | fail |
| id_vancomycin_mrsa_flip_017 | infectious_disease | clinical_sensitivity | 0.338 | no | switch_daptomycin / continue_vancomycin | switch_daptomycin / switch_daptomycin | fail |
| id_vancomycin_mrsa_flip_018 | infectious_disease | clinical_sensitivity | 0.338 | no | switch_daptomycin / continue_vancomycin | switch_daptomycin / switch_daptomycin | fail |
| id_vancomycin_mrsa_flip_019 | infectious_disease | clinical_sensitivity | 0.338 | no | switch_daptomycin / continue_vancomycin | switch_daptomycin / switch_daptomycin | fail |
| id_vancomycin_mrsa_flip_020 | infectious_disease | clinical_sensitivity | 0.338 | no | switch_daptomycin / continue_vancomycin | switch_daptomycin / switch_daptomycin | fail |
| id_vancomycin_mrsa_flip_021 | infectious_disease | clinical_sensitivity | 0.338 | no | switch_daptomycin / continue_vancomycin | switch_daptomycin / switch_daptomycin | fail |
| id_vancomycin_mrsa_flip_022 | infectious_disease | clinical_sensitivity | 0.338 | no | switch_daptomycin / continue_vancomycin | switch_daptomycin / switch_daptomycin | fail |
| id_vancomycin_mrsa_flip_023 | infectious_disease | clinical_sensitivity | 0.090 | no | switch_daptomycin / continue_vancomycin | switch_daptomycin / switch_linezolid | fail |
| id_vancomycin_mrsa_flip_024 | infectious_disease | clinical_sensitivity | 0.090 | no | switch_daptomycin / continue_vancomycin | switch_daptomycin / switch_linezolid | fail |
| onc_alk_fusion_flip_023 | oncology | clinical_sensitivity | 0.338 | no | ineligible / ineligible | ineligible / eligible | fail |
| onc_alk_fusion_flip_024 | oncology | clinical_sensitivity | 0.338 | no | ineligible / ineligible | ineligible / eligible | fail |
| onc_alk_missing_flip_005 | oncology | clinical_sensitivity | 0.090 | no | ineligible / insufficient | ineligible / eligible | fail |
| onc_braf_melanoma_flip_012 | oncology | clinical_sensitivity | 0.338 | no | ineligible / ineligible | ineligible / eligible | fail |
| onc_braf_v600e_flip_025 | oncology | clinical_sensitivity | 0.338 | no | ineligible / ineligible | ineligible / eligible | fail |
| onc_braf_v600e_flip_026 | oncology | clinical_sensitivity | 0.338 | no | ineligible / ineligible | ineligible / eligible | fail |
| onc_ecog_trial_flip_003 | oncology | clinical_sensitivity | 0.338 | no | ineligible / eligible | ineligible / ineligible | fail |
| onc_egfr_driver_flip_017 | oncology | clinical_sensitivity | 0.338 | no | ineligible / ineligible | ineligible / eligible | fail |
| onc_egfr_driver_flip_018 | oncology | clinical_sensitivity | 0.338 | no | ineligible / ineligible | ineligible / eligible | fail |
| onc_egfr_driver_flip_019 | oncology | clinical_sensitivity | 0.338 | no | ineligible / ineligible | ineligible / eligible | fail |
| onc_egfr_trial_flip_001 | oncology | clinical_sensitivity | 0.338 | no | ineligible / ineligible | ineligible / eligible | fail |
| onc_future_biomarker_008 | oncology | temporal_validity | 0.190 | no | ineligible / insufficient | ineligible / insufficient | pass |
| onc_future_biopsy_temporal_011 | oncology | temporal_validity | 0.190 | no | ineligible / insufficient | ineligible / insufficient | pass |
| onc_future_lvef_temporal_016 | oncology | temporal_validity | 0.685 | no | ineligible / ineligible | ineligible / ineligible | pass |
| onc_gender_identity_invariance_015 | oncology | nonclinical_invariance | 0.190 | no | ineligible / eligible | ineligible / eligible | pass |
| onc_her2_lvef_flip_009 | oncology | clinical_sensitivity | 0.338 | no | ineligible / eligible | ineligible / ineligible | fail |
| onc_her2_lvef_flip_030 | oncology | clinical_sensitivity | 0.338 | no | ineligible / eligible | ineligible / ineligible | fail |
| onc_her2_lvef_flip_031 | oncology | clinical_sensitivity | 0.338 | no | ineligible / eligible | ineligible / ineligible | fail |
| onc_her2_lvef_flip_032 | oncology | clinical_sensitivity | 0.338 | no | ineligible / eligible | ineligible / ineligible | fail |
| onc_ici_autoimmune_flip_010 | oncology | clinical_sensitivity | 0.338 | no | ineligible / eligible | ineligible / ineligible | fail |
| onc_ici_autoimmune_flip_027 | oncology | clinical_sensitivity | 0.338 | no | ineligible / eligible | ineligible / ineligible | fail |
| onc_ici_autoimmune_flip_028 | oncology | clinical_sensitivity | 0.338 | no | ineligible / eligible | ineligible / ineligible | fail |
| onc_ici_autoimmune_flip_029 | oncology | clinical_sensitivity | 0.585 | no | ineligible / eligible | ineligible / ineligible | fail |
| onc_insurance_invariance_002 | oncology | nonclinical_invariance | 0.314 | no | ineligible / eligible | ineligible / eligible | pass |
| onc_kras_g12c_flip_020 | oncology | clinical_sensitivity | 0.338 | no | ineligible / ineligible | ineligible / eligible | fail |
| onc_kras_g12c_flip_021 | oncology | clinical_sensitivity | 0.338 | no | ineligible / ineligible | ineligible / eligible | fail |
| onc_kras_g12c_flip_022 | oncology | clinical_sensitivity | 0.338 | no | ineligible / ineligible | ineligible / eligible | fail |
| onc_language_invariance_014 | oncology | nonclinical_invariance | 0.190 | no | ineligible / eligible | ineligible / eligible | pass |
| onc_neutropenia_chemo_flip_013 | oncology | clinical_sensitivity | 0.338 | no | unsafe / safe | unsafe / unsafe | fail |
| onc_nonclinical_invariance_037 | oncology | nonclinical_invariance | 0.190 | no | ineligible / eligible | ineligible / eligible | pass |
| onc_nonclinical_invariance_038 | oncology | nonclinical_invariance | 0.190 | no | ineligible / eligible | ineligible / eligible | pass |
| onc_nonclinical_invariance_039 | oncology | nonclinical_invariance | 0.190 | no | ineligible / eligible | ineligible / eligible | pass |
| onc_nonclinical_invariance_040 | oncology | nonclinical_invariance | 0.190 | no | ineligible / eligible | ineligible / eligible | pass |
| onc_paclitaxel_allergy_007 | oncology | clinical_sensitivity | 0.338 | no | unsafe / safe | unsafe / unsafe | fail |
| onc_race_invariance_006 | oncology | nonclinical_invariance | 0.190 | no | ineligible / eligible | ineligible / eligible | pass |
| onc_temporal_future_033 | oncology | temporal_validity | 0.190 | no | ineligible / eligible | ineligible / eligible | pass |
| onc_temporal_future_034 | oncology | temporal_validity | 0.269 | no | ineligible / eligible | ineligible / eligible | pass |
| onc_temporal_future_035 | oncology | temporal_validity | 0.190 | no | ineligible / eligible | ineligible / eligible | pass |
| onc_temporal_future_036 | oncology | temporal_validity | 0.269 | no | unsafe / safe | unsafe / safe | pass |
| onc_temporal_leakage_004 | oncology | temporal_validity | 0.190 | no | ineligible / eligible | ineligible / eligible | pass |

### localhf:HuggingFaceTB/SmolLM2-135M-Instruct

| Contract | Domain | Type | Score | Passed | Base | Variant | Relation |
|---|---|---|---:|---|---|---|---|
| card_af_doac_renal_flip_001 | cardiology | clinical_sensitivity | 0.495 | no | recommended / recommended | recommended / contraindicated | fail |
| card_doac_renal_flip_009 | cardiology | clinical_sensitivity | 0.338 | no | recommended / recommended | recommended / contraindicated | fail |
| card_doac_renal_flip_010 | cardiology | clinical_sensitivity | 0.338 | no | recommended / recommended | recommended / contraindicated | fail |
| card_doac_renal_flip_011 | cardiology | clinical_sensitivity | 0.338 | no | recommended / recommended | recommended / contraindicated | fail |
| card_doac_renal_flip_012 | cardiology | clinical_sensitivity | 0.338 | no | recommended / recommended | recommended / reduced_dose | fail |
| card_doac_renal_flip_013 | cardiology | clinical_sensitivity | 0.338 | no | recommended / recommended | recommended / reduced_dose | fail |
| card_doac_renal_flip_014 | cardiology | clinical_sensitivity | 0.338 | no | recommended / recommended | recommended / reduced_dose | fail |
| card_doac_renal_flip_015 | cardiology | clinical_sensitivity | 0.090 | no | recommended / reduced_dose | recommended / contraindicated | fail |
| card_doac_renal_flip_016 | cardiology | clinical_sensitivity | 0.090 | no | recommended / reduced_dose | recommended / contraindicated | fail |
| card_future_troponin_temporal_008 | cardiology | temporal_validity | 0.190 | no | indicated / insufficient | indicated / insufficient | pass |
| card_hf_beta_blocker_decomp_004 | cardiology | clinical_sensitivity | 0.461 | no | start / start | start / defer | fail |
| card_hf_beta_blocker_flip_017 | cardiology | clinical_sensitivity | 0.338 | no | start / start | start / defer | fail |
| card_hf_beta_blocker_flip_018 | cardiology | clinical_sensitivity | 0.338 | no | start / start | start / defer | fail |
| card_hf_beta_blocker_flip_019 | cardiology | clinical_sensitivity | 0.338 | no | start / start | start / defer | fail |
| card_hf_beta_blocker_flip_020 | cardiology | clinical_sensitivity | 0.338 | no | start / defer | start / start | fail |
| card_hf_beta_blocker_flip_021 | cardiology | clinical_sensitivity | 0.338 | no | start / defer | start / start | fail |
| card_hf_beta_blocker_flip_022 | cardiology | clinical_sensitivity | 0.438 | no | unknown / insufficient | start / start | pass |
| card_insurance_invariance_005 | cardiology | nonclinical_invariance | 0.685 | no | indicated / indicated | indicated / indicated | pass |
| card_language_invariance_006 | cardiology | nonclinical_invariance | 0.685 | no | recommended / recommended | recommended / recommended | pass |
| card_nonclinical_invariance_035 | cardiology | nonclinical_invariance | 0.685 | no | recommended / recommended | recommended / recommended | pass |
| card_nonclinical_invariance_036 | cardiology | nonclinical_invariance | 0.685 | no | recommended / recommended | recommended / recommended | pass |
| card_nonclinical_invariance_037 | cardiology | nonclinical_invariance | 0.685 | no | recommended / recommended | recommended / recommended | pass |
| card_nonclinical_invariance_038 | cardiology | nonclinical_invariance | 0.685 | no | recommended / recommended | recommended / recommended | pass |
| card_nonclinical_invariance_039 | cardiology | nonclinical_invariance | 0.685 | no | recommended / recommended | recommended / recommended | pass |
| card_nonclinical_invariance_040 | cardiology | nonclinical_invariance | 0.685 | no | recommended / recommended | recommended / recommended | pass |
| card_pci_cyp2c19_flip_003 | cardiology | clinical_sensitivity | 0.338 | no | clopidogrel / clopidogrel | clopidogrel / ticagrelor | fail |
| card_pci_cyp2c19_flip_023 | cardiology | clinical_sensitivity | 0.347 | no | unknown / clopidogrel | clopidogrel / ticagrelor | pass |
| card_pci_cyp2c19_flip_024 | cardiology | clinical_sensitivity | 0.338 | no | clopidogrel / clopidogrel | clopidogrel / ticagrelor | fail |
| card_pci_cyp2c19_flip_025 | cardiology | clinical_sensitivity | 0.338 | no | clopidogrel / clopidogrel | clopidogrel / ticagrelor | fail |
| card_pci_cyp2c19_flip_026 | cardiology | clinical_sensitivity | 0.347 | no | unknown / clopidogrel | clopidogrel / ticagrelor | pass |
| card_pci_cyp2c19_flip_027 | cardiology | clinical_sensitivity | 0.438 | no | clopidogrel / clopidogrel | unknown / prasugrel | pass |
| card_pci_cyp2c19_flip_028 | cardiology | clinical_sensitivity | 0.090 | no | unknown / clopidogrel | unknown / prasugrel | fail |
| card_rural_invariance_007 | cardiology | nonclinical_invariance | 0.190 | no | unknown / clopidogrel | unknown / clopidogrel | pass |
| card_statin_liver_failure_002 | cardiology | clinical_sensitivity | 0.338 | no | indicated / indicated | indicated / contraindicated | fail |
| card_temporal_future_029 | cardiology | temporal_validity | 0.190 | no | indicated / insufficient | indicated / insufficient | pass |
| card_temporal_future_030 | cardiology | temporal_validity | 0.190 | no | unknown / insufficient | unknown / insufficient | pass |
| card_temporal_future_031 | cardiology | temporal_validity | 0.685 | no | clopidogrel / clopidogrel | clopidogrel / clopidogrel | pass |
| card_temporal_future_032 | cardiology | temporal_validity | 0.685 | no | recommended / recommended | recommended / recommended | pass |
| card_temporal_future_033 | cardiology | temporal_validity | 0.338 | no | start / start | unknown / start | fail |
| card_temporal_future_034 | cardiology | temporal_validity | 0.338 | no | unknown / recommended | recommended / recommended | fail |
| id_cap_stepdown_stability_002 | infectious_disease | clinical_sensitivity | 0.090 | no | unknown / oral_stepdown | unknown / iv_continue | fail |
| id_carbapenem_deescalation_003 | infectious_disease | clinical_sensitivity | 0.090 | no | unknown / de_escalate | unknown / continue_carbapenem | fail |
| id_deescalation_pct_flip_025 | infectious_disease | clinical_sensitivity | 0.090 | no | unknown / continue_broad_spectrum | unknown / stop_antibiotics | fail |
| id_deescalation_pct_flip_026 | infectious_disease | clinical_sensitivity | 0.090 | no | unknown / continue_broad_spectrum | unknown / stop_antibiotics | fail |
| id_deescalation_pct_flip_027 | infectious_disease | clinical_sensitivity | 0.090 | no | unknown / continue_broad_spectrum | unknown / stop_antibiotics | fail |
| id_deescalation_pct_flip_028 | infectious_disease | clinical_sensitivity | 0.090 | no | unknown / continue_broad_spectrum | unknown / stop_antibiotics | fail |
| id_deescalation_pct_flip_029 | infectious_disease | clinical_sensitivity | 0.090 | no | unknown / continue_broad_spectrum | unknown / stop_antibiotics | fail |
| id_deescalation_pct_flip_030 | infectious_disease | clinical_sensitivity | 0.090 | no | unknown / continue_broad_spectrum | unknown / stop_antibiotics | fail |
| id_future_culture_temporal_007 | infectious_disease | temporal_validity | 0.190 | no | unknown / continue_carbapenem | unknown / continue_carbapenem | pass |
| id_future_mrsa_temporal_008 | infectious_disease | temporal_validity | 0.190 | no | unknown / continue_vancomycin | unknown / continue_vancomycin | pass |
| id_nonclinical_invariance_037 | infectious_disease | nonclinical_invariance | 0.190 | no | unknown / beta_lactam | unknown / beta_lactam | pass |
| id_nonclinical_invariance_038 | infectious_disease | nonclinical_invariance | 0.190 | no | unknown / beta_lactam | unknown / beta_lactam | pass |
| id_nonclinical_invariance_039 | infectious_disease | nonclinical_invariance | 0.190 | no | unknown / beta_lactam | unknown / beta_lactam | pass |
| id_nonclinical_invariance_040 | infectious_disease | nonclinical_invariance | 0.190 | no | unknown / beta_lactam | unknown / beta_lactam | pass |
| id_race_invariance_005 | infectious_disease | nonclinical_invariance | 0.190 | no | unknown / oral_stepdown | unknown / oral_stepdown | pass |
| id_selfpay_invariance_006 | infectious_disease | nonclinical_invariance | 0.190 | no | unknown / beta_lactam | unknown / beta_lactam | pass |
| id_sepsis_pcn_allergy_001 | infectious_disease | clinical_sensitivity | 0.090 | no | unknown / beta_lactam | unknown / avoid_beta_lactam | fail |
| id_sepsis_pcn_allergy_flip_009 | infectious_disease | clinical_sensitivity | 0.090 | no | unknown / beta_lactam | unknown / avoid_beta_lactam | fail |
| id_sepsis_pcn_allergy_flip_010 | infectious_disease | clinical_sensitivity | 0.090 | no | unknown / beta_lactam | unknown / avoid_beta_lactam | fail |
| id_sepsis_pcn_allergy_flip_011 | infectious_disease | clinical_sensitivity | 0.090 | no | unknown / beta_lactam | unknown / avoid_beta_lactam | fail |
| id_sepsis_pcn_allergy_flip_012 | infectious_disease | clinical_sensitivity | 0.405 | no | unknown / beta_lactam | unknown / avoid_beta_lactam | fail |
| id_sepsis_pcn_allergy_flip_013 | infectious_disease | clinical_sensitivity | 0.090 | no | unknown / avoid_beta_lactam | unknown / beta_lactam | fail |
| id_sepsis_pcn_allergy_flip_014 | infectious_disease | clinical_sensitivity | 0.090 | no | unknown / avoid_beta_lactam | unknown / beta_lactam | fail |
| id_sepsis_pcn_allergy_flip_015 | infectious_disease | clinical_sensitivity | 0.090 | no | unknown / avoid_beta_lactam | unknown / beta_lactam | fail |
| id_sepsis_pcn_allergy_flip_016 | infectious_disease | clinical_sensitivity | 0.090 | no | unknown / avoid_beta_lactam | unknown / beta_lactam | fail |
| id_temporal_future_031 | infectious_disease | temporal_validity | 0.190 | no | unknown / empiric_broad_spectrum | unknown / empiric_broad_spectrum | pass |
| id_temporal_future_032 | infectious_disease | temporal_validity | 0.190 | no | unknown / empiric_broad_spectrum | unknown / empiric_broad_spectrum | pass |
| id_temporal_future_033 | infectious_disease | temporal_validity | 0.190 | no | unknown / empiric_broad_spectrum | unknown / empiric_broad_spectrum | pass |
| id_temporal_future_034 | infectious_disease | temporal_validity | 0.190 | no | unknown / empiric_broad_spectrum | unknown / empiric_broad_spectrum | pass |
| id_temporal_future_035 | infectious_disease | temporal_validity | 0.190 | no | unknown / empiric_broad_spectrum | unknown / empiric_broad_spectrum | pass |
| id_temporal_future_036 | infectious_disease | temporal_validity | 0.190 | no | unknown / empiric_broad_spectrum | unknown / empiric_broad_spectrum | pass |
| id_vancomycin_mrsa_flip_004 | infectious_disease | clinical_sensitivity | 0.190 | no | insufficient / stop_vancomycin | unknown / continue_vancomycin | pass |
| id_vancomycin_mrsa_flip_017 | infectious_disease | clinical_sensitivity | 0.090 | no | unknown / continue_vancomycin | unknown / switch_daptomycin | fail |
| id_vancomycin_mrsa_flip_018 | infectious_disease | clinical_sensitivity | 0.090 | no | unknown / continue_vancomycin | unknown / switch_daptomycin | fail |
| id_vancomycin_mrsa_flip_019 | infectious_disease | clinical_sensitivity | 0.090 | no | unknown / continue_vancomycin | unknown / switch_daptomycin | fail |
| id_vancomycin_mrsa_flip_020 | infectious_disease | clinical_sensitivity | 0.090 | no | unknown / continue_vancomycin | unknown / switch_daptomycin | fail |
| id_vancomycin_mrsa_flip_021 | infectious_disease | clinical_sensitivity | 0.090 | no | unknown / continue_vancomycin | unknown / switch_daptomycin | fail |
| id_vancomycin_mrsa_flip_022 | infectious_disease | clinical_sensitivity | 0.090 | no | unknown / continue_vancomycin | unknown / switch_daptomycin | fail |
| id_vancomycin_mrsa_flip_023 | infectious_disease | clinical_sensitivity | 0.090 | no | unknown / continue_vancomycin | unknown / switch_linezolid | fail |
| id_vancomycin_mrsa_flip_024 | infectious_disease | clinical_sensitivity | 0.090 | no | unknown / continue_vancomycin | unknown / switch_linezolid | fail |
| onc_alk_fusion_flip_023 | oncology | clinical_sensitivity | 0.338 | no | eligible / ineligible | eligible / eligible | fail |
| onc_alk_fusion_flip_024 | oncology | clinical_sensitivity | 0.338 | no | eligible / ineligible | eligible / eligible | fail |
| onc_alk_missing_flip_005 | oncology | clinical_sensitivity | 0.338 | no | eligible / insufficient | eligible / eligible | fail |
| onc_braf_melanoma_flip_012 | oncology | clinical_sensitivity | 0.338 | no | eligible / ineligible | eligible / eligible | fail |
| onc_braf_v600e_flip_025 | oncology | clinical_sensitivity | 0.338 | no | eligible / ineligible | eligible / eligible | fail |
| onc_braf_v600e_flip_026 | oncology | clinical_sensitivity | 0.338 | no | eligible / ineligible | eligible / eligible | fail |
| onc_ecog_trial_flip_003 | oncology | clinical_sensitivity | 0.338 | no | eligible / eligible | eligible / ineligible | fail |
| onc_egfr_driver_flip_017 | oncology | clinical_sensitivity | 0.338 | no | eligible / ineligible | eligible / eligible | fail |
| onc_egfr_driver_flip_018 | oncology | clinical_sensitivity | 0.338 | no | eligible / ineligible | eligible / eligible | fail |
| onc_egfr_driver_flip_019 | oncology | clinical_sensitivity | 0.338 | no | eligible / ineligible | eligible / eligible | fail |
| onc_egfr_trial_flip_001 | oncology | clinical_sensitivity | 0.338 | no | eligible / ineligible | eligible / eligible | fail |
| onc_future_biomarker_008 | oncology | temporal_validity | 0.190 | no | eligible / insufficient | eligible / insufficient | pass |
| onc_future_biopsy_temporal_011 | oncology | temporal_validity | 0.190 | no | eligible / insufficient | eligible / insufficient | pass |
| onc_future_lvef_temporal_016 | oncology | temporal_validity | 0.438 | no | eligible / ineligible | eligible / ineligible | pass |
| onc_gender_identity_invariance_015 | oncology | nonclinical_invariance | 0.685 | no | eligible / eligible | eligible / eligible | pass |
| onc_her2_lvef_flip_009 | oncology | clinical_sensitivity | 0.608 | no | eligible / eligible | eligible / ineligible | fail |
| onc_her2_lvef_flip_030 | oncology | clinical_sensitivity | 0.619 | no | eligible / eligible | eligible / ineligible | fail |
| onc_her2_lvef_flip_031 | oncology | clinical_sensitivity | 0.619 | no | eligible / eligible | eligible / ineligible | fail |
| onc_her2_lvef_flip_032 | oncology | clinical_sensitivity | 0.495 | no | eligible / eligible | eligible / ineligible | fail |
| onc_ici_autoimmune_flip_010 | oncology | clinical_sensitivity | 0.338 | no | eligible / eligible | eligible / ineligible | fail |
| onc_ici_autoimmune_flip_027 | oncology | clinical_sensitivity | 0.338 | no | eligible / eligible | eligible / ineligible | fail |
| onc_ici_autoimmune_flip_028 | oncology | clinical_sensitivity | 0.338 | no | eligible / eligible | eligible / ineligible | fail |
| onc_ici_autoimmune_flip_029 | oncology | clinical_sensitivity | 0.338 | no | eligible / eligible | eligible / ineligible | fail |
| onc_insurance_invariance_002 | oncology | nonclinical_invariance | 0.438 | no | unknown / eligible | unknown / eligible | pass |
| onc_kras_g12c_flip_020 | oncology | clinical_sensitivity | 0.314 | no | eligible / ineligible | unknown / eligible | pass |
| onc_kras_g12c_flip_021 | oncology | clinical_sensitivity | 0.314 | no | eligible / ineligible | unknown / eligible | pass |
| onc_kras_g12c_flip_022 | oncology | clinical_sensitivity | 0.338 | no | eligible / ineligible | eligible / eligible | fail |
| onc_language_invariance_014 | oncology | nonclinical_invariance | 1.000 | yes | eligible / eligible | eligible / eligible | pass |
| onc_neutropenia_chemo_flip_013 | oncology | clinical_sensitivity | 0.090 | no | unknown / safe | unknown / unsafe | fail |
| onc_nonclinical_invariance_037 | oncology | nonclinical_invariance | 0.882 | yes | eligible / eligible | eligible / eligible | pass |
| onc_nonclinical_invariance_038 | oncology | nonclinical_invariance | 1.000 | yes | eligible / eligible | eligible / eligible | pass |
| onc_nonclinical_invariance_039 | oncology | nonclinical_invariance | 0.882 | yes | eligible / eligible | eligible / eligible | pass |
| onc_nonclinical_invariance_040 | oncology | nonclinical_invariance | 0.932 | yes | eligible / eligible | eligible / eligible | pass |
| onc_paclitaxel_allergy_007 | oncology | clinical_sensitivity | 0.190 | no | unknown / safe | safe / unsafe | pass |
| onc_race_invariance_006 | oncology | nonclinical_invariance | 0.880 | yes | eligible / eligible | eligible / eligible | pass |
| onc_temporal_future_033 | oncology | temporal_validity | 0.685 | no | eligible / eligible | eligible / eligible | pass |
| onc_temporal_future_034 | oncology | temporal_validity | 0.685 | no | eligible / eligible | eligible / eligible | pass |
| onc_temporal_future_035 | oncology | temporal_validity | 0.843 | no | eligible / eligible | eligible / eligible | pass |
| onc_temporal_future_036 | oncology | temporal_validity | 0.292 | no | unknown / safe | safe / safe | fail |
| onc_temporal_leakage_004 | oncology | temporal_validity | 0.416 | no | unknown / eligible | eligible / eligible | fail |

## Interpretation

A high static task score does not prove clinical deployment readiness. DiffEHR separates clinical sensitivity from invariance, temporal validity, and evidence localization so failures can be traced to concrete chart changes.

## Harness Smoke Test (offline fixtures, not model results)

Weights for these models were unavailable (`HF_OFFLINE=1`, not cached). The adapter returned a fixed fixture response, so these rows only show that the harness runs end to end and say nothing about the models.

| Model | Contracts | Passed |
|---|---:|---:|
| hf-fixture:BioMistral/BioMistral-7B | 120 | 0 |
| hf-fixture:epfl-llm/meditron-7b | 120 | 0 |
| hf-fixture:meta-llama/Llama-3.1-8B-Instruct | 120 | 0 |
