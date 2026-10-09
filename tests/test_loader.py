import json
from datetime import date
from pathlib import Path

import pytest

from diffehr.core import ContractError, load_contract, load_contracts
from diffehr.dataset import validate_dataset_manifest, validate_pack_files

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"
PACKS = ("oncology", "cardiology", "infectious_disease")
REQUIRED = {
    "id",
    "title",
    "domain",
    "task",
    "contract_type",
    "allowed_decisions",
    "base_patient",
    "variant_patient",
    "expected",
}
CATEGORIES = {"clinical_sensitivity", "nonclinical_invariance", "temporal_validity"}


@pytest.fixture(scope="module")
def contracts():
    return load_contracts(EXAMPLES)


def test_recursive_discovery_finds_all_packs(contracts):
    assert len(contracts) == 120
    for pack in PACKS:
        assert len(load_contracts(EXAMPLES / pack)) == 40
        assert len(list((EXAMPLES / pack / "contracts").glob("*.json"))) == 40


def test_manifest_and_pack_manifests_agree():
    manifest = json.loads((EXAMPLES / "manifest.json").read_text())
    assert manifest["contract_count"] == 120
    assert manifest["domain_counts"] == {pack: 40 for pack in PACKS}
    assert len(manifest["contracts"]) == 120
    for pack in PACKS:
        pack_manifest = json.loads((EXAMPLES / pack / "pack.json").read_text())
        assert pack_manifest["n_contracts"] == 40
        assert pack_manifest["domain"] == pack
    validate_dataset_manifest(EXAMPLES)
    validate_pack_files(EXAMPLES)


def test_manifest_checksums_cover_every_file_on_disk():
    manifest = json.loads((EXAMPLES / "manifest.json").read_text())
    listed = {entry["id"] for entry in manifest["contracts"]}
    on_disk = {path.stem for path in EXAMPLES.glob("*/contracts/*.json")}
    assert listed == on_disk


def test_stale_pack_count_is_rejected(tmp_path):
    import shutil

    copy = tmp_path / "examples"
    shutil.copytree(EXAMPLES, copy, ignore=shutil.ignore_patterns("discovery"))
    pack = copy / "cardiology" / "pack.json"
    data = json.loads(pack.read_text())
    data["n_contracts"] = 39
    pack.write_text(json.dumps(data))
    with pytest.raises(ContractError):
        validate_dataset_manifest(copy)


def test_all_contracts_satisfy_documented_schema(contracts):
    ids = [c.id for c in contracts]
    assert len(ids) == len(set(ids))
    for c in contracts:
        assert REQUIRED <= set(c.model_dump()), c.id
        assert c.contract_type.value in CATEGORIES
        assert len(set(c.allowed_decisions)) == len(c.allowed_decisions)
        assert c.expected.base_decision in c.allowed_decisions
        assert c.expected.variant_decision in c.allowed_decisions
        same = c.expected.base_decision == c.expected.variant_decision
        assert same == (c.expected.relation.value == "same"), c.id


def test_every_contract_has_fhir_bundles_with_integrity(contracts):
    for c in contracts:
        for patient in (c.base_patient, c.variant_patient):
            assert patient.fhir is not None, c.id
            entries = [e["resource"] for e in patient.fhir["entry"]]
            keys = [(r["resourceType"], r["id"]) for r in entries]
            assert len(keys) == len(set(keys)), c.id
            patient_ids = {r["id"] for r in entries if r["resourceType"] == "Patient"}
            assert patient_ids == {patient.id}, c.id
            for r in entries:
                ref = r.get("subject", {}).get("reference")
                if ref:
                    assert ref == f"Patient/{patient.id}", c.id


def test_decision_index_and_citations_are_consistent(contracts):
    for c in contracts:
        assert c.base_patient.as_of == c.variant_patient.as_of, c.id
        for side, patient in (("base", c.base_patient), ("variant", c.variant_patient)):
            ids = {item.id for item in patient.record}
            required = getattr(c.expected.required_citations, side)
            assert set(required) <= ids, c.id
            assert all(isinstance(item.date, date) for item in patient.record)


def test_category_mix_per_pack(contracts):
    for pack in PACKS:
        kinds = {c.contract_type.value for c in contracts if c.domain == pack}
        assert kinds == CATEGORIES, pack


def test_invalid_contracts_report_location(tmp_path):
    source = json.loads((EXAMPLES / "oncology" / "contracts" / "onc_race_invariance_006.json").read_text())
    cases = {
        "missing": lambda d: d.pop("task"),
        "enum": lambda d: d.update(contract_type="made_up"),
        "relation": lambda d: d["expected"].update(relation="flip"),
        "citation": lambda d: d["expected"]["required_citations"].update(base=["no_such_item"]),
    }
    for name, mutate in cases.items():
        data = json.loads(json.dumps(source))
        mutate(data)
        path = tmp_path / f"{name}.json"
        path.write_text(json.dumps(data, indent=2))
        with pytest.raises(ContractError) as exc:
            load_contract(path)
        assert str(path) in str(exc.value)


def test_loader_edge_cases(tmp_path):
    with pytest.raises(ContractError, match="does not exist"):
        load_contracts(tmp_path / "nope")
    with pytest.raises(ContractError, match="no contract JSON"):
        load_contracts(tmp_path)
    (tmp_path / "list.json").write_text("[]")
    with pytest.raises(ContractError, match="must be an object"):
        load_contract(tmp_path / "list.json")
    (tmp_path / "bad.json").write_text('{\n  "id": ,\n}')
    with pytest.raises(ContractError, match=r"bad\.json:2:"):
        load_contract(tmp_path / "bad.json")
