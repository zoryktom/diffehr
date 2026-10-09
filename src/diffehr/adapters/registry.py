from __future__ import annotations

from .base import ModelAdapter
from .heuristic import HeuristicAdapter
from .local_hf import HuggingFaceAdapter
from .openai import OpenAIAdapter
from .oracle import OracleAdapter

ADAPTERS: dict[str, type[ModelAdapter]] = {
    "oracle": OracleAdapter,
    "heuristic": HeuristicAdapter,
    "reckless": HeuristicAdapter,
    "openai": OpenAIAdapter,
    "local_hf": HuggingFaceAdapter,
}


def make_adapter(adapter: str, model: str | None = None) -> ModelAdapter:
    """Build an adapter from a registry key and optional model id."""
    key = adapter.strip().lower()
    if key not in ADAPTERS:
        raise ValueError(f"Unknown adapter: {adapter}. Available: {', '.join(sorted(ADAPTERS))}")
    if key == "oracle":
        return OracleAdapter()
    if key == "heuristic":
        return HeuristicAdapter(respect_temporal=True, insurance_bias=False)
    if key == "reckless":
        return HeuristicAdapter(respect_temporal=False, insurance_bias=True)
    if not model:
        raise ValueError(f"Adapter '{key}' requires --model")
    return ADAPTERS[key](model)  # type: ignore[call-arg]


def make_model(name: str) -> ModelAdapter:
    normalized = name.strip()
    lowered = normalized.lower()
    if lowered == "oracle":
        return OracleAdapter()
    if lowered in {"heuristic", "heuristic-oncology"}:
        return HeuristicAdapter(respect_temporal=True, insurance_bias=False)
    if lowered in {"reckless", "reckless-oncology"}:
        return HeuristicAdapter(respect_temporal=False, insurance_bias=True)
    for prefix, key in (("openai:", "openai"), ("localhf:", "local_hf"), ("hf:", "local_hf")):
        if lowered.startswith(prefix):
            return make_adapter(key, normalized.split(":", 1)[1])
    raise ValueError(f"Unknown model: {name}")
