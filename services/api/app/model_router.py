from __future__ import annotations

import os
import time
from typing import Any, Protocol

import httpx


class ModelProvider(Protocol):
    name: str
    def generate(self, prompt: str) -> str: ...
    def health(self) -> bool: ...


class DeterministicProvider:
    name = "deterministic"

    def generate(self, prompt: str) -> str:
        return f"AETHON received: {prompt}"

    def health(self) -> bool:
        return True


class OpenAICompatibleProvider:
    name = "openai-compatible"

    def __init__(self, base_url: str, model: str, api_key: str, timeout: float = 30.0, retries: int = 2):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_key = api_key
        self.timeout = timeout
        self.retries = max(0, retries)

    def _request(self, prompt: str) -> httpx.Response:
        last_error: Exception | None = None
        for attempt in range(self.retries + 1):
            try:
                return httpx.post(
                    f"{self.base_url}/chat/completions",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={"model": self.model, "messages": [{"role": "user", "content": prompt}]},
                    timeout=self.timeout,
                )
            except (httpx.TimeoutException, httpx.NetworkError) as exc:
                last_error = exc
                if attempt < self.retries:
                    time.sleep(min(0.25 * (2**attempt), 1.0))
        raise RuntimeError("model provider request failed after bounded retries") from last_error

    def generate(self, prompt: str) -> str:
        response = self._request(prompt)
        response.raise_for_status()
        data = response.json()
        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError("model provider returned an invalid response") from exc

    def health(self) -> bool:
        try:
            response = httpx.get(f"{self.base_url}/models", headers={"Authorization": f"Bearer {self.api_key}"}, timeout=5.0)
            return response.is_success
        except (httpx.HTTPError, OSError):
            return False


class OllamaProvider:
    """Optional local Ollama chat provider. Only final message content is exposed."""

    name = "ollama"

    def __init__(self, base_url: str = "http://127.0.0.1:11434", model: str = "qwen3:4b", timeout: float = 120.0, retries: int = 1):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self.retries = max(0, retries)

    def generate(self, prompt: str) -> str:
        if not prompt.strip():
            return "How can I help you?"
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are ASTRA, Advanced Smart Task and Reasoning Assistant. Be natural, concise, and helpful. Return only the final user-facing answer. Do not reveal private reasoning or internal fields."},
                {"role": "user", "content": prompt + "\n/no_think"},
            ],
            "think": False,
            "stream": False,
            "options": {"num_predict": int(os.getenv("AETHON_MODEL_NUM_PREDICT", "384"))},
        }
        error: Exception | None = None
        for attempt in range(self.retries + 1):
            try:
                response = httpx.post(f"{self.base_url}/api/chat", json=payload, timeout=self.timeout)
                response.raise_for_status()
                message = response.json().get("message", {})
                answer = message.get("content") if isinstance(message, dict) else None
                if not isinstance(answer, str) or not answer.strip():
                    raise RuntimeError("Ollama returned no final answer")
                return answer.strip()
            except (httpx.HTTPError, RuntimeError, ValueError) as exc:
                error = exc
                if attempt < self.retries:
                    time.sleep(min(0.25 * (2**attempt), 1.0))
        raise RuntimeError("Ollama request failed or returned no final answer") from error

    def health(self) -> bool:
        try:
            response = httpx.get(f"{self.base_url}/api/tags", timeout=5.0)
            if not response.is_success:
                return False
            models = response.json().get("models", [])
            return any(isinstance(item, dict) and item.get("name") == self.model for item in models)
        except (httpx.HTTPError, OSError, ValueError, AttributeError):
            return False


class ModelRouter:
    def __init__(self, provider: ModelProvider | None = None):
        self.provider = provider or self._from_environment()

    @staticmethod
    def _from_environment() -> ModelProvider:
        provider = os.getenv("AETHON_MODEL_PROVIDER", "deterministic").strip().lower()
        if provider == "deterministic":
            return DeterministicProvider()
        if provider == "ollama":
            base_url = os.getenv("AETHON_MODEL_BASE_URL", "http://127.0.0.1:11434").strip()
            model = os.getenv("AETHON_MODEL_NAME", "qwen3:4b").strip()
            if not base_url or not model:
                raise RuntimeError("AETHON_MODEL_BASE_URL and AETHON_MODEL_NAME are required for Ollama")
            return OllamaProvider(
                base_url=base_url,
                model=model,
                timeout=float(os.getenv("AETHON_MODEL_TIMEOUT", "120")),
            )
        if provider in {"openai", "openai-compatible"}:
            base_url = os.getenv("AETHON_MODEL_BASE_URL")
            model = os.getenv("AETHON_MODEL_NAME")
            api_key = os.getenv("AETHON_MODEL_API_KEY")
            if not all((base_url, model, api_key)):
                raise RuntimeError("AETHON_MODEL_BASE_URL, AETHON_MODEL_NAME and AETHON_MODEL_API_KEY are required")
            return OpenAICompatibleProvider(base_url, model, api_key)
        raise RuntimeError(f"unsupported model provider: {provider}")

    def generate(self, prompt: str) -> str:
        return self.provider.generate(prompt)

    def health(self) -> bool:
        return self.provider.health()
