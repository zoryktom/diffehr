from __future__ import annotations

from .base import ModelAdapter
from .heuristic import HeuristicAdapter
from .local_hf import LocalHFAdapter
from .openai import OpenAIAdapter
from .oracle import OracleAdapter


def make_model(name: str) -> ModelAdapter:
    normalized = name.strip()
    lowered = normalized.lower()
    if lowered == "oracle":
        return OracleAdapter()
    if lowered in {"heuristic", "heuristic-oncology"}:
        return HeuristicAdapter(respect_temporal=True, insurance_bias=False)
    if lowered in {"reckless", "reckless-oncology"}:
        return HeuristicAdapter(respect_temporal=False, insurance_bias=True)
    if lowered.startswith("openai:"):
        return OpenAIAdapter(normalized.split(":", 1)[1])
    if lowered.startswith("localhf:"):
        return LocalHFAdapter(normalized.split(":", 1)[1])
    if lowered.startswith("hf:"):
        return LocalHFAdapter(normalized.split(":", 1)[1])
    raise ValueError(f"Unknown model: {name}")
