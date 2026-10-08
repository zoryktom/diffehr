import unittest
from pathlib import Path

from diffehr.contracts import load_contracts
from diffehr.models import make_model
from diffehr.scoring import run_evaluation


ROOT = Path(__file__).resolve().parents[1]


class ScoringTests(unittest.TestCase):
    def setUp(self):
        self.contracts = load_contracts(ROOT / "examples" / "oncology" / "contracts")

    def test_oracle_passes_all_contracts(self):
        payload = run_evaluation(self.contracts, make_model("oracle"))
        self.assertEqual(payload["passed"], payload["n_contracts"])
        self.assertEqual(payload["mean_score"], 1.0)

    def test_reckless_fails_at_least_one_contract(self):
        payload = run_evaluation(self.contracts, make_model("reckless"))
        self.assertLess(payload["passed"], payload["n_contracts"])


if __name__ == "__main__":
    unittest.main()

