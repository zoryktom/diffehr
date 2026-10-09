#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

export PYTHONPATH="${PYTHONPATH:-src}"
export DIFFEHR_RUN_TIMESTAMP="${DIFFEHR_RUN_TIMESTAMP:-$(date -u +%Y-%m-%dT%H:%M:%SZ)}"

python -m diffehr validate examples/oncology/contracts
python -m diffehr validate examples/cardiology/contracts
python -m diffehr validate examples/infectious_disease/contracts
python -m diffehr manifest examples
python -m diffehr validate examples

mkdir -p evidence/runs/full evidence/reports

python -m diffehr evaluate examples --model oracle --out evidence/runs/full/oracle.json
python -m diffehr evaluate examples --model heuristic-oncology --out evidence/runs/full/heuristic-oncology.json
python -m diffehr evaluate examples --model reckless-oncology --out evidence/runs/full/reckless-oncology.json

python -m diffehr report \
  evidence/runs/full/oracle.json \
  evidence/runs/full/heuristic-oncology.json \
  evidence/runs/full/reckless-oncology.json \
  --out evidence/reports/full_benchmark_report.md \
  --title "DiffEHR Multi-Specialty Benchmark Report"

python -m diffehr failures \
  evidence/runs/full/oracle.json \
  evidence/runs/full/heuristic-oncology.json \
  evidence/runs/full/reckless-oncology.json \
  --out evidence/reports/failure_analysis.md \
  --title "DiffEHR Failure Analysis"

python -m diffehr fuzz \
  --input examples/discovery/base_chart.json \
  --perturbations 20 \
  --seed 2025 \
  --model reckless-oncology \
  --out evidence/runs/fuzz_findings.json

python -m diffehr replay-finding \
  --input evidence/runs/fuzz_findings.json \
  --finding-id fuzz_demographic_003 \
  --model reckless-oncology \
  --out evidence/runs/replayed_finding.json
