"""Backward-compatible contract imports.

The research artifact schema now lives in :mod:`diffehr.core`.
"""

from __future__ import annotations

from .core import (
    BehavioralRelation,
    ClinicalTask,
    Contract,
    ContractError,
    ContractProvenance,
    ContractType,
    CounterfactualMutation,
    ExpectedBehavior,
    PatientRecord,
    RecordItem,
    RequiredEvidenceCitations,
    TemporalConstraints,
    contract_from_dict,
    load_contract,
    load_contracts,
    validate_contract,
)

__all__ = [
    "BehavioralRelation",
    "ClinicalTask",
    "Contract",
    "ContractError",
    "ContractProvenance",
    "ContractType",
    "CounterfactualMutation",
    "ExpectedBehavior",
    "PatientRecord",
    "RecordItem",
    "RequiredEvidenceCitations",
    "TemporalConstraints",
    "contract_from_dict",
    "load_contract",
    "load_contracts",
    "validate_contract",
]
