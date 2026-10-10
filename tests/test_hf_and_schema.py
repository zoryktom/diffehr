import json
import sys
import types
from pathlib import Path

import pytest

from diffehr.adapters import local_hf
from diffehr.adapters.base import build_clinical_prompt, fhir_to_markdown, parse_model_response
from diffehr.adapters.local_hf import HuggingFaceAdapter, resolve_model_id, select_device
from diffehr.adapters.registry import make_adapter, make_model
from diffehr.cli import main
from diffehr.core import (
    BenchmarkResult,
    ClinicalFinding,
    FHIRBundle,
    PerturbationDelta,
    load_contracts,
)

ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = load_contracts(ROOT / "examples")


@pytest.mark.parametrize(
    ("alias", "repo"),
    [
        ("biomistral-7b", "BioMistral/BioMistral-7B"),
        ("meditron-7b", "epfl-llm/meditron-7b"),
        ("llama-3.1-8b", "meta-llama/Llama-3.1-8B-Instruct"),
    ],
)
def test_alias_resolution(alias, repo):
    assert resolve_model_id(alias) == repo
    assert resolve_model_id(repo) == repo


def test_hf_offline_without_cache_uses_labelled_fixture(monkeypatch):
    monkeypatch.setenv("HF_OFFLINE", "1")
    monkeypatch.setattr(local_hf, "is_cached", lambda model_id: False)
    adapter = make_model("biomistral-7b")
    assert isinstance(adapter, HuggingFaceAdapter)
    assert adapter.offline_mock_mode and adapter.is_fixture
    assert adapter.name == "hf-fixture:BioMistral/BioMistral-7B"
    response = adapter.answer(CONTRACTS[0], "base")
    assert response.decision == CONTRACTS[0].allowed_decisions[0]
    assert "OFFLINE FIXTURE" in response.rationale


def test_hf_online_flag_default_is_real_mode(monkeypatch):
    monkeypatch.delenv("HF_OFFLINE", raising=False)
    adapter = make_adapter("local_hf", "llama-3.1-8b")
    assert not adapter.offline_mock_mode
    assert adapter.name == "localhf:meta-llama/Llama-3.1-8B-Instruct"


def test_device_priority_cuda_then_mps_then_cpu(monkeypatch):
    def fake_torch(cuda: bool, mps: bool) -> types.ModuleType:
        module = types.ModuleType("torch")
        module.cuda = types.SimpleNamespace(is_available=lambda: cuda)  # type: ignore[attr-defined]
        module.backends = types.SimpleNamespace(mps=types.SimpleNamespace(is_available=lambda: mps))  # type: ignore[attr-defined]
        return module

    for cuda, mps, expected in ((True, True, "cuda"), (False, True, "mps"), (False, False, "cpu")):
        monkeypatch.setitem(sys.modules, "torch", fake_torch(cuda, mps))
        assert select_device() == expected
    monkeypatch.setitem(sys.modules, "torch", None)
    assert select_device() == "cpu"


def test_fhir_markdown_is_chronological_and_id_tagged():
    patient = CONTRACTS[0].base_patient
    markdown = fhir_to_markdown(patient.fhir)
    assert markdown.startswith("## Patient")
    ids = [item.id for item in patient.record]
    assert all(f"[{item_id}]" in markdown for item_id in ids)
    dates = [line.split()[2] for line in markdown.splitlines() if line.startswith("- [")]
    assert dates == sorted(dates)
    prompt = build_clinical_prompt(CONTRACTS[0], "base")
    assert "## Chart (chronological)" in prompt and '"clinical_rationale"' in prompt
    assert '"resourceType"' not in prompt


def test_regex_fallback_and_fenced_json_extraction():
    allowed = ("eligible", "ineligible", "unsafe")
    fenced = '```json\n{"decision": "Unsafe", "confidence": 7, "contraindication_flagged": "true", "clinical_rationale": "x"}\n```'
    response = parse_model_response("m", fenced, allowed)
    assert (response.decision, response.confidence, response.contraindication_flagged) == ("unsafe", 1.0, True)
    prose = "I believe the patient is ineligible because of lab_20250214_anc."
    fallback = parse_model_response("m", prose, allowed)
    assert fallback.decision == "ineligible" and fallback.citations == ("lab_20250214_anc",)
    assert parse_model_response("m", "{broken", allowed).decision == "unknown"


def test_strict_schema_models_reject_extra_fields_and_validate_artifacts():
    fuzz = json.loads((ROOT / "evidence" / "runs" / "fuzz_findings.json").read_text())
    for finding in fuzz["findings"]:
        ClinicalFinding.model_validate(finding)
    delta = {k: fuzz["results"][0][k] for k in ("id", "type", "mutation", "intended_perturbation")}
    PerturbationDelta.model_validate(delta)
    with pytest.raises(ValueError):
        PerturbationDelta.model_validate({**delta, "extra": 1})
    for contract in CONTRACTS:
        FHIRBundle.model_validate(contract.base_patient.fhir)
        FHIRBundle.model_validate(contract.variant_patient.fhir)
    with pytest.raises(ValueError):
        FHIRBundle.model_validate({"resourceType": "Patient"})
    BenchmarkResult.model_validate(json.loads((ROOT / "evidence" / "runs" / "full" / "oracle.json").read_text()))


def test_benchmark_comma_models_and_fixture_report_separation(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("HF_OFFLINE", "1")
    monkeypatch.setattr(local_hf, "is_cached", lambda model_id: False)
    runs = tmp_path / "runs"
    code = main(
        [
            "benchmark",
            "--manifest",
            str(ROOT / "examples" / "manifest.json"),
            "--models",
            "oracle,meditron-7b",
            "--output-dir",
            str(runs),
            "--report",
            str(tmp_path / "s.md"),
        ]
    )
    assert code == 0
    assert {p.name for p in runs.glob("*.json")} == {"oracle.json", "hf-fixture-epfl-llm-meditron-7b.json"}
    summary = (tmp_path / "s.md").read_text()
    assert "Harness Smoke Test" in summary and "not model results" in summary
    assert summary.index("| oracle |") < summary.index("Harness Smoke Test")
    assert (
        main(
            [
                "report",
                "--input-dir",
                str(runs),
                "--fuzz-input",
                str(tmp_path / "nope.json"),
                "--output-dir",
                str(tmp_path),
            ]
        )
        == 2
    )
    assert "does not exist" in capsys.readouterr().err


def test_report_exposes_unparseable_rate_and_decision_accuracy():
    from diffehr.adapters.oracle import OracleAdapter
    from diffehr.metrics.computation import run_evaluation
    from diffehr.report import render_markdown

    class Silent(OracleAdapter):
        name = "silent"

        def answer(self, contract, side):
            return parse_model_response(self.name, "no decision here", contract.allowed_decisions)

    payload = run_evaluation(CONTRACTS[:6], Silent())
    markdown = render_markdown([payload])
    assert "Output Validity And Decision Accuracy" in markdown
    assert "| silent | 0.00% | 12/12 (100.00%) | 0/6 |" in markdown
    assert payload["passed"] == 0
