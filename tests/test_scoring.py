import unittest
from pathlib import Path

from diffehr.contracts import load_contracts
from diffehr.models import ModelResponse, make_model
from diffehr.scoring import citation_precision_recall, run_evaluation, score_side


ROOT = Path(__file__).resolve().parents[1]


class ScoringTests(unittest.TestCase):
    def setUp(self):
        self.contracts = load_contracts(ROOT / "examples" / "oncology" / "contracts")

    def test_oracle_passes_all_contracts(self):
        payload = run_evaluation(self.contracts, make_model("oracle"))
        self.assertEqual(payload["passed"], payload["n_contracts"])
        self.assertEqual(payload["mean_score"], 1.0)
        self.assertEqual(payload["metrics"]["invariance_violation_rate"], 0.0)
        self.assertEqual(payload["metrics"]["decisive_sensitivity_score"], 1.0)
        self.assertEqual(payload["metrics"]["evidence_citation_precision"], 1.0)
        self.assertEqual(payload["metrics"]["evidence_citation_recall"], 1.0)
        self.assertEqual(payload["metrics"]["temporal_leakage_violations"], 0)

    def test_reckless_fails_at_least_one_contract(self):
        payload = run_evaluation(self.contracts, make_model("reckless"))
        self.assertLess(payload["passed"], payload["n_contracts"])

    def test_citation_precision_recall_edge_cases(self):
        self.assertEqual(citation_precision_recall(("a", "b"), ("a", "x")), (0.5, 0.5))
        self.assertEqual(citation_precision_recall((), ()), (1.0, 1.0))
        self.assertEqual(citation_precision_recall(("a",), ()), (0.0, 0.0))

    def test_temporal_leakage_detects_future_citation(self):
        contract = next(item for item in self.contracts if item.id == "onc_temporal_leakage_004")
        response = ModelResponse(
            model="test",
            decision="eligible",
            citations=("img_20250301_future_progression",),
            rationale="Uses the future progression note.",
            confidence=1.0,
            raw_text="{}",
        )
        score = score_side(contract, "variant", response)
        self.assertFalse(score.no_future_evidence)
        self.assertEqual(score.temporal_leakage_violations, ("img_20250301_future_progression",))


if __name__ == "__main__":
    unittest.main()
