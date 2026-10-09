"""Backward-compatible metric imports.

The scoring engine now lives in :mod:`diffehr.metrics`.
"""

from __future__ import annotations

from .metrics import (
    ContractResult,
    MetricSummary,
    SideScore,
    bootstrap_confidence_intervals,
    citation_precision_recall,
    compute_run_metrics,
    evaluate_contract,
    result_to_dict,
    run_evaluation,
    save_results,
    score_side,
)

__all__ = [
    "ContractResult",
    "MetricSummary",
    "SideScore",
    "bootstrap_confidence_intervals",
    "citation_precision_recall",
    "compute_run_metrics",
    "evaluate_contract",
    "result_to_dict",
    "run_evaluation",
    "save_results",
    "score_side",
]
