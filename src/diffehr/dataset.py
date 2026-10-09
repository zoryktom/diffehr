from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any

from .contracts import Contract, ContractError, load_contract, load_contracts

MANIFEST_NAME = "manifest.json"
DATASET_VERSION = "0.2.0"


@dataclass(frozen=True)
class DatasetManifest:
    root: Path
    payload: dict[str, Any]

    @property
    def path(self) -> Path:
        return self.root / MANIFEST_NAME


def generate_dataset_manifest(root: str | Path) -> DatasetManifest:
    root = Path(root)
    contracts = load_contracts(root)
    files = _contract_files(root)
    payload = {
        "dataset_id": "diffehr-multispecialty",
        "dataset_version": DATASET_VERSION,
        "schema_version": "0.2",
        "contract_count": len(contracts),
        "domain_counts": dict(sorted(Counter(contract.domain for contract in contracts).items())),
        "category_counts": dict(sorted(Counter(contract.contract_type.value for contract in contracts).items())),
        "review_status": "synthetic_author_checked",
        "provenance": {
            "data_type": "synthetic",
            "contains_real_patient_data": False,
            "clinical_validation_status": "not clinically validated",
        },
        "generation": {
            "deterministic": True,
            "instructions": "Run `PYTHONPATH=src python -m diffehr validate examples` and `scripts/run_all_benchmarks.sh`.",
        },
        "known_limitations": [
            "Synthetic contracts do not establish real-world clinical safety or model deployment readiness.",
            "Evidence support is checked by citation identifiers, not by independent semantic adjudication.",
            "Clinical assumptions should be reviewed before adding new contracts to a validated benchmark.",
        ],
        "contracts": [_manifest_entry(root, path) for path in files],
    }
    return DatasetManifest(root=root, payload=payload)


def _pack_counts(root: Path) -> dict[str, int]:
    return dict(sorted(Counter(contract.domain for contract in load_contracts(root)).items()))


def sync_pack_files(root: str | Path) -> list[Path]:
    """Rewrite each pack.json contract count and description from the contracts on disk."""
    root = Path(root)
    written = []
    for pack_path in sorted(root.glob("*/pack.json")):
        pack = json.loads(pack_path.read_text(encoding="utf-8"))
        count = len(list((pack_path.parent / pack.get("contracts_path", "contracts")).glob("*.json")))
        pack["n_contracts"] = count
        pack["description"] = (
            f"{count} paired synthetic {pack['domain'].replace('_', ' ')} EHR contracts for testing clinical counterfactual consistency."
        )
        pack_path.write_text(json.dumps(pack, indent=2) + "\n", encoding="utf-8")
        written.append(pack_path)
    return written


def validate_pack_files(root: str | Path) -> None:
    root = Path(root)
    for pack_path in sorted(root.glob("*/pack.json")):
        pack = json.loads(pack_path.read_text(encoding="utf-8"))
        count = len(list((pack_path.parent / pack.get("contracts_path", "contracts")).glob("*.json")))
        if pack.get("n_contracts") != count:
            raise ContractError(f"{pack_path}: n_contracts={pack.get('n_contracts')} but {count} contract files exist")


def save_dataset_manifest(root: str | Path) -> Path:
    sync_pack_files(root)
    manifest = generate_dataset_manifest(root)
    manifest.path.write_text(json.dumps(manifest.payload, indent=2) + "\n", encoding="utf-8")
    return manifest.path


def validate_dataset_manifest(root: str | Path) -> None:
    root = Path(root)
    validate_pack_files(root)
    manifest_path = root / MANIFEST_NAME
    if not manifest_path.exists():
        return
    with manifest_path.open("r", encoding="utf-8") as handle:
        actual = json.load(handle)
    expected = generate_dataset_manifest(root).payload
    if actual != expected:
        raise ContractError(f"{manifest_path}: dataset manifest is stale or inconsistent; regenerate it")


def summarize_counterfactual_differences(contract: Contract) -> dict[str, Any]:
    base_items = {item.id: item for item in contract.base_patient.record}
    variant_items = {item.id: item for item in contract.variant_patient.record}
    shared = sorted(set(base_items) & set(variant_items))
    added = sorted(set(variant_items) - set(base_items))
    removed = sorted(set(base_items) - set(variant_items))
    changed_items: list[dict[str, str]] = []
    for item_id in shared:
        base = base_items[item_id]
        variant = variant_items[item_id]
        fields = []
        if base.date != variant.date:
            fields.append("date")
        if base.type != variant.type:
            fields.append("type")
        if base.text != variant.text:
            fields.append("text")
        if fields:
            changed_items.append({"id": item_id, "fields": ",".join(fields)})

    attribute_changes = {
        key: {
            "base": contract.base_patient.attributes.get(key),
            "variant": contract.variant_patient.attributes.get(key),
        }
        for key in sorted(set(contract.base_patient.attributes) | set(contract.variant_patient.attributes))
        if contract.base_patient.attributes.get(key) != contract.variant_patient.attributes.get(key)
    }
    change_count = len(added) + len(removed) + len(changed_items) + len(attribute_changes)
    if change_count == 0:
        factor_label = "none"
    elif change_count == 1:
        factor_label = "single_factor"
    else:
        factor_label = "multifactor_or_dependent_representation"
    return {
        "factor_label": factor_label,
        "change_count": change_count,
        "attribute_changes": attribute_changes,
        "record_items_added": added,
        "record_items_removed": removed,
        "record_items_changed": changed_items,
    }


def _manifest_entry(root: Path, path: Path) -> dict[str, Any]:
    contract = load_contract(path)
    return {
        "path": path.relative_to(root).as_posix(),
        "sha256": _sha256(path),
        "id": contract.id,
        "domain": contract.domain,
        "category": contract.contract_type.value,
        "relation": contract.expected.relation.value,
        "review_status": "synthetic_author_checked",
        "counterfactual_difference": summarize_counterfactual_differences(contract)["factor_label"],
    }


def _contract_files(root: Path) -> list[Path]:
    if root.is_file():
        return [root]
    return sorted(root.glob("**/contracts/*.json"))


def _sha256(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()
