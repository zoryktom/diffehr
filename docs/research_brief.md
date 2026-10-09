# DiffEHR Research Brief

## Working Title

**DiffEHR: Counterfactual Contract Testing for Clinical AI Systems on
Longitudinal Synthetic Health Records**

## Abstract Draft

Clinical AI systems are increasingly evaluated on static question-answering,
summarization, or task-completion benchmarks. These evaluations can miss a
deployment-critical question: does the system change its behavior for the right
clinical reasons? We introduce DiffEHR, an open-source framework for
counterfactual contract testing of clinical AI systems using paired synthetic
EHRs. Each contract specifies a base patient record, a minimally changed variant
record, the expected output relation, required evidence citations, and temporal
validity constraints. We demonstrate a 32-contract multi-specialty benchmark
covering oncology, cardiology, and infectious disease, including biomarker
sensitivity, medication contraindications, antimicrobial stewardship,
non-clinical invariance, and future-evidence leakage. DiffEHR reframes clinical
AI evaluation as executable behavioral contracts rather than isolated case
scores.

## Research Question

Can clinical AI systems satisfy counterfactual behavioral contracts over
longitudinal EHR records?

Subquestions:

- Do models flip decisions when clinically decisive evidence changes?
- Do models remain invariant to non-clinical attributes that should not change
  the decision?
- Do models avoid evidence that appears after the decision date?
- Do models cite the chart items that justify their decisions?
- Do model updates introduce regressions on these behaviors?

## Core Contribution

DiffEHR contributes:

1. A strict Pydantic v2 contract schema for clinical counterfactual testing.
2. A runner that evaluates arbitrary clinical AI systems through model adapters.
3. Quantitative metrics for invariance violation rate, decisive sensitivity,
   evidence citation precision/recall, and temporal leakage.
4. A 32-contract oncology, cardiology, and infectious disease corpus.
5. An automated counterfactual discovery fuzzer.
6. A reproducible evidence report and empirical preprint draft.

## Why This Is Not Just Another Benchmark

Many benchmarks ask whether a model answers a clinical case correctly. DiffEHR
asks whether the model's answer follows a clinically meaningful counterfactual
relation:

- sensitivity: answer should change
- invariance: answer should not change
- temporal validity: answer must not depend on future evidence
- evidence localization: answer must cite the responsible chart evidence

This makes DiffEHR closer to `pytest` for clinical AI behavior than to a static
leaderboard dataset.

## V0 Evidence

The current pack includes 32 contracts. A careful heuristic baseline passes all
contracts with mean score 0.999. A reckless baseline that ignores dates and
overreacts to payer status passes 24/32 contracts with mean score 0.877, IVR
50.00%, and 5 temporal leakage violations.

The current reports are stored at:

```text
evidence/reports/full_benchmark_report.md
docs/paper_preprint.md
```

## Next Experiments

1. Evaluate frontier LLMs through the OpenAI adapter.
2. Add adapters for Anthropic, local vLLM/Ollama models, and HTTP-based vendor
   endpoints.
3. Expand the multi-specialty corpus to 100+ contracts.
4. Add clinician review for contract validity.
5. Measure disagreement between static accuracy and counterfactual contract
   scores.
6. Release a preprint with code, contracts, and reproducible run artifacts.

## Submission Targets

Possible venues:

- AMIA Annual Symposium
- AMIA Informatics Summit
- Machine Learning for Health
- JAMIA Open
- Journal of Biomedical Informatics

## Statement Of Significance

DiffEHR gives biomedical informatics researchers and health AI builders a way to
test whether clinical AI systems use the right evidence, ignore the wrong
evidence, and remain reliable under controlled patient-record changes.
