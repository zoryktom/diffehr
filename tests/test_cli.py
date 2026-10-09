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
        self.assertIn("Validated 8", result.stdout)

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


if __name__ == "__main__":
    unittest.main()
