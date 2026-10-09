import contextlib
import io
import json
import shutil
from pathlib import Path

import pytest

from diffehr.cli import main

ROOT = Path(__file__).resolve().parents[1]
ONC = ROOT / "examples" / "oncology"
CHART = ROOT / "examples" / "discovery" / "base_chart.json"


def run_cli(*argv: str) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = main([str(a) for a in argv])
    return code, out.getvalue(), err.getvalue()


def test_validate_manifest_covers_all_packs():
    code, out, _ = run_cli("validate", "--manifest", ROOT / "examples" / "manifest.json")
    assert code == 0
    assert "Validated 120" in out


def test_validate_requires_path_or_manifest():
    code, _, err = run_cli("validate")
    assert code == 2
    assert "provide a path or --manifest" in err


def test_validate_missing_manifest_reports_path():
    code, _, err = run_cli("validate", "--manifest", "/nonexistent/manifest.json")
    assert code == 2
    assert "manifest does not exist" in err


def test_validate_schema_mismatch_has_informative_stderr(tmp_path):
    pack = tmp_path / "contracts"
    pack.mkdir()
    bad = json.loads((ONC / "contracts" / "onc_race_invariance_006.json").read_text())
    bad["unexpected_field"] = 1
    (pack / "bad.json").write_text(json.dumps(bad, indent=2))
    code, _, err = run_cli("validate", pack)
    assert code == 2
    assert "unexpected_field" in err


def test_validate_malformed_json_reports_line(tmp_path):
    pack = tmp_path / "contracts"
    pack.mkdir()
    (pack / "bad.json").write_text('{\n  "id": \n')
    code, _, err = run_cli("validate", pack)
    assert code == 2
    assert "bad.json:" in err and "invalid JSON" in err


def test_run_oracle_on_pack_writes_results(tmp_path):
    out = tmp_path / "oracle.json"
    code, stdout, _ = run_cli("run", "--adapter", "oracle", "--pack", ONC, "--output", out)
    assert code == 0
    assert "40/40 passed" in stdout
    payload = json.loads(out.read_text())
    assert payload["n_contracts"] == 40
    assert payload["run_metadata"]["elapsed_seconds"] >= 0


def test_run_unknown_adapter_and_missing_pack_fail(tmp_path):
    code, _, err = run_cli("run", "--adapter", "nope", "--pack", ONC, "--output", tmp_path / "x.json")
    assert code == 1 and "Unknown adapter" in err
    code, _, err = run_cli(
        "run", "--adapter", "oracle", "--pack", tmp_path / "missing", "--output", tmp_path / "x.json"
    )
    assert code == 2 and "does not exist" in err


def test_run_external_adapter_without_credentials_fails_offline(tmp_path, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    code, _, err = run_cli("run", "--adapter", "openai", "--model", "m", "--pack", ONC, "--output", tmp_path / "x.json")
    assert code == 1 and "OPENAI_API_KEY" in err


def test_benchmark_report_pipeline(tmp_path):
    runs, reports = tmp_path / "runs", tmp_path / "reports"
    code, out, _ = run_cli(
        "benchmark",
        "--manifest",
        ROOT / "examples" / "manifest.json",
        "--adapters",
        "oracle,heuristic,reckless",
        "--output-dir",
        runs,
        "--report",
        tmp_path / "summary.md",
    )
    assert code == 0
    assert len(list(runs.glob("*.json"))) == 3
    fuzz_dir = tmp_path / "fuzz"
    for model in ("oracle", "heuristic", "reckless"):
        code, _, _ = run_cli("fuzz", "--input", CHART, "--model", model, "--out", fuzz_dir / f"{model}.json")
        assert code == 0
    code, out, _ = run_cli(
        "report", "--input-dir", runs, "--contracts", ROOT / "examples", "--fuzz-dir", fuzz_dir, "--output-dir", reports
    )
    assert code == 0
    full = (reports / "full_benchmark_report.md").read_text()
    for header in ("Executive Summary", "CFA %", "IFR %", "TDV %", "Mean SDI", "Latency (ms/contract)"):
        assert header in full
    assert "| 40 | 40 | 40 | 120 |" in full
    failure = (reports / "failure_analysis.md").read_text()
    assert "Discovery Fuzzer Findings" in failure
    assert failure.count("(invariance_violation)") == 3
    assert failure.count("(temporal_leakage)") == 1
    assert failure.count("(clinical_insensitivity)") == 6


def test_report_requires_inputs_and_rejects_empty_dir(tmp_path):
    code, _, err = run_cli("report")
    assert code == 2 and "provide result files" in err
    code, _, err = run_cli("report", "--input-dir", tmp_path)
    assert code == 2 and "no result JSON files" in err


def test_report_missing_fuzz_dir_fails(tmp_path):
    result = tmp_path / "oracle.json"
    run_cli("run", "--adapter", "oracle", "--pack", ONC, "--output", result)
    code, _, err = run_cli("failures", result, "--out", tmp_path / "f.md", "--fuzz-dir", tmp_path / "nope")
    assert code == 2 and "fuzz directory does not exist" in err


def test_fuzz_counts_and_missing_input(tmp_path):
    expected = {"oracle": 0, "heuristic": 3, "reckless": 7}
    for model, count in expected.items():
        code, out, _ = run_cli("fuzz", "--input", CHART, "--model", model, "--out", tmp_path / f"{model}.json")
        assert code == 0
        assert f"{count} finding(s)" in out
    code, _, err = run_cli("fuzz", "--input", tmp_path / "missing.json", "--out", tmp_path / "x.json")
    assert code == 1 and err.startswith("Error:")


def test_fuzz_malformed_chart_fails(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text('{"resourceType": "Bundle", "entry": []}')
    code, _, err = run_cli("fuzz", "--input", bad, "--model", "oracle", "--out", tmp_path / "x.json")
    assert code == 1 and "non-Patient" in err


def test_replay_finding_roundtrip_and_missing_id(tmp_path):
    findings = tmp_path / "f.json"
    run_cli("fuzz", "--input", CHART, "--model", "reckless", "--out", findings)
    code, _, _ = run_cli(
        "replay-finding",
        "--input",
        findings,
        "--finding-id",
        "fuzz_demographic_003",
        "--model",
        "reckless",
        "--out",
        tmp_path / "r.json",
    )
    assert code == 0
    code, _, err = run_cli(
        "replay-finding",
        "--input",
        findings,
        "--finding-id",
        "zzz",
        "--model",
        "reckless",
        "--out",
        tmp_path / "r.json",
    )
    assert code == 1 and "Finding not found" in err


def test_stale_manifest_is_detected_and_regenerated(tmp_path):
    copy = tmp_path / "examples"
    shutil.copytree(ROOT / "examples", copy, ignore=shutil.ignore_patterns("discovery"))
    victim = next((copy / "oncology" / "contracts").glob("*.json"))
    data = json.loads(victim.read_text())
    data["title"] = data["title"] + " edited"
    victim.write_text(json.dumps(data, indent=2))
    code, _, err = run_cli("validate", "--manifest", copy / "manifest.json")
    assert code == 2 and "stale" in err
    assert run_cli("manifest", copy)[0] == 0
    assert run_cli("validate", "--manifest", copy / "manifest.json")[0] == 0


def test_unknown_subcommand_exits_nonzero():
    with pytest.raises(SystemExit) as exc:
        main(["bogus"])
    assert exc.value.code != 0
