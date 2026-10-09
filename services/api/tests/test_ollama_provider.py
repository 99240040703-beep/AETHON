import httpx

from aethon.model_router import ModelRouter, OllamaProvider


def test_ollama_provider_sends_no_think_and_returns_only_content(monkeypatch):
    seen = {}

    def fake_post(url, **kwargs):
        seen["url"] = url
        seen["payload"] = kwargs["json"]
        return httpx.Response(
            200,
            json={
                "message": {
                    "content": "Hi! I'm ASTRA. I can help you research, code, and create.",
                    "thinking": "This internal field must not be returned.",
                }
            },
        )

    monkeypatch.setattr(httpx, "post", fake_post)
    provider = OllamaProvider()
    answer = provider.generate("Context for the conversation", user_text="Hi ASTRA")

    assert answer.startswith("Hi! I'm ASTRA")
    assert "internal field" not in answer
    assert seen["url"] == "http://127.0.0.1:11434/api/chat"
    assert seen["payload"]["think"] is False
    assert seen["payload"]["stream"] is False
    assert seen["payload"]["messages"][-1]["content"].endswith("/no_think")


def test_ollama_provider_selected_from_environment(monkeypatch):
    monkeypatch.setenv("AETHON_MODEL_PROVIDER", "ollama")
    monkeypatch.setenv("AETHON_MODEL_BASE_URL", "http://127.0.0.1:11434")
    monkeypatch.setenv("AETHON_MODEL_NAME", "qwen3:4b")

    router = ModelRouter()

    assert isinstance(router.provider, OllamaProvider)
    assert router.provider.model == "qwen3:4b"
    assert router.provider.base_url == "http://127.0.0.1:11434"
