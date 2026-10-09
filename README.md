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
PYTHONPATH=src python3 -m pytest tests/ -q
PYTHONPATH=src python3 -m diffehr validate examples/oncology/contracts
PYTHONPATH=src python3 -m diffehr manifest examples
PYTHONPATH=src python3 -m diffehr validate examples
PYTHONPATH=src python3 -m diffehr evaluate examples --model oracle --out evidence/runs/oracle.json
PYTHONPATH=src python3 -m diffehr evaluate examples --model reckless-oncology --out evidence/runs/reckless.json
PYTHONPATH=src python3 -m diffehr fuzz --input examples/discovery/base_chart.json --perturbations 20 --model reckless-oncology --out evidence/runs/fuzz_findings.json
PYTHONPATH=src python3 -m diffehr failures evidence/runs/reckless.json --out evidence/reports/failure_analysis.md
scripts/run_all_benchmarks.sh
```

The deterministic workflow does not call external APIs or download model
weights. Optional OpenAI and local-HF adapters are available for separate
experiments.

## How Scoring Works

DiffEHR separates several behaviors that static accuracy tends to collapse:

- **Contract pass rate**: fraction of contracts where both decisions, the
  base/variant relation, evidence citations, and temporal checks all pass.
- **DSS**: decisive sensitivity score, the fraction of `flip` contracts where
  the model changes decision for the expected clinical reason.
- **IVR**: invariance violation rate, the fraction of `same` contracts where
  the model unexpectedly changes decision.
- **Evidence precision/recall**: whether cited record IDs match required
  evidence IDs.
- **Temporal leakage**: cited evidence whose chart date is after the decision
  index timestamp.

See [`docs/METRICS.md`](docs/METRICS.md) for formulas, denominators, and edge
case behavior.

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

## Reproduce The Full Benchmark

```bash
python -m pip install -e '.[test]'
PYTHONPATH=src python3 -m pytest tests/ -q
scripts/run_all_benchmarks.sh
```

The script validates all contract packs, refreshes `examples/manifest.json`,
runs deterministic baselines, writes JSON results under `evidence/runs/full/`,
generates `evidence/reports/full_benchmark_report.md`, generates
`evidence/reports/failure_analysis.md`, runs bounded fuzzing, and replays one
recorded finding. Run metadata includes the DiffEHR version, Python version,
adapter, contract IDs, dataset version, dataset fingerprint, timestamp, and
bootstrap seed.

## Reproducing A Failure

Run the benchmark, then inspect or replay a recorded finding:

```bash
scripts/run_all_benchmarks.sh
PYTHONPATH=src python3 -m diffehr replay-finding --input evidence/runs/fuzz_findings.json --finding-id fuzz_demographic_003 --model reckless-oncology --out evidence/runs/replayed_finding.json
```

Failure-analysis reports use explicit benchmark severity rules and mark clinical interpretation as requiring human review.

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

External-model results are not part of the deterministic baseline evidence in
this repository. If provider credentials, dependencies, network access, or model
loading fail, DiffEHR reports the invocation failure instead of treating it as a
successful evaluation.

## Add A Contract

1. Copy an existing JSON file from `examples/*/contracts/`.
2. Give it a unique `id`, clear `task`, and explicit `allowed_decisions`.
3. Define `base_patient` and `variant_patient` with dated record items and an
   `as_of` decision date.
4. Set `expected.relation` to `flip` or `same`, expected decisions, and required
   citation IDs.
5. Add provenance, known limitations, and safety-critical notes where relevant.
6. Run:

```bash
PYTHONPATH=src python3 -m diffehr manifest examples
PYTHONPATH=src python3 -m diffehr validate examples
PYTHONPATH=src python3 -m pytest tests/ -q
```

Schema details are in [`docs/CONTRACT_SCHEMA.md`](docs/CONTRACT_SCHEMA.md).

## Add An Adapter

Implement `ModelAdapter.answer(contract, side)` and return a `ModelResponse`.
Adapters should emit one of the contract's allowed decisions, citation IDs,
rationale text, and confidence. Malformed or unavailable external model outputs
should raise explicit errors or parse to `unknown`; they must not silently
improve scores. Register the adapter in `src/diffehr/adapters/registry.py` and
add offline tests with mocked responses.

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

## Reproducibility And Citation

Use `CITATION.cff` when citing this artifact. The synthetic dataset manifest
records counts and SHA-256 checksums in `examples/manifest.json`. The current
contract pack is author-checked synthetic data, not clinician-validated data.
No real-patient records are included.

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
examples/manifest.json       Generated dataset counts and checksums
tests                        Pytest test suite
```
