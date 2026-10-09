from __future__ import annotations

import json
import os
import socket
import urllib.error
import urllib.request

from diffehr.core import Contract

from .base import ModelAdapter, ModelResponse, parse_model_response


class OpenAIAdapter(ModelAdapter):
    def __init__(self, model_id: str = "gpt-5-mini", timeout: int = 90) -> None:
        self.model_id = model_id
        self.timeout = timeout
        self.name = f"openai:{model_id}"

    def answer(self, contract: Contract, side: str) -> ModelResponse:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is not set")
        base_url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
        url = base_url.rstrip("/") + "/responses"
        payload = {
            "model": self.model_id,
            "input": contract.prompt(side),
            "temperature": 0,
        }
        request = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                data = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"OpenAI API error {exc.code}: {body}") from exc
        except (urllib.error.URLError, TimeoutError, socket.timeout) as exc:
            raise RuntimeError(f"OpenAI API request failed: {exc}") from exc
        except json.JSONDecodeError as exc:
            raise RuntimeError("OpenAI API response was not valid JSON") from exc
        text = _extract_response_text(data)
        if not text.strip():
            raise RuntimeError("OpenAI API response did not contain text output")
        return parse_model_response(self.name, text, contract.allowed_decisions)


def _extract_response_text(data: object) -> str:
    if isinstance(data, dict) and isinstance(data.get("output_text"), str):
        return data["output_text"]
    texts: list[str] = []

    def walk(value: object) -> None:
        if isinstance(value, dict):
            if isinstance(value.get("text"), str):
                texts.append(value["text"])
            for child in value.values():
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)

    walk(data)
    return "\n".join(texts) if texts else json.dumps(data)
