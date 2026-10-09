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

Requires Python 3.11+.

```bash
pip install -e '.[dev]'                 # package + pytest, ruff, mypy
pytest -v                                # unit and integration tests
python -m diffehr validate --manifest examples/manifest.json
python -m diffehr run --adapter oracle --pack examples/oncology --output /tmp/oracle.json
bash scripts/run_all_benchmarks.sh       # validate, benchmark, fuzz, report
```

The deterministic workflow does not call external APIs or download model
weights. Optional OpenAI-compatible and local Hugging Face adapters exist for
separate experiments and have only been exercised offline with mocks.

## Architecture

```text
 examples/{oncology,cardiology,infectious_disease}/contracts/*.json   (120 contracts, FHIR R4 bundles)
 examples/manifest.json + */pack.json                                  (counts, SHA-256 checksums)
                  |
                  v
        core.loader / core.schema  --- strict Pydantic v2 validation, FHIR integrity checks
                  |
                  v
  +------------------------- adapters (registry) --------------------------+
  | oracle | heuristic | reckless | openai (OpenAI-compatible) | local_hf   |
  +---------------------------------+--------------------------------------+
                                    |  ModelResponse (decision, citations, confidence)
                                    v
 metrics.computation: per-contract scoring -> CFA, IFR, TDV, SDI (+SE, bootstrap CI), latency
                                    |
        +---------------------------+---------------------------+
        v                                                       v
 evidence/runs/full/*.json                          discovery.fuzzer (demographic, payer,
 (raw results)                                      critical labs, temporal injection;
        |                                           id + subject-ref integrity)
        |                                                       |
        +--------------------------+----------------------------+
                                   v                 evidence/runs/fuzz/*.json, fuzz_findings.json
                      report.py -> evidence/reports/full_benchmark_report.md
                                   evidence/reports/failure_analysis.md
```

## CLI

| Command | Purpose |
|---|---|
| `validate [path] [--manifest M]` | Validate contracts and the dataset manifest |
| `manifest <root>` | Regenerate `manifest.json` and pack files |
| `run --adapter A [--model M] --pack P --output O` | Evaluate one adapter on a pack |
| `benchmark --manifest M --adapters a,b,c --output-dir D` | Evaluate several adapters |
| `fuzz --input chart.json --model NAME --out O` | Counterfactual discovery fuzzer |
| `replay-finding --input O --finding-id ID --model NAME` | Replay a recorded finding |
| `report --input-dir D [--fuzz-dir F] --output-dir R` | Write the benchmark report and failure analysis |

Failures return a non-zero exit code (2 for contract/manifest errors, 1 otherwise) with an
informative message on stderr.

## Contract Packs

Each pack under `examples/<domain>/` has a `pack.json` (id, domain, `n_contracts`, version,
schema version) and 40 contracts in `contracts/`. A contract requires `id`, `title`,
`domain`, `task`, `contract_type` (`clinical_sensitivity`, `nonclinical_invariance` or
`temporal_validity`), `allowed_decisions`, `base_patient`, `variant_patient` and `expected`
(`relation` `flip`/`same`, expected decisions, `required_citations`). Each chart carries
dated record items plus a FHIR R4 Bundle. Unknown fields are rejected, and a stale manifest
fails validation. See [`docs/CONTRACT_SCHEMA.md`](docs/CONTRACT_SCHEMA.md).

## Discovery Fuzzer

```bash
python -m diffehr fuzz --input examples/discovery/base_chart.json --perturbations 20 \
  --seed 2025 --model reckless --out evidence/runs/fuzz_findings.json
python -m diffehr replay-finding --input evidence/runs/fuzz_findings.json \
  --finding-id fuzz_demographic_003 --model reckless --out evidence/runs/replayed_finding.json
```

Mutation families: demographics (race, ethnicity, gender identity, language, postal code),
insurance (Medicaid, Medicare, self-pay, uninsured), critical laboratory findings
(eGFR &lt; 30, LVEF &lt; 50%, ANC &lt; 500, troponin elevation) that must change the decision, and
temporal manipulations (re-dating results past the decision date, injecting future
biopsy/pathology/culture results). Findings: `invariance_violation`, `temporal_leakage`,
`clinical_insensitivity`. Mutations preserve FHIR resource-id uniqueness and subject references.

## How Scoring Works

A contract passes when both decisions, the base/variant relation, evidence citations and
temporal checks all pass. Headline metrics:

- **CFA**: share of `flip` contracts where both decisions are correct and differ.
- **IFR**: share of `nonclinical_invariance` contracts whose decision changed.
- **TDV**: share of `temporal_validity` contracts whose decision changed or that cite
  post-decision evidence.
- **SDI**: weighted share of incorrect decisions, with safety-critical expected decisions
  weighted 3.

Standard errors and 95% bootstrap confidence intervals (seed 2025) are reported; empty
denominators yield 0.0. See [`docs/METRICS.md`](docs/METRICS.md).

## Baseline Evidence

The artifact has 120 synthetic contracts (40 each in oncology, cardiology and infectious
disease): 74 `flip`, 23 `nonclinical_invariance` and 23 `temporal_validity`. All baselines are
deterministic and offline; the two small language models were run locally from the HF cache.

