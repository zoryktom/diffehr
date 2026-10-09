# DiffEHR Implementation Audit

## Date And Scope

This audit documents the repository state after the v0.2 multi-specialty artifact and the current research-grade hardening pass. It covers the local package, examples, deterministic baselines, CLI commands, generated evidence, tests, and known methodological limits.

## Current Architecture

DiffEHR is a Python package under `src/diffehr/`.

- `core/`: strict Pydantic v2 contract schema and JSON loaders.
- `metrics/`: contract scoring, IVR/DSS/evidence/temporal metrics, and deterministic bootstrap intervals.
- `adapters/`: oracle, heuristic, deliberately flawed reckless baseline, OpenAI adapter, and optional local HF adapter.
- `discovery/`: FHIR-style counterfactual fuzzer and replay support.
- `dataset.py`: generated dataset manifest, checksums, and counterfactual-difference summaries.
- `cli.py`: validation, evaluation, report, failure-analysis, manifest, fuzzing, replay, and benchmark commands.
- `examples/`: synthetic oncology, cardiology, infectious disease contracts plus one discovery FHIR chart.
- `evidence/`: generated machine-readable runs and Markdown reports.
- `scripts/run_all_benchmarks.sh`: deterministic offline reproduction script.

## Commands Checked

Baseline test command:

```bash
PYTHONPATH=src pytest tests/ -q
```

Current result:

```text
29 passed
```

Dataset validation:

```bash
PYTHONPATH=src python -m diffehr validate examples
```

Current result:

```text
Validated 32 contract(s).
```

Deterministic benchmark:

```bash
scripts/run_all_benchmarks.sh
```

Current deterministic results:

| Model | Contracts | Passed | Mean score | IVR | Temporal leakage |
|---|---:|---:|---:|---:|---:|
| oracle | 32 | 32 | 1.000 | 0.000 | 0 |
| heuristic-oncology | 32 | 32 | 0.999 | 0.000 | 0 |
| reckless-oncology | 32 | 24 | 0.877 | 0.500 | 5 |

Fuzzing currently records 20 perturbations and 3 deduplicated findings against the reckless baseline.

## Implemented Capabilities

- Strict schema validation rejects unknown fields, invalid decisions, duplicate IDs, bad dates, missing evidence references, and bad FHIR objects.
- Contract packs include exactly 32 synthetic contracts across 3 domains.
- Oracle baseline acts as a deterministic test fixture.
- Heuristic baseline is transparent and passes the deterministic suite.
- Reckless baseline intentionally exposes payer-invariance and temporal-leakage failures.
- Metrics include raw denominators and deterministic bootstrap CIs for IVR and DSS.
- Dataset manifest generation records counts and SHA-256 checksums.
- Validation checks the manifest when `examples/manifest.json` exists.
- Fuzz results record generation configuration, original and modified charts, finding status, and replay metadata.
- Failure-analysis reports show case-level failed assertions and rule-based severity.

## Methodological Weaknesses Found

- Evidence citation scoring verifies citation identifiers, not clinical semantic support. This is evidence localization, not independent clinical adjudication.
- Most contracts do not yet include external guideline citations inside the JSON contract itself. The dataset is synthetic author-checked, not clinician-validated.
- Contract provenance and review metadata are schema-supported but defaulted for backward compatibility with existing fixtures.
- API/provider failures are surfaced as command failures rather than as structured per-contract failed invocations.
- Confidence intervals are conditional on this deliberately constructed benchmark and should not be interpreted as population-level estimates.
- Fuzzer findings are confirmed relative to generated synthetic assertions, not autonomous real-world safety determinations.

## Changes Made In This Pass

- Added dataset manifest generation and manifest validation.
- Added counterfactual-difference summaries.
- Added contract provenance/review-status schema fields.
- Added run metadata to evaluation JSON.
- Added failure-analysis report generation.
- Added replayable fuzz findings and seed/config metadata.
- Added `docs/METRICS.md`, `docs/CONTRACT_SCHEMA.md`, and this audit.
- Added CI workflow and tests for manifest, metrics, fuzz replay, and failure reporting.

## Remaining Limitations

- No real LLM was evaluated in the deterministic workflow.
- No clinician review has been performed or claimed.
- No external medical references are asserted as verified contract provenance.
- No dashboard was added because the core research workflow and reports are currently more valuable than another UI surface.
- Per-contract API timeout/retry accounting is not implemented for external providers.
