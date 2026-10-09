from __future__ import annotations

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
    """Deterministic (greedy) open-weight Hugging Face adapter using transformers and torch."""

    def __init__(self, model_id: str, max_new_tokens: int = 512, device: str | None = None) -> None:
        self.model_id = model_id
        self.max_new_tokens = max_new_tokens
        self.device = device
        self.name = f"localhf:{model_id}"
        self._pipeline: Any | None = None

    def answer(self, contract: Contract, side: str) -> ModelResponse:
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

    def _render_prompt(self, generator: Any, prompt: str) -> str:
        tokenizer: Any = getattr(generator, "tokenizer", None)
        template = getattr(tokenizer, "chat_template", None) if tokenizer is not None else None
        if template and hasattr(tokenizer, "apply_chat_template"):
            return tokenizer.apply_chat_template(
                [{"role": "user", "content": prompt}], tokenize=False, add_generation_prompt=True
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
            dtype = torch.float32 if device == "cpu" else torch.float16
            try:
                self._pipeline = pipeline("text-generation", model=self.model_id, device=device, torch_dtype=dtype)
            except Exception as exc:
                raise RuntimeError(f"LocalHFAdapter could not load model {self.model_id}: {exc}") from exc
        return self._pipeline


LocalHFAdapter = HuggingFaceAdapter


def _extract_generated_text(output: object) -> str:
    if isinstance(output, list) and output:
        first = output[0]
        if isinstance(first, dict) and isinstance(first.get("generated_text"), str):
            return first["generated_text"]
    return str(output)
