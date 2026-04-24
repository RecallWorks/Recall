// @wbx-modified copilot-a3f7·MTN | 2026-04-24 | TS live smoke against running Recall container
// Run order:
//   docker run -d --name recall-smoke -p 8799:8787 -e API_KEY=smoke-key ghcr.io/recallworks/recall:0.1.0
//   npx tsx smoke_live.ts   (or compile + node)

import { RecallAuthError, RecallClient } from "./src/index.js";

const BASE = "http://localhost:8799";
const KEY = "smoke-key";

async function main() {
  const c = new RecallClient({ baseUrl: BASE, apiKey: KEY });

  console.log("=== TS smoke ===");
  const h = await c.health();
  console.log("health:", h);

  const r = await c.remember("ts-sdk live smoke ran", { tags: "smoke,ts" });
  console.log("remember:", r.result.slice(0, 80));

  const rec = await c.recall("ts-sdk smoke", { n: 3 });
  console.log("recall (", rec.result.length, "chars):");
  console.log(rec.result.slice(0, 300));

  const cp = await c.checkpoint({
    intent: "validate TS SDK 0.2.0 against live server",
    established: "envelope shape match, X-API-Key works",
    pursuing: "ship 0.2.0 PR",
    openQuestions: "npm token still pending",
    session: "a3f7",
  });
  console.log("checkpoint:", cp.result.slice(0, 120));

  console.log("--- auth-error path ---");
  const bad = new RecallClient({ baseUrl: BASE, apiKey: "WRONG" });
  try {
    await bad.remember("should fail");
    throw new Error("expected auth error");
  } catch (e) {
    if (e instanceof RecallAuthError) {
      console.log("  got expected RecallAuthError:", String(e).slice(0, 60));
    } else {
      throw e;
    }
  }

  console.log("\nALL TS SMOKE PASSED");
}

main().catch((e) => {
  console.error("SMOKE FAILED:", e);
  process.exit(1);
});
