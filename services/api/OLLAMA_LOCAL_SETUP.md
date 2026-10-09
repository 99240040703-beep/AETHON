# Run ASTRA with local Ollama

This setup uses the existing AETHON API and adds Ollama as an optional model provider. It does not replace the current OpenAI, OpenAI-compatible, or local fallback providers.

## 1. Install and start Ollama

Install Ollama for Windows from https://ollama.com/download/windows, then run:

```powershell
ollama pull qwen3:4b
ollama list
```

Ollama normally serves its local API at `http://127.0.0.1:11434`.

## 2. Configure the API process

Set these environment variables in the terminal that starts the API:

```powershell
$env:AETHON_MODEL_PROVIDER = "ollama"
$env:AETHON_MODEL_BASE_URL = "http://127.0.0.1:11434"
$env:AETHON_MODEL_NAME = "qwen3:4b"
$env:AETHON_MODEL_TIMEOUT = "120"
```

Then start the API using the repository's normal development command. The local Ollama service must be running on the same computer as the API process.

## 3. Verify

Open `/v1/model/health` on the local API and confirm the provider is `ollama`. Send a short chat message and confirm the API returns the final answer text only.

The provider sends `think: false` and the Qwen `/no_think` hint, and reads only `message.content`; it never falls back to the separate `message.thinking` field.

## Deployment note

A Render-hosted API cannot reach Ollama at `127.0.0.1` on your Windows PC. Use this provider for local development unless you deliberately configure a secure, reachable Ollama server. Do not expose Ollama publicly without appropriate network and access controls.
