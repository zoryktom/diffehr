#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

export PYTHONPATH="${PYTHONPATH:-src}"

python -m diffehr validate examples/oncology/contracts
python -m diffehr validate examples/cardiology/contracts
python -m diffehr validate examples/infectious_disease/contracts
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

python -m diffehr fuzz \
  --input examples/discovery/base_chart.json \
  --perturbations 20 \
  --model reckless-oncology \
  --out evidence/runs/fuzz_findings.json
