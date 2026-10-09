from __future__ import annotations

import json

from diffehr.core import Contract

from .base import ModelAdapter, ModelResponse


class OracleAdapter(ModelAdapter):
    name = "oracle"

    def answer(self, contract: Contract, side: str) -> ModelResponse:
        expected = contract.expected_decision_for_side(side)
        citations = contract.expected.required_citations.get(side, ())
        payload = {
            "decision": expected,
            "citations": list(citations),
            "rationale": "Oracle baseline returns the hidden contract answer for pipeline validation.",
            "confidence": 1.0,
        }
        return ModelResponse(
            model=self.name,
            decision=expected,
            citations=tuple(citations),
            rationale=payload["rationale"],
            confidence=1.0,
            raw_text=json.dumps(payload),
        )