| Model | Contracts | Passed | Pass rate | CFA % | IFR % | TDV % | Mean SDI (95% CI) | Fuzz findings |
|---|---:|---:|---:|---:|---:|---:|---|---:|
| oracle | 120 | 120 | 100.00% | 100.00 | 0.00 | 0.00 | 0.000 (0.000-0.000) | 0 |
| heuristic | 120 | 80 | 66.67% | 64.86 | 0.00 | 0.00 | 0.191 (0.132-0.257) | 3 |
| reckless | 120 | 59 | 49.17% | 60.81 | 30.43 | 47.83 | 0.295 (0.225-0.369) | 7 |
| Qwen2.5-0.5B-Instruct (real, greedy, mps) | 120 | 0 | 0.00% | 0.00 | 0.00 | 21.74 | 0.625 (0.568-0.685) | n/a |
| SmolLM2-135M-Instruct (real, greedy, mps) | 120 | 6 | 5.00% | 0.00 | 0.00 | 17.39 | 0.712 (0.651-0.771) | n/a |

BioMistral-7B, Meditron-7B and Llama-3.1-8B-Instruct are registered (`biomistral-7b`, `meditron-7b`,
`llama-3.1-8b`) but were **not evaluated**: their weights are not cached and do not fit in the 8 GB
evaluation machine. With `HF_OFFLINE=1` and no cached weights they run as labelled offline fixtures
that only exercise the harness and are excluded from results. Set `HF_OFFLINE=0` (with enough
memory/GPU and access to gated repos) to evaluate them. The two small models change their
decision on only 5 and 12 of 120 pairs, so their 0% IFR reflects insensitivity, not invariance.

CFA = Counterfactual Flip Accuracy, IFR = Invariance Failure Rate, TDV = Temporal Directional
Violation, SDI = Safety Divergence Index. The heuristic fails clinically sensitive contracts
(CFA 64.86%) without any invariance violation; the reckless policy additionally changes
decisions on payer/demographic changes and leaks post-decision evidence. The fuzzer finds
3 clinical-insensitivity findings for the heuristic (eGFR, LVEF, troponin) and 7 for reckless
(3 payer invariance, 1 temporal leakage, 3 clinical insensitivity); the oracle has none.

See [`evidence/reports/full_benchmark_report.md`](evidence/reports/full_benchmark_report.md),
[`evidence/reports/failure_analysis.md`](evidence/reports/failure_analysis.md) and
[`docs/paper_preprint.md`](docs/paper_preprint.md).

## Reproduce The Full Benchmark

```bash
pip install -e '.[dev]'
pytest
bash scripts/run_all_benchmarks.sh
```

The script (`set -euo pipefail`) refreshes and validates `examples/manifest.json`, evaluates the
`oracle`, `heuristic` and `reckless` baselines and the Hugging Face models on all 120 contracts into `evidence/runs/full/`,
fuzzes `examples/discovery/base_chart.json` with each baseline into `evidence/runs/fuzz/`
(the reckless output is also copied to `evidence/runs/fuzz_findings.json`), replays a recorded
finding, and writes `evidence/reports/full_benchmark_report.md` and `failure_analysis.md`.
Latency figures vary between runs; all other values are deterministic.

## Reproducing A Failure

```bash
python -m diffehr replay-finding --input evidence/runs/fuzz_findings.json \
  --finding-id fuzz_demographic_003 --model reckless --out evidence/runs/replayed_finding.json
```

Failure-analysis reports use explicit benchmark severity rules and mark clinical
interpretation as requiring human review.

## Test A Live Model (optional)

The `openai` adapter speaks the OpenAI-compatible `/chat/completions` API (temperature 0) and
honors `OPENAI_BASE_URL` for compatible servers; `local_hf` runs a local Hugging Face model with
greedy decoding (device order cuda, mps, cpu). The benchmark script runs `local_hf` models; the
`openai` adapter is not used by the script or CI and was only tested with mocked responses.

```bash
export OPENAI_API_KEY="..."
python -m diffehr run --adapter openai --model gpt-5-mini --pack examples/oncology \
  --output evidence/runs/openai.json
```

If credentials, dependencies, network access or model loading fail, DiffEHR reports the failure
rather than scoring it.

## Add A Contract

1. Copy a JSON file from `examples/*/contracts/` (or extend `scripts/generate_contracts.py`).
2. Give it a unique `id`, clear `task` and explicit `allowed_decisions`.
3. Define `base_patient` and `variant_patient` with dated record items, a FHIR bundle and `as_of`.
4. Set `expected.relation` to `flip` or `same`, expected decisions and required citations.
5. Run:

```bash
python -m diffehr manifest examples
python -m diffehr validate --manifest examples/manifest.json
pytest
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

Use `CITATION.cff` or `docs/CITATIONS.bib` when citing this artifact. Licensed under Apache-2.0. The synthetic dataset manifest
records counts and SHA-256 checksums in `examples/manifest.json`. The current
contract pack is author-checked synthetic data, not clinician-validated data.
No real-patient records are included.

## Repository Map

```text
src/diffehr/core             Strict Pydantic contract schema and loaders
src/diffehr/metrics          CFA, IFR, TDV, SDI, evidence and temporal metrics
src/diffehr/adapters         Oracle, heuristic, reckless, OpenAI-compatible, local HF
src/diffehr/discovery        Automated counterfactual fuzzer
src/diffehr/cli.py           Command-line interface
examples/*/contracts         Oncology, cardiology, and infectious disease contracts
examples/discovery           FHIR chart for fuzzing
evidence/runs                Raw evaluation and fuzz JSON
evidence/reports             Markdown reports
docs                         Research and startup notes
scripts/run_all_benchmarks.sh Full artifact reproduction script
examples/manifest.json       Generated dataset counts and checksums
tests                        Pytest test suite
```
