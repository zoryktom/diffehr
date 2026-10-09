from __future__ import annotations

import json
import os
from typing import Any

from diffehr.core import Contract

from .base import ModelAdapter, ModelResponse, build_clinical_prompt, parse_model_response

CLINICAL_MODELS = (
    "BioMistral/BioMistral-7B",
    "epfl-llm/meditron-7b",
    "google/medgemma-2b",
)
BASELINE_MODELS = (
    "meta-llama/Llama-3.1-8B-Instruct",
    "mistralai/Mistral-7B-Instruct-v0.3",
    "Qwen/Qwen2.5-7B-Instruct",
)
SUPPORTED_MODELS = CLINICAL_MODELS + BASELINE_MODELS

MODEL_ALIASES: dict[str, str] = {
    "biomistral-7b": "BioMistral/BioMistral-7B",
    "meditron-7b": "epfl-llm/meditron-7b",
    "llama-3.1-8b": "meta-llama/Llama-3.1-8B-Instruct",
    "medgemma-2b": "google/medgemma-2b",
    "qwen2.5-0.5b": "Qwen/Qwen2.5-0.5B-Instruct",
    "smollm2-135m": "HuggingFaceTB/SmolLM2-135M-Instruct",
}


def resolve_model_id(name: str) -> str:
    """Map a short alias such as ``biomistral-7b`` to its Hugging Face repo id."""
    return MODEL_ALIASES.get(name.strip().lower(), name.strip())


def is_cached(model_id: str) -> bool:
    """True when the model weights are already in the local Hugging Face cache."""
    try:
        from huggingface_hub import snapshot_download

        snapshot_download(model_id, local_files_only=True)
    except Exception:
        return False
    return True


def offline_requested() -> bool:
    return os.environ.get("HF_OFFLINE", "").strip().lower() in {"1", "true", "yes"}


def select_device() -> str:
    """Return the best available torch device: cuda, then mps, then cpu."""
    try:
        import torch
    except ImportError:
        return "cpu"
    if torch.cuda.is_available():
        return "cuda"
    mps = getattr(torch.backends, "mps", None)
    if mps is not None and mps.is_available():
        return "mps"
    return "cpu"


class HuggingFaceAdapter(ModelAdapter):
    """Deterministic (greedy) open-weight Hugging Face adapter using transformers and torch.

    With ``HF_OFFLINE=1`` weights are never downloaded. If they are not already cached the adapter
    switches to ``offline_mock_mode``: it returns a fixed fixture response (first allowed decision)
    so the harness can be exercised in restricted environments. Fixture output is not model output
    and is reported separately.
    """

    def __init__(
        self,
        model_id: str,
        max_new_tokens: int = 192,
        device: str | None = None,
        offline_mock_mode: bool | None = None,
    ) -> None:
        self.model_id = resolve_model_id(model_id)
        self.max_new_tokens = max_new_tokens
        self.device = device
        if offline_mock_mode is None:
            offline_mock_mode = offline_requested() and not is_cached(self.model_id)
        self.offline_mock_mode = offline_mock_mode
        self.is_fixture = offline_mock_mode
        self.name = f"hf-fixture:{self.model_id}" if offline_mock_mode else f"localhf:{self.model_id}"
        self._pipeline: Any | None = None

    def answer(self, contract: Contract, side: str) -> ModelResponse:
        if self.offline_mock_mode:
            return self._fixture_response(contract)
        generator = self._get_pipeline()
        prompt = self._render_prompt(generator, build_clinical_prompt(contract, side))
        try:
            output = generator(
                prompt,
                max_new_tokens=self.max_new_tokens,
                do_sample=False,
                temperature=None,
                top_p=None,
                return_full_text=False,
            )
        except Exception as exc:
            raise RuntimeError(f"LocalHFAdapter generation failed for {self.model_id}: {exc}") from exc
        text = _extract_generated_text(output)
        return parse_model_response(self.name, text, contract.allowed_decisions)

    def _fixture_response(self, contract: Contract) -> ModelResponse:
        text = json.dumps(
            {
                "decision": contract.allowed_decisions[0],
                "confidence": 0.0,
                "contraindication_flagged": False,
                "clinical_rationale": "OFFLINE FIXTURE: weights unavailable, not model output.",
                "citations": [],
            }
        )
        return parse_model_response(self.name, text, contract.allowed_decisions)

    def _render_prompt(self, generator: Any, prompt: str) -> str:
        tokenizer: Any = getattr(generator, "tokenizer", None)
        template = getattr(tokenizer, "chat_template", None) if tokenizer is not None else None
        if template and hasattr(tokenizer, "apply_chat_template"):
            return str(
                tokenizer.apply_chat_template(
                    [{"role": "user", "content": prompt}], tokenize=False, add_generation_prompt=True
                )
            )
        return prompt

    def _get_pipeline(self) -> Any:
        if self._pipeline is None:
            try:
                import torch
                from transformers import pipeline
            except ImportError as exc:
                raise RuntimeError(
                    "LocalHFAdapter requires transformers and torch. Install with `pip install diffehr[hf]`."
                ) from exc
            device = self.device or select_device()
            self.device = device
            dtype = torch.float32 if device == "cpu" else torch.float16
            try:
                self._pipeline = pipeline("text-generation", model=self.model_id, device=device, dtype=dtype)
            except Exception as exc:
                raise RuntimeError(f"LocalHFAdapter could not load model {self.model_id}: {exc}") from exc
        return self._pipeline


LocalHFAdapter = HuggingFaceAdapter


def _extract_generated_text(output: object) -> str:
    if isinstance(output, list) and output:
        first = output[0]
        if isinstance(first, dict) and isinstance(first.get("generated_text"), str):
            return str(first["generated_text"])
    return str(output)
