import unittest
from pathlib import Path

from diffehr.contracts import load_contracts
from diffehr.models import ModelResponse, make_model
from diffehr.scoring import citation_precision_recall, compute_run_metrics, run_evaluation, score_side

ROOT = Path(__file__).resolve().parents[1]


class ScoringTests(unittest.TestCase):
    def setUp(self):
        self.contracts = load_contracts(ROOT / "examples")

    def test_oracle_passes_all_contracts(self):
        payload = run_evaluation(self.contracts, make_model("oracle"))
        self.assertEqual(payload["passed"], payload["n_contracts"])
        self.assertEqual(payload["mean_score"], 1.0)
        self.assertEqual(payload["metrics"]["invariance_violation_rate"], 0.0)
        self.assertEqual(payload["metrics"]["decisive_sensitivity_score"], 1.0)
        self.assertEqual(payload["metrics"]["evidence_citation_precision"], 1.0)
        self.assertEqual(payload["metrics"]["evidence_citation_recall"], 1.0)
        self.assertEqual(payload["metrics"]["temporal_leakage_violations"], 0)
        self.assertEqual(payload["metrics"]["confidence_intervals"]["invariance_violation_rate"], [0.0, 0.0])
        self.assertEqual(payload["metrics"]["confidence_intervals"]["decisive_sensitivity_score"], [1.0, 1.0])
        metadata = payload["run_metadata"]
        self.assertEqual(metadata["dataset_version"], "0.2.0")
        self.assertEqual(metadata["contract_count"], 120)
        self.assertEqual(len(metadata["dataset_fingerprint_sha256"]), 64)
        self.assertFalse(metadata["external_model"])

    def test_heuristic_passes_original_suite_and_is_imperfect_on_expansion(self):
        limits = {"oncology": 16, "cardiology": 8, "infectious_disease": 8}
        original = [c for c in self.contracts if int(c.id.rsplit("_", 1)[1]) <= limits[c.domain]]
        self.assertEqual(len(original), 32)
        payload = run_evaluation(original, make_model("heuristic-oncology"))
        self.assertEqual(payload["passed"], 32)
        full = run_evaluation(self.contracts, make_model("heuristic-oncology"))
        self.assertEqual(full["n_contracts"], 120)
        self.assertLess(full["passed"], 120)

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

    def test_empty_metric_inputs_are_explicit_zero_or_perfect_empty_sets(self):
        metrics = compute_run_metrics([])
        self.assertEqual(metrics.invariance_violation_rate, 0.0)
        self.assertEqual(metrics.decisive_sensitivity_score, 0.0)
        self.assertEqual(metrics.evidence_citation_precision, 1.0)
        self.assertEqual(metrics.evidence_citation_recall, 1.0)
        self.assertEqual(metrics.temporal_leakage_violations, 0)


if __name__ == "__main__":
    unittest.main()
