from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from .schema import Contract, ContractError


def contract_from_dict(data: dict[str, Any]) -> Contract:
    try:
        return Contract.model_validate(data)
    except ValidationError as exc:
        raise ContractError(str(exc)) from exc


def load_contract(path: str | Path) -> Contract:
    path = Path(path)
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except json.JSONDecodeError as exc:
        raise ContractError(f"{path}: invalid JSON: {exc}") from exc
    except OSError as exc:
        raise ContractError(f"{path}: could not read contract: {exc}") from exc
    if not isinstance(data, dict):
        raise ContractError(f"{path}: contract JSON must be an object")
    try:
        return contract_from_dict(data)
    except ContractError as exc:
        raise ContractError(f"{path}: {exc}") from exc


def load_contracts(path: str | Path) -> list[Contract]:
    root = Path(path)
    if root.is_file():
        return [load_contract(root)]
    if not root.exists():
        raise ContractError(f"{root}: path does not exist")
    files = sorted(root.glob("*.json"))
    if not files:
        files = sorted(root.glob("**/contracts/*.json"))
    if not files:
        raise ContractError(f"{root}: no contract JSON files found")
    return [load_contract(file) for file in files]


def validate_contract(contract: Contract) -> None:
    Contract.model_validate(contract.model_dump(mode="python"))
