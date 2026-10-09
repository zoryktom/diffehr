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

echo "== Step 3: Hugging Face evaluations =="
# HF_OFFLINE=1 (default) never downloads weights: cached models run real greedy inference on cuda/mps/cpu,
# uncached models fall back to clearly labelled offline fixtures that the report keeps separate.
export HF_OFFLINE="${HF_OFFLINE:-1}"
HF_MODELS="${HF_MODELS:-biomistral-7b,meditron-7b,llama-3.1-8b,qwen2.5-0.5b,smollm2-135m}"
"$PY" -m diffehr benchmark \
  --manifest examples/manifest.json \
  --models "$HF_MODELS" \
  --output-dir evidence/runs/full \
  --report evidence/reports/hf_benchmark_summary.md

echo "== Step 4: discovery fuzzer sweeps =="
for model in oracle heuristic reckless; do
  "$PY" -m diffehr fuzz \
    --input examples/discovery/base_chart.json \
    --perturbations 20 \
    --seed 2025 \
    --model "$model" \
    --out "evidence/runs/fuzz/fuzz_${model}.json"
done

echo "== Step 5: raw artifacts =="
cp evidence/runs/fuzz/fuzz_reckless.json evidence/runs/fuzz_findings.json
"$PY" -m diffehr replay-finding \
  --input evidence/runs/fuzz_findings.json \
  --finding-id fuzz_demographic_003 \
  --model reckless \
  --out evidence/runs/replayed_finding.json

echo "== Step 6: reports =="
"$PY" -m diffehr report \
  --input-dir evidence/runs/full \
  --contracts examples \
  --fuzz-dir evidence/runs/fuzz \
  --output-dir evidence/reports \
  --title "DiffEHR Multi-Specialty Benchmark Report"

echo "Artifacts written to evidence/runs/ and evidence/reports/"
