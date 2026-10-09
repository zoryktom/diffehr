from __future__ import annotations

from typing import Any

from diffehr.core import Contract

from .base import ModelAdapter, ModelResponse, parse_model_response


class LocalHFAdapter(ModelAdapter):
    def __init__(self, model_id: str, max_new_tokens: int = 512) -> None:
        self.model_id = model_id
        self.max_new_tokens = max_new_tokens
        self.name = f"localhf:{model_id}"
        self._pipeline: Any | None = None

    def answer(self, contract: Contract, side: str) -> ModelResponse:
        generator = self._get_pipeline()
        try:
            output = generator(
                contract.prompt(side),
                max_new_tokens=self.max_new_tokens,
                do_sample=False,
                return_full_text=False,
            )
        except Exception as exc:
            raise RuntimeError(f"LocalHFAdapter generation failed for {self.model_id}: {exc}") from exc
        text = _extract_generated_text(output)
        return parse_model_response(self.name, text, contract.allowed_decisions)

    def _get_pipeline(self) -> Any:
        if self._pipeline is None:
            try:
                from transformers import pipeline
            except ImportError as exc:
                raise RuntimeError(
                    "LocalHFAdapter requires transformers. Install with `pip install diffehr[hf]`."
                ) from exc
            try:
                self._pipeline = pipeline("text-generation", model=self.model_id)
            except Exception as exc:
                raise RuntimeError(f"LocalHFAdapter could not load model {self.model_id}: {exc}") from exc
        return self._pipeline


def _extract_generated_text(output: object) -> str:
    if isinstance(output, list) and output:
        first = output[0]
        if isinstance(first, dict) and isinstance(first.get("generated_text"), str):
            return first["generated_text"]
    return str(output)
