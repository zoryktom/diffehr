# DiffEHR: Counterfactual Contract Testing for Clinical AI Systems on Synthetic FHIR Records

## Abstract

Clinical AI systems are often evaluated on static question-answering or case-vignette benchmarks, which can miss whether a system changes behavior for the right clinical reasons. We introduce DiffEHR, an executable research artifact for counterfactual contract testing on paired synthetic health records. Each contract defines a base chart, a controlled counterfactual variant, a clinical task, allowed decisions, an expected behavioral relation, required evidence citations, and temporal constraints at a decision index timestamp. We evaluate three baselines across 32 contracts spanning oncology, cardiology, and infectious disease. The oracle baseline passed 32/32 contracts with mean score 1.000. A temporally careful heuristic passed 32/32 with mean score 0.999. A reckless baseline that overreacts to payer status and ignores decision-time availability passed 24/32 with mean score 0.877, an invariance violation rate of 50.00% and 5 temporal leakage violations. Automated fuzzing over a FHIR chart generated 20 perturbations and identified 3 distinct findings after deduplication: 2 payer-driven invariance violations and 1 future-evidence leakage case. These results show that counterfactual contract testing can expose deployment-relevant failures that static accuracy alone would obscure.

## Introduction

Clinical AI evaluation has focused heavily on static performance: a model is asked a clinical question, and the answer is scored for correctness. Static benchmarks are useful, but they do not directly test whether the model is using the right evidence, ignoring the wrong evidence, or respecting the timestamp at which a decision is made. In practice, a model can answer a chart correctly once while still failing clinically important behavioral requirements.

DiffEHR reframes clinical AI evaluation as executable counterfactual contracts. A contract pairs a base synthetic record with a minimally changed variant. The change can be clinically decisive, such as a biomarker becoming positive, or clinically irrelevant, such as payer status or race. The model is expected either to flip its answer or remain invariant. The contract also specifies required evidence citations and disallows evidence dated after the decision index.

This artifact contributes a multi-specialty benchmark, a strict schema, a metrics engine, adapter interfaces, an automated fuzzer, and reproducible reports. It is intended for research, regression testing, and governance workflows, not for clinical decision support.

## Research Questions

- RQ1: Can DiffEHR detect predefined violations of clinical behavior contracts in controlled synthetic experiments?
- RQ2: How do decisive sensitivity and irrelevant-attribute invariance vary across deterministic baselines?
- RQ3: What failure modes are revealed by evidence-grounding and temporal-validity checks?
- RQ4: Are deterministic evaluations reproducible from checked-in contracts and scripts?
- RQ5: What limitations prevent synthetic contract-test performance from establishing real-world clinical reliability?

## Background And Related Work

Medical AI benchmarks such as exam-style multiple-choice tasks and clinical QA datasets measure important aspects of medical knowledge. However, they typically evaluate isolated answers rather than behavioral stability under controlled chart edits. Software testing offers a complementary framing: properties can be encoded as tests that must continue passing as systems evolve. DiffEHR applies this idea to synthetic FHIR-style clinical records, making counterfactual behavior inspectable and reproducible.

The closest methodological family is metamorphic testing: a system should satisfy expected relations between outputs under controlled input transformations. DiffEHR specializes this approach for clinical AI by encoding clinical tasks, paired records, evidence IDs, temporal constraints, and specialty-specific expected behavior. DiffEHR uses FHIR R4-style JSON for chart representation, but does not claim conformance to a complete production FHIR profile.

## Problem Formulation

The problem is not to prove that a clinical AI system is safe. The narrower question is whether a system satisfies explicitly defined behavior contracts on synthetic paired records. A failure means the model violated a benchmark assertion; it does not by itself quantify patient harm or clinical deployment risk.

## DiffEHR Methodology

### Contract Definition

A DiffEHR contract is a tuple:

```text
C = (B, V, T, A, R, E, tau)
```

where `B` is the base chart, `V` is the counterfactual variant chart, `T` is the clinical task, `A` is the set of allowed decisions, `R` is the expected relation, `E` is the required evidence set, and `tau` is the decision index timestamp.

DiffEHR supports two primary behavioral relations:

- `MustFlip`: the model decision must change between base and variant.
- `MustRemainInvariable`: the model decision must remain unchanged.

Each chart is represented as strict Pydantic v2 models with FHIR R4-style JSON compatibility. Records contain dated chart items, demographic attributes, optional FHIR resources, and a decision `as_of` timestamp. Evidence citations are chart item IDs.

## Contract Schema And Counterfactual Construction

