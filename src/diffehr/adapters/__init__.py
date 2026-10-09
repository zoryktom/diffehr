"""Model adapters for clinical counterfactual contract evaluation."""

from .base import ClinicalPrediction, ModelAdapter, ModelResponse, build_clinical_prompt, parse_model_response
from .heuristic import HeuristicAdapter
from .local_hf import HuggingFaceAdapter, LocalHFAdapter
from .openai import OpenAIAdapter
from .oracle import OracleAdapter
from .registry import ADAPTERS, make_adapter, make_model

__all__ = [
    "ADAPTERS",
    "ClinicalPrediction",
    "HuggingFaceAdapter",
    "build_clinical_prompt",
    "make_adapter",
    "HeuristicAdapter",
    "LocalHFAdapter",
    "ModelAdapter",
    "ModelResponse",
    "OpenAIAdapter",
    "OracleAdapter",
    "make_model",
    "parse_model_response",
]
