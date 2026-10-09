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
        response = parse_model_response("mock", "not valid json and no allowed decision", self.contract.allowed_decisions)
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


if __name__ == "__main__":
    unittest.main()