Contracts are versioned JSON objects validated by strict Pydantic models. The dataset manifest records counts and SHA-256 checksums for the checked-in contracts. Counterfactual integrity checks summarize observed differences between base and variant records as single-factor, multifactor/dependent representation, or none. This structural summary supports auditability, but it does not replace clinical review.

## Evaluation Metrics

DiffEHR reports contract pass rate and four research metrics.

Invariance Violation Rate:

```text
IVR = unexpected flips on invariant pairs / total invariant pairs
```

Decisive Sensitivity Score:

```text
DSS = expected flips on decisive pairs with correct side decisions / total decisive pairs
```

Citation attribution precision and recall:

```text
precision = |observed citations intersect required citations| / |observed citations|
recall    = |observed citations intersect required citations| / |required citations|
```

Temporal Leakage Violation Rate:

```text
TLVR = citations with evidence_t > decision_t / total observed citations
```

For IVR and DSS, DiffEHR computes deterministic 95% percentile bootstrap confidence intervals by resampling contracts with replacement.

## Benchmark Design

The benchmark contains exactly 32 paired synthetic contracts:

| Specialty | Contracts | Clinical sensitivity | Invariance | Temporal validity |
|---|---:|---:|---:|---:|
| Oncology | 16 | 8 | 4 | 4 |
| Cardiology | 8 | 4 | 3 | 1 |
| Infectious disease | 8 | 4 | 2 | 2 |
| Total | 32 | 16 | 9 | 7 |

The three evaluated baselines were:

- Oracle: returns hidden expected decisions and evidence IDs.
- Heuristic: rule-based, respects decision timestamps, and ignores non-clinical attributes.
- Reckless: rule-based, ignores temporal visibility and overreacts to payer status.

## Experimental Setup

The full reproducible report is generated by:

```bash
scripts/run_all_benchmarks.sh
```

The deterministic run requires no API keys, internet access, or downloaded model weights. Optional OpenAI and local-HF adapters are available but were not used for the reported deterministic results.

## Results

### Overall Performance

| Model | Contracts | Passed | Pass rate | Mean score |
|---|---:|---:|---:|---:|
| oracle | 32 | 32 | 100.00% | 1.000 |
| heuristic-oncology | 32 | 32 | 100.00% | 0.999 |
| reckless-oncology | 32 | 24 | 75.00% | 0.877 |

### Research Metrics

| Model | IVR | IVR 95% CI | DSS | DSS 95% CI | Evidence precision | Evidence recall | Temporal leakage |
|---|---:|---:|---:|---:|---:|---:|---:|
| oracle | 0.00% | 0.00%-0.00% | 100.00% | 100.00%-100.00% | 100.00% | 100.00% | 0 |
| heuristic-oncology | 0.00% | 0.00%-0.00% | 100.00% | 100.00%-100.00% | 98.88% | 100.00% | 0 |
| reckless-oncology | 50.00% | 25.00%-75.00% | 100.00% | 100.00%-100.00% | 88.76% | 89.77% | 5 |

The reckless baseline preserved decisive clinical sensitivity but failed invariance and temporal validity. This demonstrates why static decision accuracy is not sufficient: the same model can respond correctly to clinically meaningful changes while also overreacting to payer status or using unavailable future information.

### Failure Case Analysis

The highest violation rates were in temporal-validity categories. Reckless failed 100.00% of cardiology temporal contracts and 75.00% of oncology temporal contracts. It also failed non-clinical invariance contracts in cardiology, infectious disease, and oncology due to payer bias.

Representative failures included:

- Cardiology: future troponin created a statin indication before NSTEMI was confirmed at the decision index.
- Infectious disease: future culture susceptibility caused premature carbapenem de-escalation.
- Oncology: future EGFR or LVEF evidence changed eligibility despite being dated after the decision index.
- Fuzzing: payer mutations to Medicaid or self-pay flipped an EGFR trial eligibility answer with unchanged clinical evidence.

### Automated Counterfactual Discovery

DiffEHR includes a fuzzer that mutates non-clinical demographic attributes and shifts FHIR resource dates into the future. Against the reckless baseline, the fuzzer ran 20 perturbations and found 3 distinct failures after deduplicating equivalent findings:

| Finding type | Count |
|---|---:|
| Invariance violation | 2 |
| Temporal leakage | 1 |

The fuzz run is stored at `evidence/runs/fuzz_findings.json`.

## Ablation And Robustness Analysis

The deterministic baselines serve as practical ablations of framework claims:

