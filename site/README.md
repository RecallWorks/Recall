# Recall™ — Agent OS

> **Durable memory, audit, and continuity for AI coding agents.**

[![Live Site](https://img.shields.io/badge/site-recall.works-blue)](https://stevepaltridge.github.io/agent-os/)
[![PyPI](https://img.shields.io/pypi/v/ai-recallworks)](https://pypi.org/project/ai-recallworks/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

---

## The Problem

Modern AI coding agents are **stateless goldfish**. Every conversation starts cold. Memory is whatever the host platform decides to keep. Multi-day campaigns degrade into *"we already discussed this"* loops until the context window compacts your history into oblivion.

## The Solution

**Recall treats the agent like a contractor who clocks in every day.** They don't remember yesterday from their own head — they read the project log. The log lives on disk, in a vector brain, and in immutable cloud storage.

```
Hot tier   → /memories/         (auto-loaded every turn)
Warm tier  → /memories/session/  (current conversation)
Cold tier  → vector brain        (22 MCP tools, semantic search)
Archive    → Azure Blob WORM     (<$1/mo, 7-year retention)
```

## Six Pillars

| # | Pillar | What it does |
|---|--------|-------------|
| 1 | **Memory** | Tiered file + vector memory that survives across sessions |
| 2 | **Local Compute** | Open-weights models on consumer GPUs for summarization |
| 3 | **Vault** | Immutable cloud backup (WORM) — nothing can be deleted |
| 4 | **Guardrails** | Safety rules that prevent destructive actions |
| 5 | **Brain Backup** | Vector DB with 22 MCP tools for semantic recall |
| 6 | **Continuity** | Cold-start protocol + revival docs for session handoff |

## Works With

GitHub Copilot · Claude Code · Cursor · Cline · Aider · Continue.dev · LangChain · AutoGen · any MCP-compatible client

## Quick Start

```bash
pip install ai-recallworks
recall serve
```

Then add to your MCP client config:

```json
{
  "mcpServers": {
    "recall": {
      "command": "recall",
      "args": ["serve"]
    }
  }
}
```

## By The Numbers

| Metric | Value |
|--------|-------|
| Cloud storage cost | < $1/mo |
| WORM retention | 7 years |
| Cold-start brief | ~3 KB |
| MCP tools | 22 |
| Independent fail-safes | 3 |

## Links

- **Website:** [recall.works](https://stevepaltridge.github.io/agent-os/)
- **PyPI:** [ai-recallworks](https://pypi.org/project/ai-recallworks/)
- **MCP Registry:** [io.github.RecallWorks/recall](https://github.com/RecallWorks/Recall)
- **Whitepaper:** [Read the full whitepaper →](https://stevepaltridge.github.io/agent-os/whitepaper.html)

## License

MIT — free to read, free to use, free to adapt.

**Recall™** trademark application pending.

---

*Built by [Steve Paltridge](https://github.com/stevepaltridge) · [Mortgagetech](https://mortgagetech.com)*
