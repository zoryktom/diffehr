"""Backward-compatible adapter imports.

The artifact's adapter implementations live in :mod:`diffehr.adapters`.
"""

from __future__ import annotations

from .adapters import (
    HeuristicAdapter,
    LocalHFAdapter,
    ModelAdapter,
    ModelResponse,
    OpenAIAdapter,
    OracleAdapter,
    make_model,
    parse_model_response,
)

ClinicalAI = ModelAdapter
OracleAgent = OracleAdapter
HeuristicOncologyAgent = HeuristicAdapter
OpenAIResponsesModel = OpenAIAdapter

__all__ = [
    "ClinicalAI",
    "HeuristicAdapter",
    "HeuristicOncologyAgent",
    "LocalHFAdapter",
    "ModelAdapter",
    "ModelResponse",
    "OpenAIAdapter",
    "OpenAIResponsesModel",
    "OracleAdapter",
    "OracleAgent",
    "make_model",
    "parse_model_response",
]
