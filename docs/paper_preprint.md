# DiffEHR: Counterfactual Contract Testing for Clinical AI Systems on Synthetic FHIR Records

**Author:** Zorykto Mykola
**Version:** 0.2.0 (artifact `zoryktom/diffehr`)  **Date:** 2026-10-09
**Target venues:** JAMIA / medRxiv / arXiv (cs.AI, cs.CY)
**Status:** Preprint. Synthetic, author-generated data; not clinician-validated.

## Abstract

**Objective.** Static accuracy benchmarks can conceal unsafe behavior in clinical AI systems. We present DiffEHR, an executable framework that tests whether a system changes its answer for the right clinical reasons, and only for those reasons, using paired synthetic FHIR R4 records ("counterfactual contracts").

**Materials and Methods.** A contract couples a base chart and a variant chart that differ by one controlled change, a decision task, allowed decisions, expected decisions, required evidence citations, and a decision-time cutoff. We release 120 contracts (40 each in oncology, cardiology and infectious disease): 74 clinical-sensitivity contracts that must flip, 23 non-clinical invariance contracts (payer, race, language, setting) that must not, and 23 temporal-validity contracts that must ignore post-decision evidence. Four headline metrics are defined: Counterfactual Flip Accuracy (CFA), Invariance Failure Rate (IFR), Temporal Directional Violation (TDV) and a safety-weighted Safety Divergence Index (SDI), each with standard errors and deterministic 95% bootstrap intervals. A discovery fuzzer mutates a FHIR chart along demographic, insurance, critical-laboratory-threshold and temporal-injection families while enforcing resource-id and subject-reference integrity.

**Results.** Three fully offline policies were evaluated: an oracle, a keyword heuristic, and a deliberately flawed "reckless" policy. The oracle passed 120/120 contracts (CFA 100%, IFR 0%, TDV 0%, SDI 0.000). The heuristic passed 80/120 (66.7%; CFA 64.9% [SE 5.6], IFR 0.0%, TDV 0.0%, SDI 0.191 [95% CI 0.132-0.257]) and passed all 32 contracts it was originally tuned on but only 16/40 infectious-disease contracts. The reckless policy passed 59/120 (49.2%; CFA 60.8%, IFR 30.4% [SE 9.6], TDV 47.8% [SE 10.4], SDI 0.295 [0.225-0.369]) and cited 11 post-decision evidence items. The fuzzer surfaced 7 findings for the reckless policy (3 payer-driven invariance violations, 1 temporal leakage, 3 clinical insensitivities), 3 clinical insensitivities for the heuristic, and none for the oracle.

**Discussion and Conclusion.** Contract-level metrics exposed failures (payer sensitivity, temporal leakage, insensitivity to renal, cardiac and troponin thresholds) that a pass/fail accuracy number does not separate. No large language model was evaluated in this release; HuggingFace and OpenAI-compatible adapters are implemented and unit-tested offline, and empirical results for them are future work. Results characterize the benchmark's discriminative behavior on three reference policies, not the safety of any deployed system.

**Keywords:** clinical AI evaluation; counterfactual testing; FHIR; synthetic data; invariance; temporal leakage; patient safety.

## 1. Introduction

Clinical AI systems are usually validated with aggregate accuracy on held-out cases. Accuracy does not say why a system was right. A model can be correct on one chart while keying on payer status, using results that were not yet available at the time of the decision, or ignoring a contraindication such as severe renal impairment. Such failures matter because they implicate fairness [Obermeyer 2019; Kusner 2017], retrospective-validation validity, and direct patient harm.

Software engineering addresses analogous problems with unit tests and behavioral testing; CheckList [Ribeiro 2020] introduced the idea for NLP. We adapt it to clinical records. A DiffEHR *contract* specifies a minimal counterfactual edit to a chart and the behavioral relation that must hold: **flip** (a decisive clinical fact changed), **same** (an irrelevant attribute changed, or evidence became available only after the decision date). Contracts are machine-checkable, version-controlled, and run against any system exposing a structured-output adapter.

Contributions: (1) a strict, validated contract schema with FHIR R4 bundles and referential-integrity checks; (2) 120 synthetic contracts across three specialties; (3) four headline metrics with uncertainty estimates and defined edge-case behavior; (4) a FHIR-aware counterfactual fuzzer; (5) an offline, reproducible pipeline with CI; and (6) an empirical characterization with three reference policies.

## 2. Clinical Counterfactual Formulation

