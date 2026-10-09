import os
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch

from diffehr.adapters.base import parse_model_response
from diffehr.adapters.local_hf import LocalHFAdapter
from diffehr.adapters.openai import OpenAIAdapter
from diffehr.contracts import load_contracts

ROOT = Path(__file__).resolve().parents[1]


class AdapterTests(unittest.TestCase):
    def setUp(self):
        self.contract = load_contracts(ROOT / "examples" / "oncology" / "contracts")[0]

    def test_malformed_model_text_becomes_unknown_not_success(self):
        response = parse_model_response(
            "mock", "not valid json and no allowed decision", self.contract.allowed_decisions
        )
        self.assertEqual(response.decision, "unknown")
        self.assertEqual(response.confidence, 0.0)

    def test_invalid_json_decision_is_not_accepted(self):
        response = parse_model_response(
            "mock",
            '{"decision": "made_up", "citations": ["path_20250101_egfr"], "confidence": 0.8}',
            self.contract.allowed_decisions,
        )
        self.assertEqual(response.decision, "unknown")
        self.assertEqual(response.citations, ("path_20250101_egfr",))

    def test_openai_adapter_requires_api_key_offline(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "OPENAI_API_KEY"):
                OpenAIAdapter("test-model").answer(self.contract, "base")

    def test_openai_adapter_wraps_transport_errors(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}, clear=True):
            with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("offline")):
                with self.assertRaisesRegex(RuntimeError, "OpenAI API request failed"):
                    OpenAIAdapter("test-model", timeout=1).answer(self.contract, "base")

    def test_local_hf_generation_failure_is_explicit(self):
        adapter = LocalHFAdapter("dummy")

        def fail(*args, **kwargs):
            raise ValueError("model unavailable")

        adapter._pipeline = fail
        with self.assertRaisesRegex(RuntimeError, "generation failed"):
            adapter.answer(self.contract, "base")

    def test_registry_instantiates_every_adapter_offline(self):
        from diffehr.adapters import ADAPTERS, make_adapter, make_model

        self.assertEqual(set(ADAPTERS), {"oracle", "heuristic", "reckless", "local_hf", "openai"})
        self.assertEqual(make_adapter("oracle").name, "oracle")
        self.assertTrue(make_adapter("heuristic").name.startswith("heuristic"))
        self.assertTrue(make_adapter("reckless").name.startswith("reckless"))
        self.assertEqual(make_adapter("openai", "m").name, "openai:m")
        self.assertEqual(make_adapter("local_hf", "org/m").name, "localhf:org/m")
        self.assertEqual(make_model("hf:org/m").name, "localhf:org/m")
        self.assertEqual(make_model("openai:m").name, "openai:m")
        for key in ("oracle", "heuristic", "reckless"):
            response = make_adapter(key).answer(self.contract, "base")
            self.assertIn(response.decision, self.contract.allowed_decisions)

    def test_registry_rejects_unknown_and_missing_model(self):
        from diffehr.adapters import make_adapter, make_model

        with self.assertRaisesRegex(ValueError, "Unknown adapter"):
            make_adapter("nope")
        with self.assertRaisesRegex(ValueError, "requires --model"):
            make_adapter("openai")
        with self.assertRaisesRegex(ValueError, "Unknown model"):
            make_model("nope")

    def test_oracle_and_baselines_are_deterministic(self):
        from diffehr.adapters import make_adapter

        for key in ("oracle", "heuristic", "reckless"):
            adapter = make_adapter(key)
            first = adapter.answer(self.contract, "variant")
            self.assertEqual(first, adapter.answer(self.contract, "variant"))

    def test_hf_without_transformers_fails_explicitly_offline(self):
        import sys

        adapter = LocalHFAdapter("org/model")
        with patch.dict(sys.modules, {"transformers": None}):
            with self.assertRaisesRegex(RuntimeError, "requires transformers and torch"):
                adapter.answer(self.contract, "base")

    def test_hf_uses_greedy_decoding_and_extracts_structured_output(self):
        calls = {}

        def fake_pipeline(prompt, **kwargs):
            calls.update(kwargs)
            calls["prompt"] = prompt
            return [
                {
                    "generated_text": '{"decision": "ELIGIBLE", "confidence": 0.9, "citations": [], "contraindication_flagged": true}'
                }
            ]

        adapter = LocalHFAdapter("org/model", device="cpu")
        adapter._pipeline = fake_pipeline
        response = adapter.answer(self.contract, "base")
        self.assertFalse(calls["do_sample"])
        self.assertIsNone(calls["temperature"])
        self.assertFalse(calls["return_full_text"])
        self.assertIn(self.contract.task, calls["prompt"])
        self.assertEqual(response.decision, "eligible")
        self.assertTrue(response.contraindication_flagged)
        self.assertAlmostEqual(response.confidence, 0.9)

    def test_hf_malformed_generation_is_unknown(self):
        adapter = LocalHFAdapter("org/model")
        adapter._pipeline = lambda prompt, **kw: [{"generated_text": "I cannot answer."}]
        self.assertEqual(adapter.answer(self.contract, "base").decision, "unknown")

    def test_openai_sends_temperature_zero_and_parses_structured_output(self):
        import io
        import json

        captured = {}

        class FakeResponse(io.BytesIO):
            def __enter__(self):
                return self

            def __exit__(self, *exc):
                return False

        body = {"choices": [{"message": {"content": '{"decision": "ineligible", "citations": [], "confidence": 0.7}'}}]}

        def fake_urlopen(request, timeout=None):
            captured["payload"] = json.loads(request.data.decode("utf-8"))
            captured["url"] = request.full_url
            return FakeResponse(json.dumps(body).encode("utf-8"))

        env = {"OPENAI_API_KEY": "test-key", "OPENAI_BASE_URL": "http://localhost:9/v1"}
        with patch.dict(os.environ, env, clear=True), patch("urllib.request.urlopen", fake_urlopen):
            response = OpenAIAdapter("m").answer(self.contract, "base")
        self.assertEqual(captured["payload"]["temperature"], 0)
        self.assertEqual(captured["url"], "http://localhost:9/v1/chat/completions")
        self.assertEqual(response.decision, "ineligible")

    def test_openai_malformed_json_and_empty_responses_fail_gracefully(self):
        import io

        class FakeResponse(io.BytesIO):
            def __enter__(self):
                return self

            def __exit__(self, *exc):
                return False

        env = {"OPENAI_API_KEY": "test-key"}
        with patch.dict(os.environ, env, clear=True):
            with patch("urllib.request.urlopen", lambda r, timeout=None: FakeResponse(b"<html>")):
                with self.assertRaisesRegex(RuntimeError, "not valid JSON"):
                    OpenAIAdapter("m").answer(self.contract, "base")
            garbage = b'{"choices": [{"message": {"content": "no json here"}}]}'
            with patch("urllib.request.urlopen", lambda r, timeout=None: FakeResponse(garbage)):
                self.assertEqual(OpenAIAdapter("m").answer(self.contract, "base").decision, "unknown")

    def test_build_clinical_prompt_and_prediction_schema(self):
        from diffehr.adapters.base import ClinicalPrediction, build_clinical_prompt

        prompt = build_clinical_prompt(self.contract, "base")
        self.assertIn("decision", prompt)
        self.assertIn(self.contract.allowed_decisions[0], prompt)
        prediction = ClinicalPrediction(decision="  Eligible ", confidence=7)
        self.assertEqual(prediction.decision, "eligible")
        self.assertLessEqual(prediction.confidence, 1.0)


if __name__ == "__main__":
    unittest.main()
