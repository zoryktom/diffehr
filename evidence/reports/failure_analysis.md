# DiffEHR Failure Analysis

This report is generated from machine-readable DiffEHR run outputs. Severity is assigned by benchmark rules, not by autonomous clinical adjudication.

## Aggregate Patterns

| Model | Failures | High | Medium | Low | Human review needed |
|---|---:|---:|---:|---:|---:|
| oracle | 0 | 0 | 0 | 0 | 0 |
| heuristic-oncology | 0 | 0 | 0 | 0 | 0 |
| reckless-oncology | 8 | 8 | 0 | 0 | 8 |

## Case-Level Failures

| Model | Contract | Domain | Category | Failed assertion | Severity | Expected | Observed | Evidence issue | Reproduce |
|---|---|---|---|---|---|---|---|---|---|
| reckless-oncology | card_future_troponin_temporal_008 | cardiology | temporal_validity | decision+relation+evidence+temporal | high | insufficient -> insufficient | insufficient -> indicated | variant temporal leakage | `PYTHONPATH=src python -m diffehr evaluate examples --model reckless-oncology --out /tmp/reckless-oncology.json` |
| reckless-oncology | card_insurance_invariance_005 | cardiology | nonclinical_invariance | decision+relation+evidence | high | indicated -> indicated | indicated -> unknown | variant citations | `PYTHONPATH=src python -m diffehr evaluate examples --model reckless-oncology --out /tmp/reckless-oncology.json` |
| reckless-oncology | id_future_culture_temporal_007 | infectious_disease | temporal_validity | decision+relation+evidence+temporal | high | continue_carbapenem -> continue_carbapenem | continue_carbapenem -> de_escalate | variant citations, variant temporal leakage | `PYTHONPATH=src python -m diffehr evaluate examples --model reckless-oncology --out /tmp/reckless-oncology.json` |
| reckless-oncology | id_selfpay_invariance_006 | infectious_disease | nonclinical_invariance | decision+relation+evidence | high | beta_lactam -> beta_lactam | beta_lactam -> unknown | variant citations | `PYTHONPATH=src python -m diffehr evaluate examples --model reckless-oncology --out /tmp/reckless-oncology.json` |
| reckless-oncology | onc_future_biomarker_008 | oncology | temporal_validity | decision+relation+evidence+temporal | high | insufficient -> insufficient | insufficient -> eligible | variant temporal leakage | `PYTHONPATH=src python -m diffehr evaluate examples --model reckless-oncology --out /tmp/reckless-oncology.json` |
| reckless-oncology | onc_future_lvef_temporal_016 | oncology | temporal_validity | decision+relation+evidence+temporal | high | ineligible -> ineligible | ineligible -> eligible | variant temporal leakage | `PYTHONPATH=src python -m diffehr evaluate examples --model reckless-oncology --out /tmp/reckless-oncology.json` |
| reckless-oncology | onc_insurance_invariance_002 | oncology | nonclinical_invariance | decision+relation+evidence | high | eligible -> eligible | eligible -> ineligible | variant citations | `PYTHONPATH=src python -m diffehr evaluate examples --model reckless-oncology --out /tmp/reckless-oncology.json` |
| reckless-oncology | onc_temporal_leakage_004 | oncology | temporal_validity | decision+relation+evidence+temporal | high | eligible -> eligible | eligible -> ineligible | variant citations, variant temporal leakage | `PYTHONPATH=src python -m diffehr evaluate examples --model reckless-oncology --out /tmp/reckless-oncology.json` |

## Severity Rules

- `high`: temporal leakage, safety-related expected decisions, or incorrect task decisions.
- `medium`: relation failure without a temporal or safety marker.
- `low`: evidence-only failure where decisions and relation were correct.

All failures are marked as needing human review before making any real clinical interpretation.
