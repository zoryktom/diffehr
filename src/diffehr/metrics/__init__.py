"""Quantitative metrics for DiffEHR contract runs."""

from .computation import (
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
