"""Model adapters for clinical counterfactual contract evaluation."""

from .base import ModelAdapter, ModelResponse, parse_model_response
from .heuristic import HeuristicAdapter
from .local_hf import LocalHFAdapter
from .openai import OpenAIAdapter
from .oracle import OracleAdapter
from .registry import make_model

__all__ = [
    "HeuristicAdapter",
    "LocalHFAdapter",
    "ModelAdapter",
    "ModelResponse",
    "OpenAIAdapter",
    "OracleAdapter",
    "make_model",
    "parse_model_response",
]
