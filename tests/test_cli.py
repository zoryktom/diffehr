import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class CliTests(unittest.TestCase):
    def test_validate_command(self):
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "diffehr",
                "validate",
                str(ROOT / "examples" / "oncology" / "contracts"),
            ],
            cwd=ROOT,
            env={"PYTHONPATH": str(ROOT / "src")},
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Validated 40", result.stdout)

    def test_validate_all_examples_command(self):
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "diffehr",
                "validate",
                str(ROOT / "examples"),
            ],
            cwd=ROOT,
            env={"PYTHONPATH": str(ROOT / "src")},
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Validated 120", result.stdout)

    def test_evaluate_command_writes_json(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out = Path(tmpdir) / "results.json"
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "diffehr",
                    "evaluate",
                    str(ROOT / "examples" / "oncology" / "contracts"),
                    "--model",
                    "oracle",
                    "--out",
                    str(out),
                ],
                cwd=ROOT,
                env={"PYTHONPATH": str(ROOT / "src")},
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(out.exists())

    def test_report_command_writes_metric_tables(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            run = Path(tmpdir) / "oracle.json"
            report = Path(tmpdir) / "report.md"
            evaluate = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "diffehr",
                    "evaluate",
                    str(ROOT / "examples" / "oncology" / "contracts"),
                    "--model",
                    "oracle",
                    "--out",
                    str(run),
                ],
                cwd=ROOT,
                env={"PYTHONPATH": str(ROOT / "src")},
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(evaluate.returncode, 0, evaluate.stderr)
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "diffehr",
                    "report",
                    str(run),
                    "--out",
                    str(report),
                ],
                cwd=ROOT,
                env={"PYTHONPATH": str(ROOT / "src")},
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Research Metrics", report.read_text(encoding="utf-8"))
            self.assertIn("Failure Matrix", report.read_text(encoding="utf-8"))

    def test_fuzz_command_writes_findings(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out = Path(tmpdir) / "fuzz.json"
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "diffehr",
                    "fuzz",
                    "--input",
                    str(ROOT / "examples" / "discovery" / "base_chart.json"),
                    "--perturbations",
                    "20",
                    "--model",
                    "reckless-oncology",
                    "--out",
                    str(out),
                ],
                cwd=ROOT,
                env={"PYTHONPATH": str(ROOT / "src")},
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(out.read_text(encoding="utf-8"))
            self.assertGreaterEqual(payload["n_findings"], 2)

    def test_manifest_and_failure_commands(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "diffehr",
                    "manifest",
                    str(ROOT / "examples"),
                ],
                cwd=ROOT,
                env={"PYTHONPATH": str(ROOT / "src")},
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(manifest_result.returncode, 0, manifest_result.stderr)
            run = Path(tmpdir) / "reckless.json"
            report = Path(tmpdir) / "failures.md"
            evaluate = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "diffehr",
                    "evaluate",
                    str(ROOT / "examples"),
                    "--model",
                    "reckless-oncology",
                    "--out",
                    str(run),
                ],
                cwd=ROOT,
                env={"PYTHONPATH": str(ROOT / "src")},
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(evaluate.returncode, 0, evaluate.stderr)
            failures = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "diffehr",
                    "failures",
                    str(run),
                    "--out",
                    str(report),
                ],
                cwd=ROOT,
                env={"PYTHONPATH": str(ROOT / "src")},
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(failures.returncode, 0, failures.stderr)
            self.assertIn("Case-Level Failures", report.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
