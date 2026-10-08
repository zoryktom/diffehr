import unittest
from pathlib import Path

from diffehr.contracts import load_contracts


ROOT = Path(__file__).resolve().parents[1]


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


if __name__ == "__main__":
    unittest.main()