Let a chart be a time-indexed set of clinical facts $C = \{(e_i, t_i)\}$, a decision time $\tau$, and non-clinical attributes $A$. A system $f$ maps $(C, A, \tau, q)$ for task $q$ to a decision $d \in \mathcal{D}$ and a set of cited evidence $E \subseteq C$. A counterfactual edit $\delta$ yields a variant chart $C'$. Three contract families are defined:

- **Clinical sensitivity (flip).** $\delta$ changes a guideline-decisive fact (for example CrCl crossing a DOAC dose threshold, EGFR driver status, penicillin allergy history). Required: $f(C') \neq f(C)$ and both match the expected decisions.
- **Non-clinical invariance (same).** $\delta$ changes only $A$ (payer, race, language, care setting). Required: $f(C') = f(C)$.
- **Temporal validity (same).** $\delta$ adds or moves evidence to $t > \tau$. Required: $f(C') = f(C)$ and $E \cap \{e_i : t_i > \tau\} = \emptyset$.

Every contract additionally requires that cited evidence cover a declared set of required chart items.

## 3. Contract Schema Design

Contracts are JSON documents validated by strict Pydantic v2 models (`extra="forbid"`, frozen). Required fields are `id`, `title`, `domain`, `task`, `contract_type`, `allowed_decisions`, `base_patient`, `variant_patient` and `expected` (`relation`, expected decisions, `required_citations`, `forbidden_after_as_of`). Validation rejects unknown fields, duplicate decisions, invalid dates, relation/decision contradictions (`same` with different decisions, `flip` with equal ones), citations absent from the chart, and `decision_index_timestamp` mismatches.

Each of the 120 contracts embeds a FHIR R4 Bundle per chart (Patient, Observation, MedicationRequest, Procedure, Encounter, Condition, AllergyIntolerance, DocumentReference). The schema enforces an allowed resource-type set, unique `(resourceType, id)` pairs, that every `subject.reference` of the form `Patient/x` resolves to a Patient in the bundle, and that the bundle's Patient id equals the chart id. Loader errors report file, line and column. A manifest (`examples/manifest.json`) records per-file SHA-256 checksums and counts, and per-pack `pack.json` files are checked against it; a stale manifest fails validation. Full field documentation is in `docs/CONTRACT_SCHEMA.md`.

## 4. Metrics

Let $F$, $N$, $T$ denote flip, non-clinical-invariance and temporal-validity contracts.

- **CFA** $= |\{c \in F: \text{both decisions correct and differ}\}| / |F|$.
- **IFR** $= |\{c \in N: f(C') \neq f(C)\}| / |N|$.
- **TDV** $= |\{c \in T: f(C') \neq f(C) \lor E' \text{ cites post-}\tau \text{ evidence}\}| / |T|$.
- **SDI** is a weighted error fraction over contract sides; sides whose expected decision is safety-critical (`contraindicated`, `unsafe`, `avoid_beta_lactam`, `defer`) carry weight 3, others weight 1.

Empty denominators yield 0.0 (no observable violation) instead of raising. Standard errors are binomial, $\sqrt{p(1-p)/n}$, for CFA, IFR and TDV and a bootstrap standard deviation for SDI. 95% confidence intervals use 1,000 contract-level bootstrap resamples with seed 2025; resamples with an empty relevant denominator are skipped rather than counted as zero. Legacy metrics (IVR, DSS, evidence precision/recall, leakage counts) are retained; see `docs/METRICS.md`.

## 5. Experimental Setup

**Contracts.** 120 contracts, 40 per pack: oncology (EGFR, KRAS G12C, ALK, BRAF, immune-checkpoint autoimmunity, HER2/LVEF, temporal, invariance), cardiology (DOAC renal dosing bands, beta-blocker use in heart failure, CYP2C19/clopidogrel, temporal, invariance) and infectious disease (penicillin allergy, MRSA, procalcitonin de-escalation, temporal, invariance). Of these, 32 were hand-authored in earlier versions and 88 were produced by the deterministic generator `scripts/generate_contracts.py`; FHIR bundles for the 32 were materialized by `scripts/add_fhir_bundles.py`. All data are synthetic, author-checked, and not clinician-reviewed.

**Systems (all offline; no API calls or model downloads).**
- *Oracle:* returns the contract's expected decisions and required citations (validates the harness; upper bound).
- *Heuristic:* keyword rules that respect decision-time cutoffs. Rules were written against the original 32 contracts.
- *Reckless:* the heuristic with temporal checks disabled and an insurance bias (adverse payer status lowers eligibility), simulating known failure modes.

**Fuzzer.** On `examples/discovery/base_chart.json` (an EGFR-mutant oncology chart) the fuzzer generates 20 perturbations (seed 2025): payer, race, ethnicity, gender identity, language and postal-code changes; pre-decision critical findings (eGFR 24, LVEF 38%, ANC 400, troponin I 2.4 ng/mL) that should flip eligibility; and temporal manipulations (one existing result shifted one week past $\tau$; future-dated biopsy, pathology and culture results injected). Each mutated bundle is checked for id uniqueness and subject-reference integrity before use.

**Pipeline.** `bash scripts/run_all_benchmarks.sh` validates manifests, runs all three systems, fuzzes with each, and writes JSON to `evidence/runs/` and Markdown to `evidence/reports/`. Runs record version, dataset fingerprint (SHA-256), seed and timestamp; per-contract latency is reported.

## 6. Results

### 6.1 Benchmark performance (120 contracts)

| System | Passed | Pass rate | CFA % (SE) | IFR % (SE) | TDV % (SE) | Mean SDI (SE; 95% CI) |
|---|---:|---:|---|---|---|---|
| Oracle | 120/120 | 100.0% | 100.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 0.000 (0.000; 0.000-0.000) |
| Heuristic | 80/120 | 66.7% | 64.86 (5.55) | 0.00 (0.00) | 0.00 (0.00) | 0.191 (0.032; 0.132-0.257) |
| Reckless | 59/120 | 49.2% | 60.81 (5.67) | 30.43 (9.59) | 47.83 (10.42) | 0.295 (0.038; 0.225-0.369) |

Denominators: CFA n = 74, IFR n = 23, TDV n = 23. Bootstrap 95% CIs: CFA heuristic 53.95-75.00%, reckless 50.00-71.43%; IFR reckless 12.50-50.00%; TDV reckless 25.00-68.42%. Per-contract latency is on the order of 0.02-0.04 ms for these in-process policies (`evidence/reports/full_benchmark_report.md`); it is not informative for model-based adapters.

### 6.2 By specialty

| System | Pack | Passed /40 | CFA % | IFR % | TDV % | SDI |
|---|---|---:|---:|---:|---:|---:|
| Heuristic | Oncology | 33 | 79.17 | 0.00 | 0.00 | 0.095 |
| Heuristic | Cardiology | 31 | 70.83 | 0.00 | 0.00 | 0.066 |
| Heuristic | Infectious disease | 16 | 46.15 | 0.00 | 0.00 | 0.408 |
| Reckless | Oncology | 25 | 75.00 | 25.00 | 62.50 | 0.190 |
| Reckless | Cardiology | 21 | 66.67 | 33.33 | 71.43 | 0.208 |
| Reckless | Infectious disease | 13 | 42.31 | 33.33 | 12.50 | 0.480 |

The heuristic passes all 32 contracts it was tuned on yet only 80/120 overall, with the weakest results in infectious disease (SDI 0.408), where rules for MRSA coverage, procalcitonin de-escalation and allergy history were absent. This illustrates the benchmark detecting rule overfitting. The heuristic's TDV of 0% does not mean it passes temporal contracts (14/23 passed): its failures there are incorrect decisions, not leakage, which TDV deliberately does not count. The reckless policy leaked 11 post-decision citations.

### 6.3 Discovery fuzzer

| System | Perturbations | Findings | Invariance | Temporal leakage | Clinical insensitivity |
|---|---:|---:|---:|---:|---:|
| Oracle | 20 | 0 | 0 | 0 | 0 |
| Heuristic | 20 | 3 | 0 | 0 | 3 |
| Reckless | 20 | 7 | 3 | 1 | 3 |

## 7. Failure Mode Taxonomy

The seven reckless-policy fuzzer discoveries fall into three classes (full FHIR diffs in `evidence/reports/failure_analysis.md`; each is reproducible with `diffehr replay-finding`):

1. **Payer-driven invariance violation (3).** Changing `Patient.payer` from commercial to Medicaid (`fuzz_demographic_003`), self-pay (`_004`) or uninsured (`_006`) flipped `eligible` to `ineligible` with all clinical resources unchanged. Consequence: identical clinical facts receive different recommendations by coverage, an equity and liability hazard. Race, ethnicity, gender identity, language and postal-code edits did not change this policy's decision.
2. **Temporal leakage (1).** After `path_20250201_egfr` was re-dated to 2025-02-22, past the decision date, the policy still cited it (`fuzz_temporal_011`). Consequence: reliance on information unavailable at decision time, which invalidates retrospective validation claims.
3. **Clinical insensitivity (3).** Adding a pre-decision eGFR 24, LVEF 38% or troponin I 2.4 ng/mL result (`fuzz_clinical_014`, `_015`, `_017`) left the recommendation at `eligible`. Consequence: a documented guideline stop signal is ignored. The heuristic shares these three; both policies did respond to the ANC 400 finding and neither was misled by the injected future biopsy, pathology and culture results beyond the single re-dating case above.

At the contract level, failures cluster as incorrect safety-critical decisions (36 of the heuristic's 40 failures and 58 of the reckless policy's 61 are rated `high` severity under the benchmark's rule-based severity scheme), followed by evidence-only failures (4 and 3 `low`).

## 8. Discussion: Deployment Guardrails

Contract tests suggest concrete guardrails: (i) regression-gate every model or prompt release on the full contract suite, with zero tolerance for IFR > 0 on payer and demographic attributes; (ii) enforce decision-time filtering of inputs at the data-access layer rather than relying on the model, and audit citations for post-decision items; (iii) require deterministic decoding (temperature 0 / greedy) during evaluation so failures are reproducible; (iv) treat SDI, not mean accuracy, as the release criterion for safety-critical decisions; (v) retain machine-readable run metadata (dataset fingerprint, seed) for governance audit. The fuzzer complements fixed contracts by exploring perturbations near a site's own charts; findings are marked `needs_human_review` and are not clinical adjudications.

## 9. Limitations

- **Baseline-only evaluation.** Only three offline policies were run. No LLM (including the supported BioMistral, Meditron, MedGemma, Llama, Mistral and Qwen families, or OpenAI-compatible endpoints) was evaluated; those adapters are implemented and tested offline with mocked pipelines and responses, so conclusions about real models cannot be drawn.
- **Synthetic, unvalidated contracts.** Contracts are author-generated, templated, and not clinician-reviewed or guideline-certified; heuristic rules were written with knowledge of 32 of the contracts. Ground truth is therefore a design decision, and real-chart complexity (noise, missing data, free text length) is absent.
- **Reference policies are artificial.** The reckless policy was constructed to fail; its rates quantify benchmark sensitivity, not the prevalence of these failures in practice.
- **Small samples.** IFR and TDV rest on 23 contracts each; intervals are wide, and the bootstrap treats the finite contract set as the sampling unit.
- **Fuzzer scope.** One base chart, 20 perturbations, one specialty; the findings illustrate the method.
- **Metric simplifications.** SDI weights (3:1) are a design choice; TDV counts decision changes and leakage but not correct-but-late reasoning.
- **Licensing and use.** DiffEHR is not a medical device or decision-support tool.

## 10. Conclusion

DiffEHR turns clinical-AI behavioral expectations into executable, versioned contracts over synthetic FHIR records. On 120 contracts, an oracle passes all, a tuned heuristic generalizes poorly outside its tuning set, and a flawed policy shows payer sensitivity, temporal leakage and clinical insensitivity that the metrics and fuzzer identify and localize. Evaluating real clinical language models and obtaining clinician review of the contracts are the immediate next steps.

## Data and Code Availability

Code, contracts, run outputs and reports: https://github.com/zoryktom/diffehr (Apache-2.0). Reproduce with `pip install -e '.[dev]'`, `pytest -v`, `bash scripts/run_all_benchmarks.sh`. No real patient data were used.

## Ethics

No human subjects or identifiable data; all records are synthetic. Misuse risk is limited, but benchmark success must not be read as clinical safety.

## References

1. Ribeiro MT, Wu T, Guestrin C, Singh S. Beyond Accuracy: Behavioral Testing of NLP Models with CheckList. ACL 2020:4902-4912.
2. Obermeyer Z, Powers B, Vogeli C, Mullainathan S. Dissecting racial bias in an algorithm used to manage the health of populations. Science 2019;366(6464):447-453.
3. Kusner MJ, Loftus J, Russell C, Silva R. Counterfactual fairness. NeurIPS 2017.
4. Walonoski J, et al. Synthea: An approach, method, and software mechanism for generating synthetic patients and the synthetic electronic health care record. JAMIA 2018;25(3):230-238.
5. HL7 International. FHIR Release 4 (v4.0.1). 2019.
6. Efron B. Bootstrap methods: another look at the jackknife. Ann Stat 1979;7(1):1-26.

BibTeX entries are in `docs/CITATIONS.bib`.
