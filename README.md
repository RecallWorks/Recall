<!-- @wbx-modified copilot-a3f7 | 2026-04-30 01:30 MTN | v0.5.5-readme | add mcp-name marker for MCP Registry namespace verify | prev: copilot-a3f7@2026-04-30 03:25 MTN -->
<!-- mcp-name: io.github.recallworks/recall -->
<div align="center">

# Recall&trade;

**A better memory server for AI agents — works for one, scales to many.**
**Local, free, zero-config, MCP-native. Your data stays on your machine.**

[![Tests](https://github.com/RecallWorks/Recall/actions/workflows/test.yml/badge.svg)](https://github.com/RecallWorks/Recall/actions/workflows/test.yml)
[![Docker](https://github.com/RecallWorks/Recall/actions/workflows/docker.yml/badge.svg)](https://github.com/RecallWorks/Recall/actions/workflows/docker.yml)
[![PyPI](https://img.shields.io/pypi/v/ai-recallworks?label=pypi%3A%20ai-recallworks&logo=pypi&logoColor=white)](https://pypi.org/project/ai-recallworks/)
[![npm](https://img.shields.io/npm/v/@recallworks/recall-client?label=npm%3A%20%40recallworks%2Frecall-client&logo=npm&logoColor=white)](https://www.npmjs.com/package/@recallworks/recall-client)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue?logo=python&logoColor=white)](pyproject.toml)
[![MCP](https://img.shields.io/badge/MCP-compatible-7c3aed)](https://modelcontextprotocol.io)
[![Container](https://img.shields.io/badge/ghcr.io-recallworks%2Frecall-2496ED?logo=docker&logoColor=white)](https://github.com/RecallWorks/Recall/pkgs/container/recall)

[**Quickstart**](#one-line-install-claude-desktop-vs-code-cursor) · [**vs. mem0/Letta/Zep**](#how-is-this-different-from-mem0--letta--zep) · [**Multi-agent**](#scaling-up-coordination-when-you-run-more-than-one-agent) · [**Recall Pro →**](#recall-open-source-vs-recall-pro-vs-hosted) · [**Book a demo**](mailto:sales@recall.works?subject=Recall%20demo)

</div>

> Without a memory server, every Claude / Copilot / Cursor conversation
> starts cold. You re-explain the codebase, the conventions, the
> decisions, the gotchas — every time. Recall fixes that.

## Start here: what Recall does for one developer, one AI

Install it once, point your MCP client at it, and your AI now:

- **Remembers across sessions** — "what did we decide about the auth
  flow last week?" returns the actual decision, not a hallucination
- **Indexes your code and docs** — `index_file` + `recall` = local
  semantic RAG over your repo
- **Cites where the answer came from** — `answer` returns text plus
  the chunks it pulled from
- **Builds project knowledge** — every `checkpoint`, `reflect`, and
  `anti_pattern` becomes searchable later
- **Survives restarts** — append-only artifacts on disk, vector store
  rebuildable from them

One `pip install`, one config block, done. No API key. No external
service. No per-token bill. MIT license. **This is what 95% of users
will ever use Recall for.**

---

## How is this different from mem0 / Letta / Zep?

Recall does the same job they do — persistent memory across AI sessions,
semantic recall, "remember what the user said last week." The difference
is *where* and *how*:

| | mem0 / Letta / Zep | Recall |
|---|---|---|
| **Where memory lives** | Their cloud | Your `~/.recall/` |
| **API key required** | Yes | No |
| **Cost** | Per-token / monthly SaaS | Free |
| **Embeddings** | Their service | Local ONNX (offline) |
| **Network calls** | Every recall | Zero |
| **Air-gappable** | No | Yes |
| **MCP-native** | Wrapper or SDK | Built on MCP |
| **Multi-agent coordination** | None | 6 primitives |

If you're happy paying a hosted memory provider per token, those are
great products and you don't need Recall. If you'd rather your AI's
memory live on your laptop or your own server, free and offline,
that's what Recall is for.

---

## Scaling up: coordination when you run more than one agent

The same install that gives one developer a personal AI memory also
works as a **shared brain** when more than one agent talks to it. Two
Copilot windows. A planner + executor pair. Three Claude instances
dividing up a refactor. A `pre-commit` agent and a `code-review` agent
on the same PR. They all `remember` and `recall` from the same store.

That introduces a new problem none of the hosted memory services have
even tried to solve: **agents stepping on each other.** Agent A starts
refactoring `src/auth.py`. Agent B, in another window, rewrites the
same file with no idea A is mid-edit. Whoever saves last wins. The
other agent's work is gone.

Recall ships six MCP primitives that turn parallel agents from a
clobber-fest into a coordinated team:

| Tool                         | What it does                                                  |
| ---------------------------- | ------------------------------------------------------------- |
| `claim(resource, agent)`     | Soft-lock a file/table/URL with an auto-expiring TTL          |
| `release(resource, agent)`   | Drop the lock (soft-archive — audit trail survives)           |
| `who_has(resource)`          | "Is anyone editing `src/foo.py` right now?"                   |
| `claims()`                   | All active locks across all agents                            |
| `handoff(to_agent, ...)`     | Explicit work transfer with intent + files + context          |
| `pulse_others(self_agent)`   | The N most recent checkpoints from agents *other than you*    |

Claims are advisory (like git locks) — Recall doesn't physically stop
a second agent from writing, but every well-behaved client checks
first. TTLs prevent a crashed agent from freezing a resource forever.
Releases soft-archive (per the project-wide delete=archive rule) so
the audit trail of who held what when survives.

If you're a single user, these tools just sit there unused. If you
ever scale up to multiple agents, they're already there.

```text
   ┌──────────────┐                           ┌──────────────┐
   │  Agent a3f7  │      claim(file, ttl)     │  Agent b1c4  │
   │  Claude #1   │ ───────────┐  ┌─────────► │  Claude #2   │
   └──────┬───────┘            ▼  │           └──────┬───────┘
          │              ┌────────┴───────┐          │
          │   remember   │     Recall     │   pulse  │
          ├────────────► │ • shared memory│ ◄────────┤
          │              │ • claims/locks │          │
          │   handoff    │ • handoffs     │  handoff │
          ├────────────► │ • who_has      │ ◄────────┤
          │              └────────────────┘          │
          ▼                                          ▼
       22 MCP tools — Copilot, Claude, Cursor, custom
```

**22 MCP tools total** — 16 memory tools every user gets, plus the 6
coordination primitives that activate when you scale up.

---

## One-line install (Claude Desktop, VS Code, Cursor)

Recall ships as a stdio MCP server. Zero config — no API keys, no Docker, no
ports. Memory lives in `~/.recall/`.

```bash
pip install "ai-recallworks[mcp]"
```

Then add Recall to your MCP client config:

**Claude Desktop** (`~/Library/Application Support/Claude/claude_desktop_config.json`
on macOS, `%APPDATA%\Claude\claude_desktop_config.json` on Windows):

```json
{
  "mcpServers": {
    "recall": {
      "command": "recall-mcp"
    }
  }
}
```

**VS Code** (`mcp.json` in your workspace or user settings):

```json
{
  "servers": {
    "recall": {
      "command": "recall-mcp"
    }
  }
}
```

Restart the client. Your agent now has persistent memory across sessions.
Embeddings run fully offline (Chroma's bundled all-MiniLM-L6-v2). Upgrade
to Ollama / OpenAI / Voyage embeddings via env vars when you want.

---

## Five-minute install (HTTP / multi-user / team)

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
# Python (use requests/httpx — no SDK pkg needed)
import requests
h = {"X-API-Key": "changeme", "Content-Type": "application/json"}
requests.post("http://localhost:8787/tool/remember", headers=h,
              json={"content": "first memory", "tags": "hello"})
print(requests.post("http://localhost:8787/tool/recall", headers=h,
                    json={"query": "memory"}).json()["result"])
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
