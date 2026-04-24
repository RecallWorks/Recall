// @wbx-modified copilot-a3f7·MTN | 2026-04-24 | minimal Recall agent-memory example (TS)
//
// Run a server first:
//   docker run -d -p 8787:8787 -e API_KEY=changeme \
//     -v recall-data:/data ghcr.io/recallworks/recall:latest
//
// Then:
//   npm install @recallworks/recall-client
//   npx tsx agent_memory.ts

import { RecallClient } from "@recallworks/recall-client";

const URL = process.env.RECALL_URL ?? "http://localhost:8787";
const KEY = process.env.RECALL_KEY ?? "changeme";

async function main() {
  const c = new RecallClient({ baseUrl: URL, apiKey: KEY });

  // 0. Health
  console.log("server:", await c.health());

  // 1. Store a few facts the agent should remember across sessions.
  await c.remember("user prefers dark mode", { source: "prefs", tags: "ui,dark-mode" });
  await c.remember("project deadline is 2026-05-15", { source: "project", tags: "deadline" });
  await c.remember("lead engineer is Jamie (jamie@example.com)", { source: "people", tags: "contact" });

  // 2. Pull them back semantically.
  const hits = await c.recall("when is the deadline", { n: 3 });
  console.log("\nrecall: when is the deadline");
  console.log(hits.result);

  // 3. End-of-session checkpoint so the next agent can pick up.
  const cp = await c.checkpoint({
    intent: "onboard new agent to the project",
    established: "user prefers dark mode; deadline 2026-05-15; lead is Jamie",
    pursuing: "prepare kickoff doc draft",
    openQuestions: "which team channel does Jamie use?",
    session: "e0a1",
  });
  console.log("\ncheckpoint:", cp.result.split("\n")[0]);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
