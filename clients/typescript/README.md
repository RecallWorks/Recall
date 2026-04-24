<!-- @wbx-modified copilot-a3f7·MTN | 2026-04-24 | TS SDK README | prev: NEW -->
# @recallworks/recall-client (TypeScript)

Official TypeScript / JavaScript SDK for [Recall](https://github.com/RecallWorks/Recall) — open-source memory for AI agents.

Works in Node 18+, Bun, Deno, and modern browsers (CORS-permitting).

## Install

```bash
npm install @recallworks/recall-client
# or
pnpm add @recallworks/recall-client
# or
bun add @recallworks/recall-client
```

## Quick start

```ts
import { RecallClient } from "@recallworks/recall-client";

const client = new RecallClient({
  baseUrl: "http://localhost:8787",
  apiKey: "changeme",
});

console.log(await client.health()); // { status: "ok", chunks: ..., ready: true }

await client.remember("the user prefers dark mode", { tags: "pref,ui" });

const res = await client.recall("user preferences", { n: 5 });
console.log(res.result); // markdown listing of hits
```

Every tool returns a `ToolResponse` envelope with three string fields: `result`, `tool`, `by`. The server formats results as markdown — parse `result` if you need structured fields.

## Tool surface

Typed wrappers for the high-traffic tools:

| Method            | Recall tool      |
| ----------------- | ---------------- |
| `remember()`      | `remember`       |
| `recall()`        | `recall`         |
| `reflect()`       | `reflect`        |
| `checkpoint()`    | `checkpoint`     |
| `pulse()`         | `pulse`          |
| `memoryStats()`   | `memory_stats`   |
| `forget()`        | `forget`         |
| `health()`        | `GET /health`    |

All 13 server tools have typed wrappers (`remember`, `recall`, `reflect`, `antiPattern`, `sessionClose`, `checkpoint`, `pulse`, `memoryStats`, `forget`, `reindex`, `indexFile`, `maintenance`, `snapshotIndex`). For any custom or future tool, use the generic dispatch:

```ts
await client.callTool("index_file", { filepath: "/data/notes.md" });
await client.callTool("forget", { source: "agent-observation" });
```

> Note: `forget()` takes a `source` label and **soft-archives** every chunk with that source. It does not delete a single chunk by id.

## Errors

All exceptions extend `RecallError`:

- `RecallConnectionError` — server unreachable
- `RecallAuthError` — 401/403 (bad/missing API key)
- `RecallServerError` — 5xx (carries `.statusCode`)
- `RecallToolError` — tool returned an explicit `error` payload

## License

MIT. See [LICENSE](https://github.com/RecallWorks/Recall/blob/main/LICENSE) at the root of the Recall repo.
