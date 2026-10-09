# AETHON / ASTRA hybrid AI setup

AETHON keeps its existing model router and supports two deployment modes:

- **Cloud (Render):** use the existing OpenAI Responses provider. The API key stays in Render environment variables.
- **Local (your Windows PC):** use Ollama with the already-downloaded `qwen3:4b` model. The local API key is not needed.

These modes share the same router interface. Render cannot reach `127.0.0.1:11434` on your PC; localhost always means the machine/container running AETHON.

## Cloud AI on Render

1. Create an API key from your chosen provider's official developer dashboard. For OpenAI, visit https://platform.openai.com/api-keys and create a secret key. API usage may cost money; review billing and usage limits first.
2. In the Render dashboard, open the `aethon-personal-ai` service and select **Environment**.
3. Add/update these variables. Never put the secret in source code, GitHub, screenshots, or chat.

   - `AETHON_MODEL_PROVIDER` = `openai`
   - `AETHON_MODEL_API_KEY` = your newly created secret key
   - `AETHON_MODEL_BASE_URL` = `https://api.openai.com/v1`
   - `AETHON_MODEL_NAME` = a model currently enabled for your API account (check the provider dashboard/docs)
   - `AETHON_WEB_SEARCH` = `true` only if you want to enable the Responses API web-search tool and it is available for your account

4. Save the environment settings and let Render restart/redeploy the service.
5. Verify:
   - `/health` returns `ok: true`
   - `/v1/model/health` reports provider `openai`, configured `true`, and the chosen model
   - Use the existing ASTRA chat UI to ask a fresh question. Do not send the API key in a chat message.

The code's prior default model name may not be enabled for every API account. Choose a model explicitly available to your account instead of assuming the default is valid.

## Local Qwen 3 4B on Windows

Ensure Ollama is running and `ollama list` shows `qwen3:4b`. In the same terminal used to start the AETHON API, set:

```powershell
$env:AETHON_MODEL_PROVIDER = "ollama"
$env:AETHON_MODEL_BASE_URL = "http://127.0.0.1:11434"
$env:AETHON_MODEL_NAME = "qwen3:4b"
$env:AETHON_MODEL_TIMEOUT = "120"
$env:AETHON_OLLAMA_NUM_PREDICT = "512"
cd services/api
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Check `http://127.0.0.1:8000/v1/model/health` and use the local AETHON chat UI/API. The provider requests non-streaming output and only returns Ollama's `message.content`; the separate `thinking` field is not returned to the user.

## Security and operations

- Keep provider keys only in secret environment-variable stores.
- Do not expose the Ollama port directly to the public internet.
- Use a VPN or authenticated private gateway if you later need a cloud service to call a local model; do not use an unauthenticated public tunnel.
- Cloud and local models can produce different answers. A cloud deployment does not silently claim to be using your PC's Qwen model.
