# @wbx-modified copilot-b1c4 | 2026-04-27 22:25 MTN | v1.0 | MCP integration guide for Claude Desktop / Cursor / Cline | prev: NEW
# Recall as an MCP server

Recall ships with first-class support for the [Model Context Protocol](https://modelcontextprotocol.io/),
so you can wire it into Claude Desktop, Cursor, Cline, Continue.dev, or any
other MCP client as a memory tool. Your AI assistant gets persistent memory
across sessions — locally, on your machine, no SaaS in the loop.

## Two transports, same 16 tools

Recall exposes the same tool surface over two MCP transports:

| Transport | Use when                                                | Entry point |
|-----------|---------------------------------------------------------|-------------|
| **stdio** | Running locally, used by Claude Desktop / Cursor / Cline | `recall-mcp` (or `python -m recall.mcp_stdio`) |
| **SSE**   | Running as a network service, multiple agents share it   | `recall-server` exposes `/sse` automatically when `mcp` extras installed |

Both serve all 16 tools: `recall`, `recall_filtered`, `answer`, `remember`,
`reindex`, `index_file`, `memory_stats`, `forget`, `reflect`, `anti_pattern`,
`session_close`, `checkpoint`, `pulse`, `maintenance`, `snapshot_index`,
`backfill_epoch`.

## Install

```bash
pip install "recall[mcp]"
```

That installs the server, all 16 tools, and the MCP runtime (`mcp>=1.27.0`).

## Claude Desktop

Edit `~/Library/Application Support/Claude/claude_desktop_config.json`
(macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "recall": {
      "command": "recall-mcp",
      "env": {
        "RECALL_STORE_DIR": "/Users/you/.recall/store",
        "RECALL_LOG_LEVEL": "WARNING"
      }
    }
  }
}
```

Restart Claude Desktop. You'll see a new wrench icon — click it and you'll
see all 16 Recall tools available to the conversation.

## Cursor

Cursor reads MCP servers from `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "recall": {
      "command": "recall-mcp",
      "env": {
        "RECALL_STORE_DIR": "/Users/you/.recall/store"
      }
    }
  }
}
```

After Cursor restart, the tools show up in Composer.

## Cline (VS Code extension)

In VS Code: open Cline settings → "MCP Servers" → click "+":

```json
{
  "recall": {
    "command": "recall-mcp",
    "args": [],
    "env": {
      "RECALL_STORE_DIR": "/Users/you/.recall/store"
    }
  }
}
```

## Continue.dev

In `~/.continue/config.json`:

```json
{
  "mcpServers": [
    {
      "name": "recall",
      "command": "recall-mcp",
      "env": {
        "RECALL_STORE_DIR": "/Users/you/.recall/store"
      }
    }
  ]
}
```

## Verify it's working

After your client restarts, ask: **"What Recall tools do you have access to?"**

A working setup will list all 16 tools. Then ask:

> *"Remember that I prefer concise answers."*

The model should call `remember`. In the next session, ask:

> *"How do I like my answers?"*

The model should call `recall` and answer "concise."

## Bring your own embedding model

By default Recall uses a small offline embedding model bundled with chroma —
this runs on a laptop with no API keys.

To use a stronger model, add to your client's `env`:

```json
"env": {
  "RECALL_EMBEDDER": "openai",
  "OPENAI_API_KEY": "sk-...",
  "RECALL_STORE_DIR": "/Users/you/.recall/store"
}
```

## Privacy posture

- **Stdio mode is fully local.** The MCP client launches `recall-mcp` as a
  subprocess on your machine. No network calls unless you opted into a
  cloud embedder.
- **No telemetry. Ever.** Recall doesn't phone home about tool calls,
  tool counts, or anything else. Read [`auth.py`](../src/recall/auth.py)
  and [`app.py`](../src/recall/app.py) — the only network code is the
  optional git_sync if you set `RECALL_GIT_REPO_URL`.
- **Store path is yours.** Set `RECALL_STORE_DIR` to anywhere you control.
  Default is `~/.recall/store/`.

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| Client shows 0 tools | `pip install "recall[mcp]"` not run | Install with the `mcp` extra |
| `recall-mcp: command not found` | Not in client's PATH | Use absolute path: `"command": "/Users/you/.venv/bin/recall-mcp"` |
| Tools list but calls fail | Store init failed at startup | Check stderr — likely a permissions issue on `RECALL_STORE_DIR` |
| Stdout corruption / parse errors | Something logged to stdout | Recall logs to stderr only — if you wrote a custom plugin, fix it |

## Source

- [`src/recall/mcp_stdio.py`](../src/recall/mcp_stdio.py) — stdio entry
- [`src/recall/transport/mcp_sse.py`](../src/recall/transport/mcp_sse.py) — FastMCP wiring
- [`src/recall/tools/__init__.py`](../src/recall/tools/__init__.py) — tool registry