| Comparison | What changes | Expected diagnostic result | Observed result |
|---|---|---|---|
| Oracle vs heuristic | Hidden contract fixture vs transparent rules | Both should pass if evaluator and rules match contracts | Both passed 32/32 |
| Heuristic vs reckless | Temporal visibility and payer-invariance disabled in reckless | Reckless should fail temporal and invariance checks | Reckless passed 24/32, IVR 50.00%, 5 temporal leaks |
| Fuzz demographic perturbations | Non-clinical payer fields changed | Reckless should reveal payer-driven flips | 2 deduplicated invariance findings |
| Fuzz temporal perturbations | Evidence dates shifted after decision index | Reckless should cite future evidence | 1 deduplicated temporal finding |

These ablations show that the evaluation engine detects the intentionally introduced failure modes. They do not establish performance for a real clinical model.

## Error Analysis

The checked-in failure-analysis report is generated at `evidence/reports/failure_analysis.md`. It assigns severity by explicit benchmark rules:

- high: temporal leakage, safety-related expected decisions, or incorrect task decisions,
- medium: relation failures without temporal or safety markers,
- low: evidence-only failures.

All failures require human review before clinical interpretation.

## Threats To Validity

The benchmark is synthetic and deliberately constructed. It is not a random sample of clinical cases. The deterministic baselines are not real clinical AI systems. Evidence matching uses record IDs and does not independently judge semantic truth. Confidence intervals are conditional on the benchmark and bootstrap scheme. Contract rationales are author-specified and should be reviewed before use as a validated benchmark.

## Ethical Considerations

DiffEHR is designed to reduce risk in evaluation workflows by making failure modes visible on synthetic records. It must not be used as clinical decision support. It should not be used to make claims about patient outcomes, model safety, or fairness in deployment without additional validation, governance, and clinician review.

## Reproducibility Statement

The deterministic artifact can be reproduced with:

```bash
python -m pip install -e '.[test]'
PYTHONPATH=src pytest tests/ -q
PYTHONPATH=src python -m diffehr manifest examples
PYTHONPATH=src python -m diffehr validate examples
scripts/run_all_benchmarks.sh
```

Machine-readable outputs are in `evidence/runs/`. Human-readable reports are in `evidence/reports/`. Dataset integrity is recorded in `examples/manifest.json`.

## Discussion

DiffEHR shows that clinical AI evaluation can be made more operational by encoding behavioral expectations as executable contracts. The multi-specialty suite tests whether models flip on decisive clinical facts, remain invariant to non-clinical attributes, cite the responsible evidence, and avoid future information.

The empirical results are intentionally small enough to inspect by hand but broad enough to exercise three specialties and multiple failure modes. The reckless baseline illustrates a clinically important pattern: high decisive sensitivity can coexist with poor invariance and temporal reliability. This is the kind of failure that a static benchmark can miss.

## Clinical Safety Implications

Counterfactual contract testing can support:

- model release regression tests,
- vendor evaluation by health systems,
- clinical informatics research on robustness,
- audit trails for evidence citation behavior,
- educational demonstrations of temporal leakage and demographic bias.

Because the artifact uses synthetic data, it can be shared, inspected, and extended without exposing patient information.

## Limitations

The current contract pack is synthetic and compact. It does not establish real-world clinical safety, and it is not a substitute for clinician review, prospective validation, or deployment monitoring. The heuristic baselines are deliberately simple and should not be interpreted as clinical systems. Future work should expand contract volume, add clinician-authored validation, evaluate frontier LLMs and vendor systems, and measure inter-rater agreement on expected contract behavior.

## Conclusion

DiffEHR operationalizes clinical counterfactual testing as a reproducible software artifact. Across 32 contracts, it distinguishes a careful baseline from a reckless baseline despite both showing strong decisive sensitivity. The artifact provides a foundation for rigorous, inspectable, multi-specialty evaluation of clinical AI behavior.

## References

- Chen, T. Y., Cheung, S. C., and Yiu, S. M. 1998. *Metamorphic Testing: A New Approach for Generating Next Test Cases*. Technical Report HKUST-CS98-01. https://www.cse.ust.hk/faculty/scc/publ/CS98-01-metamorphictesting.pdf
- Segura, S., Fraser, G., Sanchez, A. B., and Ruiz-Cortes, A. 2016. *A Survey on Metamorphic Testing*. IEEE Transactions on Software Engineering, 42(9), 805-824. https://doi.org/10.1109/TSE.2016.2532875
- HL7. *FHIR Release 4, Bundle Resource*. https://hl7.org/fhir/R4/bundle.html
- U.S. Food and Drug Administration. 2022. *Clinical Decision Support Software: Guidance for Industry and Food and Drug Administration Staff*. https://www.fda.gov/media/109618/download

These references establish nearby technical and regulatory context. They do not constitute a comprehensive literature review or external clinical validation of DiffEHR.
