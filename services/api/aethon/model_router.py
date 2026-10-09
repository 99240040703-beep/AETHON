"""Optional local Ollama provider for ASTRA."""
from __future__ import annotations
import os
import time
from typing import Any
import httpx
from app.model_router import *
from app.model_router import ModelRouter as _BaseModelRouter

class OllamaProvider:
    name = "ollama"
    def __init__(self, base_url="http://127.0.0.1:11434", model="qwen3:4b", timeout=120.0, retries=1):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self.retries = max(0, retries)

    def generate(self, prompt: str, user_text: str | None = None) -> str:
        user_text = (user_text or "").strip() or prompt.strip()
        if not user_text:
            return "How can I help you?"
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are ASTRA, Advanced Smart Task and Reasoning Assistant. Be natural, concise, and helpful. Never identify yourself as Qwen. Return only the final answer.\n\nContext:\n" + prompt},
                {"role": "user", "content": user_text + "\n/no_think"},
            ],
            "think": False,
            "stream": False,
            "options": {"num_predict": int(os.getenv("AETHON_MODEL_NUM_PREDICT", "384"))},
        }
        error = None
        for attempt in range(self.retries + 1):
            try:
                response = httpx.post(self.base_url + "/api/chat", json=payload, timeout=self.timeout)
                if response.status_code >= 400:
                    raise RuntimeError(f"Ollama returned HTTP {response.status_code}")
                message = response.json().get("message", {})
                answer = message.get("content") if isinstance(message, dict) else None
                if not isinstance(answer, str) or not answer.strip():
                    raise RuntimeError("Ollama returned no final answer")
                return answer.strip()
            except (httpx.HTTPError, RuntimeError, ValueError) as exc:
                error = exc
                if attempt < self.retries:
                    time.sleep(0.25 * (attempt + 1))
        raise RuntimeError("Ollama request failed") from error

    def health(self) -> bool:
        try:
            response = httpx.get(self.base_url + "/api/tags", timeout=5.0)
            if not response.is_success:
                return False
            models = response.json().get("models", [])
            return any(isinstance(m, dict) and m.get("name") == self.model for m in models)
        except (httpx.HTTPError, OSError, ValueError):
            return False

class ModelRouter(_BaseModelRouter):
    @staticmethod
    def _from_environment() -> ModelProvider:
        if os.getenv("AETHON_MODEL_PROVIDER", "auto").strip().lower() == "ollama":
            return OllamaProvider(
                base_url=os.getenv("AETHON_MODEL_BASE_URL", "http://127.0.0.1:11434"),
                model=os.getenv("AETHON_MODEL_NAME", "qwen3:4b"),
                timeout=float(os.getenv("AETHON_MODEL_TIMEOUT", "120")),
            )
        return _BaseModelRouter._from_environment()
