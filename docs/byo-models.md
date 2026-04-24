<!-- @wbx-modified copilot-a3f7·MTN | 2026-04-23 | Wk2: BYO embedder + summarizer docs | prev: NEW -->
# Bring Your Own Models

Recall is designed to run entirely on your hardware with the models *you*
already trust. Two seams are pluggable:

1. **Embedder** — converts text into vectors for the vector store.
2. **Summarizer** — condenses long narrative content into shorter retrieval
   chunks (used today by `session_close`; more callers coming).

Both default to fully-offline implementations so a fresh `docker run` works
out of the box. You only set env vars when you want to override.

---

## Embedder

| Backend   | `RECALL_EMBEDDER` value | When to use                                           |
|-----------|-------------------------|-------------------------------------------------------|
| Default   | `default` *(or unset)*  | Bundled all-MiniLM-L6-v2. Offline. Fine for laptops.  |
| OpenAI    | `openai`                | OpenAI / Azure-OpenAI / OpenAI-compatible endpoints.  |
| Ollama    | `ollama`                | Local Ollama. Recommended for on-prem / regulated data.|

### `default`

No config needed.

### `openai`

```bash
RECALL_EMBEDDER=openai
RECALL_EMBED_MODEL=text-embedding-3-small      # default if unset
RECALL_EMBED_API_KEY=sk-...                    # or OPENAI_API_KEY
RECALL_EMBED_BASE_URL=https://your-azure-openai.openai.azure.com  # optional
```

Requires `pip install openai`.

### `ollama`

```bash
RECALL_EMBEDDER=ollama
RECALL_EMBED_MODEL=nomic-embed-text            # or mxbai-embed-large, etc
RECALL_EMBED_ENDPOINT=http://ollama:11434      # default localhost:11434
```

Requires `pip install httpx` and a running Ollama server with the embedding
model pulled (`ollama pull nomic-embed-text`).

---

## Summarizer

| Backend   | `RECALL_SUMMARIZER` value | When to use                                       |
|-----------|---------------------------|---------------------------------------------------|
| Noop      | `noop` *(or unset)*       | Store raw content verbatim. No LLM, no network.   |
| OpenAI    | `openai`                  | OpenAI / Azure / OpenAI-compatible chat API.      |
| Ollama    | `ollama`                  | Local Ollama chat API.                            |

### `noop`

No config needed. `session_close` and friends store the raw narrative as-is.

### `openai`

```bash
RECALL_SUMMARIZER=openai
RECALL_LLM_MODEL=gpt-4o-mini                   # default if unset
RECALL_LLM_API_KEY=sk-...                      # or OPENAI_API_KEY
RECALL_LLM_BASE_URL=https://your-azure-openai.openai.azure.com  # optional
```

### `ollama`

```bash
RECALL_SUMMARIZER=ollama
RECALL_LLM_MODEL=llama3.1                      # or mistral, qwen2.5, etc
RECALL_LLM_ENDPOINT=http://ollama:11434
```

---

## Why this matters

- **Compliance**: lenders, hospitals, and government tenants often cannot
  ship content to a public-cloud LLM. Pointing at on-prem Ollama or your
  own Azure-OpenAI tenant keeps the data in your network.
- **Cost**: you're already paying for inference. Recall layers on top
  instead of double-billing through a separate embedding/LLM vendor.
- **Lock-in**: the seam is a Protocol, not a hard dependency. Drop in
  Bedrock, Voyage, vLLM, llama.cpp — anything that speaks the OpenAI or
  Ollama API shape works in <50 lines.

---

## Mixing and matching

You can run different backends for embeddings and summarization. Common
patterns:

| Use case                    | Embedder | Summarizer |
|-----------------------------|----------|------------|
| Dev laptop                  | default  | noop       |
| On-prem regulated tenant    | ollama   | ollama     |
| Hosted production           | openai   | openai     |
| Hybrid (embed local, LLM cloud) | ollama | openai   |

The `default` + `noop` combination has zero external dependencies and is
what you get with no env vars set — useful for first-touch installs and CI.

---

## Failure modes

- If a configured external service is unreachable at startup, Recall logs
  the error and falls back to `default` / `noop` so the server still binds.
- If a summarizer call fails mid-request (network blip, rate limit, etc.),
  the calling tool falls back to storing raw content for that one operation.
  Reflections are never lost to LLM errors.
