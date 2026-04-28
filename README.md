<!-- @wbx-modified copilot-b1c4 | 2026-04-27 23:58 MTN | v0.3.3 | added ™ to H1 brand | prev: copilot-a3f7@2026-04-24 -->
<div align="center">

# Recall&trade;

**Open-source memory for AI agents. MCP-native. Self-hosted. One Docker image.**

[![Tests](https://github.com/RecallWorks/Recall/actions/workflows/test.yml/badge.svg)](https://github.com/RecallWorks/Recall/actions/workflows/test.yml)
[![Docker](https://github.com/RecallWorks/Recall/actions/workflows/docker.yml/badge.svg)](https://github.com/RecallWorks/Recall/actions/workflows/docker.yml)
[![PyPI](https://img.shields.io/pypi/v/recall-client?label=pypi%3A%20recall-client&logo=pypi&logoColor=white)](https://pypi.org/project/recall-client/)
[![npm](https://img.shields.io/npm/v/@recallworks/recall-client?label=npm%3A%20%40recallworks%2Frecall-client&logo=npm&logoColor=white)](https://www.npmjs.com/package/@recallworks/recall-client)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue?logo=python&logoColor=white)](pyproject.toml)
[![MCP](https://img.shields.io/badge/MCP-compatible-7c3aed)](https://modelcontextprotocol.io)
[![Container](https://img.shields.io/badge/ghcr.io-recallworks%2Frecall-2496ED?logo=docker&logoColor=white)](https://github.com/RecallWorks/Recall/pkgs/container/recall)

[**OSS quickstart**](#five-minute-install) · [**Recall Pro →**](#recall-open-source-vs-recall-pro-vs-hosted) · [**Book a demo**](mailto:sales@recall.works?subject=Recall%20demo) · [**IceWhisperer for Encompass**](https://icewhisperer.ai)

</div>

> Your agent forgets every session. Recall fixes that — with a small,
> opinionated memory surface that any MCP-speaking agent (or any HTTP
> client) can drive. Append-only, rebuildable, soft-delete by design.

```text
   ┌─────────────┐    MCP / HTTP    ┌──────────────────────────┐
   │  AI agent   │ ───────────────► │  Recall (one container)  │
   │  (Copilot,  │                  │   • 13 memory tools      │
   │   Claude,   │  remember/recall │   • BYO embedder + LLM   │
   │   Cursor,   │ ◄─────────────── │   • Append-only artifacts│
   │   custom)   │                  │   • Auto-snapshot to disk│
   └─────────────┘                  └──────────────────────────┘
```

---

## Five-minute install

**1. Run the server:**

```bash
docker run -d --name recall \
  -p 8787:8787 \
  -e API_KEY=changeme \
  -v recall-data:/data \
  ghcr.io/recallworks/recall:latest
```

**2. Talk to it — pick your stack:**

```bash
# Raw HTTP (any language)
curl -H "X-API-Key: changeme" \
     -H "Content-Type: application/json" \
     -d '{"content":"first memory","tags":"hello"}' \
     http://localhost:8787/tool/remember
```

```python
# Python
pip install recall-client

from recall_client import RecallClient
with RecallClient("http://localhost:8787", api_key="changeme") as c:
    c.remember("first memory", tags="hello")
    print(c.recall("memory").result)
```

```ts
// TypeScript / JavaScript (Node 18+, Bun, Deno, browser)
npm install @recallworks/recall-client

import { RecallClient } from "@recallworks/recall-client";
const c = new RecallClient({ baseUrl: "http://localhost:8787", apiKey: "changeme" });
await c.remember("first memory", { tags: "hello" });
console.log((await c.recall("memory")).result);
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

If you want a managed service, see [Recall Cloud](#recall-open-source-vs-recall-pro-vs-hosted) below. If you want a brain you fully own, this OSS core is enough.

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

## Recall Open Source vs. Recall Pro vs. Hosted

| Capability                          | OSS (this repo) | **Recall Pro** | **Recall Cloud** |
|-------------------------------------|:---------------:|:--------------:|:----------------:|
| Single-tenant Docker image          | ✅              | ✅             | n/a (hosted)     |
| 13 memory tools, MCP + HTTP         | ✅              | ✅             | ✅               |
| BYO embedder + LLM                  | ✅              | ✅             | ✅               |
| Append-only artifacts + auto-snapshot| ✅             | ✅             | ✅               |
| Multi-tenant, SSO, RBAC             | —               | ✅             | ✅               |
| Audit log + retention policy        | —               | ✅             | ✅               |
| Cross-session entity graph          | —               | ✅             | ✅               |
| PII sanitization pipeline           | —               | ✅             | ✅               |
| Snapshot replication / DR           | —               | ✅             | ✅               |
| Vendor support + SLA                | community       | business hours | 24×7             |
| Hosted on our infra                 | —               | —              | ✅               |
| **Pricing**                         | **free**        | **from $99/mo per node** | **from $0.10 per 1k tools** |

**Recall Pro** ships from the `enterprise/` tree under a [Business Source License](LICENSE-COMMERCIAL.md) — source-available, 5-seat free Additional Use Grant, converts to MIT after 3 years. Buy a license and the `enterprise/` modules light up alongside your OSS install.

**Recall Cloud** is the hosted multi-tenant version. Same tools, no infra. Reach out for early-access pricing.

➡️ Talk to sales: `sales@recall.works` · Book a 20-min walkthrough: `https://recall.works/demo`

---

## Vertical builds powered by Recall

Recall is the engine. We ship turn-key vertical brains on top of it:

- **[IceWhisperer](https://icewhisperer.ai)** — the memory + workflow brain for ICE Mortgage Technology / Encompass shops. Pre-loaded SDK index, settings recipes, plugin audits, drift detection. Pilots from $250/mo.

If you want a vertical brain for *your* industry, we'll build it. Email `partners@recall.works`.

---

## Maintainers

Reach the maintainers at `maintainers@recall.works`. Issues and PRs welcome on GitHub.
