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

await client.remember("the user prefers dark mode", {
  tags: ["pref", "ui"],
});

const hits = await client.recall("user preferences", { limit: 5 });
for (const h of hits) {
  console.log(`${h.score.toFixed(3)}  ${h.content}`);
}
```

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

For tools without a typed wrapper, use the generic dispatch:

```ts
await client.callTool("index_file", { path: "/data/notes.md" });
await client.callTool("anti_pattern", { pattern: "don't auto-merge without CI" });
```

## Errors

All exceptions extend `RecallError`:

- `RecallConnectionError` — server unreachable
- `RecallAuthError` — 401/403 (bad/missing API key)
- `RecallServerError` — 5xx (carries `.statusCode`)
- `RecallToolError` — tool returned an explicit `error` payload

## License

MIT. See [LICENSE](https://github.com/RecallWorks/Recall/blob/main/LICENSE) at the root of the Recall repo.
