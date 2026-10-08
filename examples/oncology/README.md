# DiffEHR-Oncology

This example pack contains paired synthetic oncology charts for counterfactual
contract testing. Each contract includes:

- a base synthetic patient chart
- a variant chart with a controlled clinical or non-clinical change
- expected behavior for the AI system
- required chart evidence
- temporal restrictions
- automated scoring criteria

The data are synthetic and are intended for evaluation research, demos, and
software testing only. They are not clinical guidance and contain no real patient
records.

Run:

```bash
python -m diffehr validate examples/oncology/contracts
python -m diffehr evaluate examples/oncology/contracts --model heuristic --out evidence/runs/heuristic.json
python -m diffehr evaluate examples/oncology/contracts --model reckless --out evidence/runs/reckless.json
python -m diffehr report evidence/runs/heuristic.json evidence/runs/reckless.json --out evidence/reports/demo.md
```

