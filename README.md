# DiffEHR

**Counterfactual contract testing for clinical AI systems.**

DiffEHR is an open-source research artifact for testing whether clinical AI
systems change their answers for the right reasons. It creates paired synthetic
EHR cases where exactly one clinically meaningful or clinically irrelevant thing
changes, then scores whether an AI system satisfies the expected behavioral
contract.

The core idea:

> Clinical AI should flip its answer when a decisive biomarker changes, stay
> stable when insurance or race changes, ignore future evidence, and cite the
> chart items that justify its decision.

DiffEHR is designed to become **unit testing for clinical AI**.

## Why This Exists

Static benchmark accuracy can hide dangerous behavior. A model can answer a case
correctly once while still failing deployment-relevant tests:

- ignoring a decisive biomarker
- overreacting to payer status or demographic attributes
- using chart evidence that was not available at the decision date
- changing behavior after a model update
- failing to cite the exact record evidence behind a decision

DiffEHR tests these behaviors directly with **clinical counterfactual
contracts**.

## What Is A Contract?

A DiffEHR contract contains:

- a base synthetic patient chart
- a variant chart with one controlled change
- a task
- allowed output decisions
- expected base and variant decisions
- required evidence citations
- temporal restrictions
- scoring rules

Example contract concept:

```text
Base:    metastatic NSCLC, EGFR negative
Variant: same chart, EGFR exon 19 deletion positive
Task:    determine eligibility for an EGFR trial
Expected: base=ineligible, variant=eligible
```

## Quick Start

```bash
cd diffehr
python -m pip install -e '.[test]'
PYTHONPATH=src python3 -m diffehr validate examples/oncology/contracts
PYTHONPATH=src python3 -m diffehr validate examples
PYTHONPATH=src python3 -m diffehr evaluate examples --model oracle --out evidence/runs/oracle.json
PYTHONPATH=src python3 -m diffehr evaluate examples --model reckless-oncology --out evidence/runs/reckless.json
PYTHONPATH=src python3 -m diffehr fuzz --input examples/discovery/base_chart.json --perturbations 20 --model reckless-oncology --out evidence/runs/fuzz_findings.json
scripts/run_all_benchmarks.sh
```

## Baseline Evidence

The multi-specialty artifact includes 32 contracts across oncology,
cardiology, and infectious disease. It covers biomarker sensitivity, ECOG
eligibility, payer/race/language/setting invariance, cardiology medication
selection, antimicrobial stewardship, medication safety, and temporal validity.

| Model | Contracts | Passed | Pass rate | Mean score |
|---|---:|---:|---:|---:|
| oracle | 32 | 32 | 100.00% | 1.000 |
| heuristic-oncology | 32 | 32 | 100.00% | 0.999 |
| reckless-oncology | 32 | 24 | 75.00% | 0.877 |

The run JSON also reports invariance violation rate (IVR), decisive
sensitivity score (DSS), evidence citation precision/recall, temporal leakage
counts, and 95% bootstrap confidence intervals for IVR and DSS. The reckless
baseline reaches IVR 50.00% and 5 temporal leakage violations on the 32-contract
suite.

See [`evidence/reports/full_benchmark_report.md`](evidence/reports/full_benchmark_report.md)
and [`docs/paper_preprint.md`](docs/paper_preprint.md).

## Test A Live OpenAI Model

DiffEHR includes an OpenAI Responses API adapter. Set an API key and use any
model available to your account:

```bash
export OPENAI_API_KEY="..."
PYTHONPATH=src python3 -m diffehr evaluate examples --model openai:gpt-5-mini --out evidence/runs/openai-gpt-5-mini.json
PYTHONPATH=src python3 -m diffehr report evidence/runs/openai-gpt-5-mini.json --out evidence/reports/openai-gpt-5-mini.md
```

If `gpt-5-mini` is not available in your account, replace it with another model
identifier.

## Research Positioning

DiffEHR is not another synthetic patient dataset. It is a **counterfactual
testing language and engine** for clinical AI behavior.

The first paper can be framed as:

> **DiffEHR: Counterfactual Contract Testing for Clinical AI Systems on
> Longitudinal Synthetic Health Records**

Core hypothesis:

> Clinical AI systems can appear accurate on static cases while failing
> counterfactual contracts: ignoring decisive clinical changes, overreacting to
> irrelevant non-clinical attributes, or using temporally unavailable evidence.

## Startup Positioning

DiffEHR can become a clinical AI QA and regression-testing platform:

```bash
diffehr test --model vendor-model --pack oncology
```

Potential users:

- health AI startups testing model releases
- hospital AI governance teams evaluating vendors
- clinical informatics labs benchmarking systems
- biomedical informatics courses teaching AI evaluation
- journals or reviewers checking reproducibility artifacts

## Safety And Intended Use

DiffEHR uses synthetic data and is intended for research, software testing, and
education. It is **not** a clinical decision support system, medical device,
diagnostic tool, or substitute for clinician judgment.

## Repository Map

```text
src/diffehr/core             Strict Pydantic contract schema and loaders
src/diffehr/metrics          IVR, DSS, evidence, and temporal metrics
src/diffehr/adapters         Oracle, heuristic, OpenAI, and local HF adapters
src/diffehr/discovery        Automated counterfactual fuzzer
src/diffehr/cli.py           Command-line interface
examples/*/contracts         Oncology, cardiology, and infectious disease contracts
examples/discovery           FHIR chart for fuzzing
evidence/runs                Reproducible evaluation JSON
evidence/reports             Markdown reports
docs                         Research and startup notes
scripts/run_all_benchmarks.sh Full artifact reproduction script
tests                        Pytest test suite
```
