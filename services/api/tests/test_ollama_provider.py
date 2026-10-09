import httpx

from app.model_router import ModelRouter, OllamaProvider


def test_ollama_response_returns_only_final_content(monkeypatch):
    seen = {}

    def fake_post(url, **kwargs):
        seen["url"] = url
        seen["payload"] = kwargs["json"]
        return httpx.Response(
            200,
            json={"message": {"content": "Hello from ASTRA", "thinking": "not shown"}},
        )

    monkeypatch.setattr(httpx, "post", fake_post)
    answer = OllamaProvider().generate("Hi ASTRA")

    assert answer == "Hello from ASTRA"
    assert seen["url"] == "http://127.0.0.1:11434/api/chat"
    assert seen["payload"]["think"] is False
    assert seen["payload"]["messages"][-1]["content"].endswith("/no_think")


def test_ollama_router_environment(monkeypatch):
    monkeypatch.setenv("AETHON_MODEL_PROVIDER", "ollama")
    monkeypatch.setenv("AETHON_MODEL_BASE_URL", "http://127.0.0.1:11434")
    monkeypatch.setenv("AETHON_MODEL_NAME", "qwen3:4b")

    router = ModelRouter()

    assert isinstance(router.provider, OllamaProvider)
    assert router.provider.model == "qwen3:4b"
