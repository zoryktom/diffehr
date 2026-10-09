import unittest
from pathlib import Path
import tempfile

from diffehr.discovery import DiffEHRFuzzer, load_fhir_chart, replay_finding, save_fuzz_results
from diffehr.models import make_model


ROOT = Path(__file__).resolve().parents[1]


class DiscoveryTests(unittest.TestCase):
    def test_fuzzer_finds_reckless_failures(self):
        chart = load_fhir_chart(ROOT / "examples" / "discovery" / "base_chart.json")
        fuzzer = DiffEHRFuzzer(make_model("reckless-oncology"), perturbations=20)
        payload = fuzzer.run(chart)
        self.assertEqual(payload["n_perturbations"], 20)
        self.assertEqual(payload["n_findings"], 3)
        finding_types = {finding["finding"] for finding in payload["findings"]}
        self.assertIn("invariance_violation", finding_types)
        self.assertIn("temporal_leakage", finding_types)
        self.assertIn("generation_config", payload)
        self.assertTrue(all("finding_status" in finding for finding in payload["findings"]))
        keys = {
            (finding["finding"], finding["mutation"], finding["variant_decision"])
            for finding in payload["findings"]
            if finding["finding"] == "invariance_violation"
        }
        self.assertEqual(len(keys), 2)

    def test_recorded_finding_can_be_replayed(self):
        chart = load_fhir_chart(ROOT / "examples" / "discovery" / "base_chart.json")
        payload = DiffEHRFuzzer(make_model("reckless-oncology"), perturbations=20).run(chart)
        finding_id = payload["findings"][0]["id"]
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "fuzz.json"
            save_fuzz_results(payload, path)
            replay = replay_finding(path, finding_id, make_model("reckless-oncology"))
        self.assertEqual(replay["replayed_finding_id"], finding_id)
        self.assertIn("variant_decision", replay)

    def test_malformed_fhir_chart_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "at least one non-Patient resource"):
            DiffEHRFuzzer(make_model("oracle")).run({"resourceType": "Bundle", "entry": []})

    def test_replay_missing_finding_fails_explicitly(self):
        chart = load_fhir_chart(ROOT / "examples" / "discovery" / "base_chart.json")
        payload = DiffEHRFuzzer(make_model("reckless-oncology"), perturbations=3).run(chart)
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "fuzz.json"
            save_fuzz_results(payload, path)
            with self.assertRaisesRegex(ValueError, "Finding not found"):
                replay_finding(path, "missing", make_model("reckless-oncology"))


if __name__ == "__main__":
    unittest.main()
