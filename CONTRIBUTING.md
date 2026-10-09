# Contributing To DiffEHR

DiffEHR is a synthetic research and testing artifact. Contributions should improve reproducibility, methodological clarity, or benchmark quality.

## Before Adding A Contract

Every contract should be synthetic and inspectable. Do not include real patient records, identifiers, secrets, or private clinical data.

New contracts should include:

- a clear clinical or operational question,
- base and variant records,
- the expected relation,
- allowed decisions,
- required evidence IDs,
- temporal decision cutoff,
- rationale,
- known ambiguities or limitations when applicable.

Do not claim clinician validation or guideline support unless that review or source has actually been documented.

## Verification

Run:

```bash
python -m pip install -e '.[test]'
PYTHONPATH=src pytest tests/ -q
PYTHONPATH=src python -m diffehr manifest examples
PYTHONPATH=src python -m diffehr validate examples
scripts/run_all_benchmarks.sh
```

The manifest must match the checked-in dataset.

## Responsible Use

DiffEHR is not a clinical decision-support product, medical device, diagnostic tool, or substitute for clinician judgment. Synthetic benchmark performance does not establish real-world clinical safety.
