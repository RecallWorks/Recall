// @wbx-modified copilot-a3f7·MTN | 2026-04-24 | TS SDK tests for real contract | prev: typed-Hit fiction
import { beforeEach, describe, expect, it } from "vitest";
import {
  RecallAuthError,
  RecallClient,
  RecallConnectionError,
  RecallServerError,
  RecallToolError,
} from "../src/index.js";

const BASE_URL = "http://localhost:8787";
const API_KEY = "test-key";

interface MockCall {
  url: string;
  init?: RequestInit;
}

function makeFetch(responder: (call: MockCall) => Response | Promise<Response>) {
  const calls: MockCall[] = [];
  const fn = (async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = typeof input === "string" ? input : input.toString();
    calls.push({ url, init });
    return responder({ url, init });
  }) as typeof fetch;
  return { fn, calls };
}

const envelope = (result: string, tool: string, by = "test-user") =>
  new Response(JSON.stringify({ result, tool, by }), {
    status: 200,
    headers: { "Content-Type": "application/json" },
  });

let client: RecallClient;
let fetchMock: ReturnType<typeof makeFetch>;

function build(responder: (call: MockCall) => Response | Promise<Response>) {
  fetchMock = makeFetch(responder);
  client = new RecallClient({ baseUrl: BASE_URL, apiKey: API_KEY, fetch: fetchMock.fn });
}

beforeEach(() => {
  fetchMock = undefined as unknown as ReturnType<typeof makeFetch>;
});

describe("RecallClient (0.2.0)", () => {
  it("requires baseUrl and apiKey", () => {
    expect(() => new RecallClient({ baseUrl: "", apiKey: "x" })).toThrow();
    expect(() => new RecallClient({ baseUrl: "http://x", apiKey: "" })).toThrow();
  });

  it("strips trailing slashes from baseUrl", () => {
    const c = new RecallClient({ baseUrl: "http://x/////", apiKey: "k" });
    expect(c.baseUrl).toBe("http://x");
  });

  it("remember returns ToolResponse envelope", async () => {
    build(() => envelope("Stored 1 chunk", "remember"));
    const r = await client.remember("hello", { tags: "greeting,ui" });
    expect(r.tool).toBe("remember");
    expect(r.result).toContain("Stored");
  });

  it("remember sends string tags + default source", async () => {
    build(() => envelope("ok", "remember"));
    await client.remember("x", { tags: "a,b" });
    const body = JSON.parse(String(fetchMock.calls[0].init?.body));
    expect(body.tags).toBe("a,b");
    expect(body.source).toBe("agent-observation");
  });

  it("recall uses n + type params", async () => {
    build(() => envelope("# Hits", "recall"));
    await client.recall("query", { n: 3 });
    const body = JSON.parse(String(fetchMock.calls[0].init?.body));
    expect(body.n).toBe(3);
    expect(body.type).toBe("all");
  });

  it("forget takes source not id", async () => {
    build(() => envelope("Archived 5", "forget"));
    await client.forget("agent-observation");
    const body = JSON.parse(String(fetchMock.calls[0].init?.body));
    expect(body.source).toBe("agent-observation");
  });

  it("checkpoint maps camelCase to snake_case", async () => {
    build(() => envelope("Checkpoint stored", "checkpoint"));
    await client.checkpoint({
      intent: "ship SDK",
      established: "contract verified",
      pursuing: "live smoke",
      openQuestions: "none",
      session: "a3f7",
    });
    const body = JSON.parse(String(fetchMock.calls[0].init?.body));
    expect(body.intent).toBe("ship SDK");
    expect(body.open_questions).toBe("none");
    expect(body.session).toBe("a3f7");
  });

  it("reflect maps camelCase to snake_case", async () => {
    build(() => envelope("ok", "reflect"));
    await client.reflect({
      domain: "d",
      hypothesis: "h",
      reasoning: "r",
      result: "FAILED: x",
      revisedBelief: "rb",
      nextTime: "nt",
    });
    const body = JSON.parse(String(fetchMock.calls[0].init?.body));
    expect(body.revised_belief).toBe("rb");
    expect(body.next_time).toBe("nt");
    expect(body.confidence).toBe(0.7);
  });

  it("auth error raises RecallAuthError", async () => {
    build(() => new Response(JSON.stringify({ error: "unauthorized" }), { status: 401 }));
    await expect(client.remember("x")).rejects.toBeInstanceOf(RecallAuthError);
  });

  it("server error raises RecallServerError with status", async () => {
    build(() => new Response("boom", { status: 500 }));
    try {
      await client.remember("x");
      throw new Error("should have thrown");
    } catch (e) {
      expect(e).toBeInstanceOf(RecallServerError);
      expect((e as RecallServerError).statusCode).toBe(500);
    }
  });

  it("explicit error payload raises RecallToolError", async () => {
    build(() => new Response(JSON.stringify({ error: "bad arguments" }), { status: 400 }));
    await expect(client.remember("x")).rejects.toBeInstanceOf(RecallToolError);
  });

  it("network failure raises RecallConnectionError", async () => {
    build(() => {
      throw new TypeError("network down");
    });
    await expect(client.remember("x")).rejects.toBeInstanceOf(RecallConnectionError);
  });

  it("callTool dispatches generic tools", async () => {
    build(() => envelope("Maintenance complete", "maintenance"));
    const r = await client.callTool("maintenance", { pull: true });
    expect(r.tool).toBe("maintenance");
  });

  it("sends X-API-Key header", async () => {
    build(() => envelope("# Pulse", "pulse"));
    await client.pulse();
    const headers = fetchMock.calls[0].init?.headers as Record<string, string>;
    expect(headers["X-API-Key"]).toBe(API_KEY);
  });

  it("health hits GET /health without auth header", async () => {
    build(({ url, init }) => {
      expect(url).toBe(`${BASE_URL}/health`);
      expect((init?.headers as Record<string, string> | undefined)?.["X-API-Key"]).toBeUndefined();
      return new Response(JSON.stringify({ status: "ok" }), { status: 200 });
    });
    const h = await client.health();
    expect(h.status).toBe("ok");
  });

  it("404 unknown tool surfaces as RecallToolError", async () => {
    build(() => new Response(JSON.stringify({ error: "unknown tool: bogus" }), { status: 404 }));
    await expect(client.callTool("bogus")).rejects.toBeInstanceOf(RecallToolError);
  });
});
