#!/usr/bin/env bash
# End-to-end offline DiffEHR pipeline: validate, benchmark, fuzz, report.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

export PYTHONPATH="${PYTHONPATH:-src}"
export DIFFEHR_RUN_TIMESTAMP="${DIFFEHR_RUN_TIMESTAMP:-$(date -u +%Y-%m-%dT%H:%M:%SZ)}"
PY="${PYTHON:-python}"
command -v "$PY" >/dev/null 2>&1 || PY=python3

echo "== Step 1: validate manifests =="
"$PY" -m diffehr manifest examples
"$PY" -m diffehr validate --manifest examples/manifest.json

echo "== Step 2: benchmark oracle, heuristic, reckless on 120 contracts =="
rm -rf evidence/runs/full evidence/runs/fuzz
mkdir -p evidence/runs/full evidence/runs/fuzz evidence/reports
"$PY" -m diffehr benchmark \
  --manifest examples/manifest.json \
  --adapters oracle,heuristic,reckless \
  --output-dir evidence/runs/full \
  --report evidence/reports/benchmark_summary.md

echo "== Step 3: discovery fuzzer sweeps =="
for model in oracle heuristic reckless; do
  "$PY" -m diffehr fuzz \
    --input examples/discovery/base_chart.json \
    --perturbations 20 \
    --seed 2025 \
    --model "$model" \
    --out "evidence/runs/fuzz/fuzz_${model}.json"
done

echo "== Step 4: raw artifacts =="
cp evidence/runs/fuzz/fuzz_reckless.json evidence/runs/fuzz_findings.json
"$PY" -m diffehr replay-finding \
  --input evidence/runs/fuzz_findings.json \
  --finding-id fuzz_demographic_003 \
  --model reckless \
  --out evidence/runs/replayed_finding.json

echo "== Step 5: reports =="
"$PY" -m diffehr report \
  --input-dir evidence/runs/full \
  --contracts examples \
  --fuzz-dir evidence/runs/fuzz \
  --output-dir evidence/reports \
  --title "DiffEHR Multi-Specialty Benchmark Report"

echo "Artifacts written to evidence/runs/ and evidence/reports/"
