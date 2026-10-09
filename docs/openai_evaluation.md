# Running DiffEHR On OpenAI Models

DiffEHR includes a minimal OpenAI Responses API adapter implemented with the
Python standard library.

## Setup

```bash
export OPENAI_API_KEY="..."
cd diffehr
```

## Run

```bash
PYTHONPATH=src python3 -m diffehr evaluate examples \
  --model openai:gpt-5-mini \
  --out evidence/runs/openai-gpt-5-mini.json
```

If that model is not available to your account, replace `gpt-5-mini` with a
model identifier available to you.

Render the report:

```bash
PYTHONPATH=src python3 -m diffehr report evidence/runs/openai-gpt-5-mini.json \
  --out evidence/reports/openai-gpt-5-mini.md
```

## Expected Output

The result JSON includes:

- aggregate pass rate
- mean score
- per-contract decisions
- required versus observed citations
- temporal leakage checks
- IVR/DSS confidence intervals
- raw model outputs

## Note

Do not commit API keys or real patient data. The included oncology, cardiology,
and infectious disease packs are synthetic and for testing only.
