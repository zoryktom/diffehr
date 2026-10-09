import copy
import json
import unittest
from pathlib import Path

import pytest

from diffehr.contracts import BehavioralRelation, ContractError, contract_from_dict, load_contracts


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "examples" / "oncology" / "contracts" / "onc_race_invariance_006.json"


class ContractTests(unittest.TestCase):
    def test_oncology_contracts_load(self):
        contracts = load_contracts(ROOT / "examples" / "oncology" / "contracts")
        self.assertEqual(len(contracts), 8)
        self.assertTrue(all(contract.id.startswith("onc_") for contract in contracts))

    def test_contract_prompts_include_json_instruction(self):
        contract = load_contracts(ROOT / "examples" / "oncology" / "contracts")[0]
        prompt = contract.prompt("base")
        self.assertIn("Return strict JSON", prompt)
        self.assertIn("Decision date:", prompt)

    def test_schema_rejects_unknown_fields(self):
        data = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
        data["unexpected"] = "not part of the contract schema"
        with pytest.raises(ContractError, match="Extra inputs are not permitted"):
            contract_from_dict(data)

    def test_schema_accepts_formal_relation_alias(self):
        data = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
        data["expected"]["relation"] = "must_remain_invariable"
        contract = contract_from_dict(data)
        self.assertEqual(contract.expected.relation, BehavioralRelation.MUST_REMAIN_INVARIABLE)

    def test_fhir_sanity_check_rejects_bad_bundle(self):
        data = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
        bad = copy.deepcopy(data)
        bad["base_patient"]["fhir"] = {"entry": []}
        with pytest.raises(ContractError, match="resourceType"):
            contract_from_dict(bad)


if __name__ == "__main__":
    unittest.main()
