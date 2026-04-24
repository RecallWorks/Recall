<!-- @wbx-modified copilot-a3f7·MTN | 2026-04-23 | Wk2 polish: tighter value prop, comparison table, fixed license link, contributor pointer | prev: copilot-c4a1@2026-04-23 -->
# Recall

> **Open-source agent memory for the MCP era.**
> Self-hosted. MIT-licensed core. One Docker image.
> [recall.works](https://recall.works)

Your agent forgets every session. Recall fixes that — with a small, opinionated
memory surface that any MCP-speaking agent (or any HTTP client) can drive.

---

## Five-minute install

```bash
docker run -d --name recall \
  -p 8787:8787 \
  -e API_KEY=changeme \
  -v recall-data:/data \
  ghcr.io/recallworks/recall:latest
```

```bash
curl -H "Authorization: Bearer changeme" \
     -H "Content-Type: application/json" \
     -d '{"content":"first memory","tags":["hello"]}' \
     http://localhost:8787/tool/remember
```

Full walkthrough: [docs/quickstart.md](docs/quickstart.md).

---

## What you get

- **13 tools** — `remember`, `recall`, `reflect`, `anti_pattern`, `checkpoint`,
  `pulse`, `session_close`, `index_file`, `reindex`, `snapshot_index`,
  `memory_stats`, `forget`, `maintenance`.
- **Two transports** — plain HTTP (`POST /tool/{name}`) and MCP over SSE.
  Drop into Copilot, Claude Code, Cursor, or any MCP client.
- **Bring your own models** — pluggable embedder (default / OpenAI /
  Ollama) and summarizer (noop / OpenAI / Ollama). Run fully offline,
  fully on-prem, or against your own Azure-OpenAI tenant. See
  [docs/byo-models.md](docs/byo-models.md).
- **Durable by default** — ephemeral live store with auto-snapshot to disk;
  container restarts come up whole.
- **Append-only artifacts** — every write also lands as a `.md` file. If the
  vector store ever burns down, `reindex` rebuilds it from the artifacts.
- **`forget` is soft-archive** — guardrail wired into the OSS code itself, not
  bolted on as policy. Memory you delete can be recovered.

---

## How it's different

|                       | Recall                                            | Mem0 / Letta / Zep              |
|-----------------------|---------------------------------------------------|---------------------------------|
| **License (core)**    | MIT                                               | mixed; SaaS-first               |
| **Self-host**         | one `docker run`                                  | varies, often non-trivial       |
| **BYO embedder**      | default / OpenAI / Ollama (env var)               | usually fixed                   |
| **BYO LLM**           | noop / OpenAI / Ollama (env var)                  | usually fixed                   |
| **Storage model**     | append-only artifacts + vector index, rebuildable | live DB only                    |
| **`delete`**          | soft-archive by design                            | hard delete                     |
| **Tool surface**      | 13 opinionated tools (memory + workflow)          | embedding + retrieval primitives|
| **MCP-native**        | yes, plus plain HTTP                              | partial / via wrapper           |
| **Ops model**         | single binary, single container                   | multi-service stack             |

If you want a managed service, that's coming under `enterprise/`. If you want
a brain you fully own, the OSS core is enough.

---

## Repo layout

| Path                    | What                                  |
|-------------------------|---------------------------------------|
| `src/recall/`           | OSS server (MIT)                      |
| `src/recall/tools/`     | One module per tool                   |
| `src/recall/transport/` | HTTP + MCP/SSE adapters               |
| `docker/single-tenant/` | Reference Dockerfile + compose        |
| `tests/`                | pytest suite (no Docker required)     |
| `docs/`                 | Quickstart, conventions, architecture |
| `enterprise/`           | Multi-tenant, SSO, control plane (BSL)|

---

## Conventions

These are the *practices* that make the tools pay off. Pick what fits.

- [Cold-start ritual](docs/conventions/cold-start-ritual.md) — opening
  protocol every session should run.
- [Branding](docs/conventions/branding.md) — signed-edit headers so you can
  trace which agent touched which file when.

---

## Status

Alpha. The code in `src/recall/` is **extracted from a hosted production brain
that has served thousands of sessions**, then sanitized of org-specific
paths, extensions, and tenant data. Expect breaking changes before 1.0; pin
the image tag.

---

## Contributing

Yes — please read [CONTRIBUTING.md](CONTRIBUTING.md) first. We accept bug
fixes, new `Store` backends, doc improvements, and anti-pattern entries. We
don't accept architectural rewrites without prior discussion.

Security issues: see [SECURITY.md](SECURITY.md).

---

## License

- `src/recall/`, `clients/`, `docker/single-tenant/`, `docs/`, `examples/` — **MIT** ([LICENSE](LICENSE))
- `enterprise/` — **BSL 1.1**, 5-seat additional-use grant, converts to MIT after 3 years ([LICENSE-COMMERCIAL.md](LICENSE-COMMERCIAL.md))

---

## Maintainers

Reach the maintainers at `maintainers@recall.works`. Issues and PRs welcome on GitHub.
