"""Core contract schema and loaders for DiffEHR."""

from .loader import contract_from_dict, load_contract, load_contracts, validate_contract
from .schema import (
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
