from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from .schema import Contract, ContractError


def _format_validation_error(exc: ValidationError, source_text: str | None = None) -> str:
    lines = []
    for error in exc.errors():
        location = ".".join(str(part) for part in error["loc"])
        line_hint = ""
        if source_text is not None:
            keys = [part for part in error["loc"] if isinstance(part, str)]
            for key in reversed(keys):
                match = re.search(rf'"{re.escape(key)}"\s*:', source_text)
                if match:
                    line_hint = f" (line {source_text.count(chr(10), 0, match.start()) + 1})"
                    break
        lines.append(f"{location or '<root>'}{line_hint}: {error['msg']}")
    return "; ".join(lines)


def contract_from_dict(data: dict[str, Any], source_text: str | None = None) -> Contract:
    try:
        return Contract.model_validate(data)
    except ValidationError as exc:
        raise ContractError(_format_validation_error(exc, source_text)) from exc


def load_contract(path: str | Path) -> Contract:
    path = Path(path)
    try:
        text = path.read_text(encoding="utf-8")
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ContractError(f"{path}:{exc.lineno}:{exc.colno}: invalid JSON: {exc.msg}") from exc
    except OSError as exc:
        raise ContractError(f"{path}: could not read contract: {exc}") from exc
    if not isinstance(data, dict):
        raise ContractError(f"{path}: contract JSON must be an object")
    try:
        return contract_from_dict(data, text)
    except ContractError as exc:
        raise ContractError(f"{path}: {exc}") from exc


def load_contracts(path: str | Path) -> list[Contract]:
    root = Path(path)
    if root.is_file():
        return [load_contract(root)]
    if not root.exists():
        raise ContractError(f"{root}: path does not exist")
    files = sorted(root.glob("**/contracts/*.json"))
    if not files:
        files = sorted(file for file in root.glob("*.json") if file.name != "manifest.json")
    if not files:
        raise ContractError(f"{root}: no contract JSON files found")
    return [load_contract(file) for file in files]


def validate_contract(contract: Contract) -> None:
    Contract.model_validate(contract.model_dump(mode="python"))
