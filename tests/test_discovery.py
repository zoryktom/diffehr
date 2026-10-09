import unittest
from pathlib import Path

from diffehr.discovery import DiffEHRFuzzer, load_fhir_chart
from diffehr.models import make_model


ROOT = Path(__file__).resolve().parents[1]


class DiscoveryTests(unittest.TestCase):
    def test_fuzzer_finds_reckless_failures(self):
        chart = load_fhir_chart(ROOT / "examples" / "discovery" / "base_chart.json")
        fuzzer = DiffEHRFuzzer(make_model("reckless-oncology"), perturbations=20)
        payload = fuzzer.run(chart)
        self.assertEqual(payload["n_perturbations"], 20)
        self.assertGreaterEqual(payload["n_findings"], 2)
        finding_types = {finding["finding"] for finding in payload["findings"]}
        self.assertIn("invariance_violation", finding_types)
        self.assertIn("temporal_leakage", finding_types)


if __name__ == "__main__":
    unittest.main()
