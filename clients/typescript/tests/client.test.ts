// @wbx-modified copilot-a3f7·MTN | 2026-04-24 | TS SDK tests | prev: NEW
import { afterEach, beforeEach, describe, expect, it } from "vitest";
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

function makeFetch(
  responder: (call: MockCall) => Response | Promise<Response>,
): { fn: typeof fetch; calls: MockCall[] } {
  const calls: MockCall[] = [];
  const fn = (async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = typeof input === "string" ? input : input.toString();
    calls.push({ url, init });
    return responder({ url, init });
  }) as typeof fetch;
  return { fn, calls };
}

let client: RecallClient;
let fetchMock: ReturnType<typeof makeFetch>;

function build(responder: (call: MockCall) => Response | Promise<Response>) {
  fetchMock = makeFetch(responder);
  client = new RecallClient({ baseUrl: BASE_URL, apiKey: API_KEY, fetch: fetchMock.fn });
}

beforeEach(() => {
  fetchMock = undefined as unknown as ReturnType<typeof makeFetch>;
});

afterEach(() => {
  // no global state to clean
});

describe("RecallClient", () => {
  it("requires baseUrl and apiKey", () => {
    expect(() => new RecallClient({ baseUrl: "", apiKey: "x" })).toThrow();
    expect(() => new RecallClient({ baseUrl: "http://x", apiKey: "" })).toThrow();
  });

  it("strips trailing slashes from baseUrl", () => {
    const c = new RecallClient({ baseUrl: "http://x/////", apiKey: "k" });
    expect(c.baseUrl).toBe("http://x");
  });

  it("remember returns typed RememberResult", async () => {
    build(() =>
      new Response(JSON.stringify({ id: "abc123", artifact_path: "/d/abc.md" }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );
    const result = await client.remember("hello", { tags: ["greeting"] });
    expect(result.id).toBe("abc123");
    expect(result.artifactPath).toBe("/d/abc.md");
  });

  it("recall returns typed Hit array", async () => {
    build(() =>
      new Response(
        JSON.stringify({
          hits: [
            { id: "1", content: "first", score: 0.9, tags: ["a"] },
            { id: "2", content: "second", score: 0.7 },
          ],
        }),
        { status: 200 },
      ),
    );
    const hits = await client.recall("query", { limit: 2 });
    expect(hits).toHaveLength(2);
    expect(hits[0].content).toBe("first");
    expect(hits[0].score).toBe(0.9);
    expect(hits[1].tags).toEqual([]);
  });

  it("recall handles 'results' alias", async () => {
    build(() =>
      new Response(JSON.stringify({ results: [{ content: "x", score: 0.5 }] }), {
        status: 200,
      }),
    );
    const hits = await client.recall("q");
    expect(hits).toHaveLength(1);
    expect(hits[0].content).toBe("x");
  });

  it("auth error raises RecallAuthError", async () => {
    build(() => new Response("bad key", { status: 401 }));
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
    build(() =>
      new Response(JSON.stringify({ error: "invalid tag format" }), { status: 200 }),
    );
    await expect(client.remember("x")).rejects.toBeInstanceOf(RecallToolError);
  });

  it("network failure raises RecallConnectionError", async () => {
    build(() => {
      throw new TypeError("network down");
    });
    await expect(client.remember("x")).rejects.toBeInstanceOf(RecallConnectionError);
  });

  it("callTool dispatches generic tools", async () => {
    build(() => new Response(JSON.stringify({ chunks: 7 }), { status: 200 }));
    const result = await client.callTool<{ chunks: number }>("index_file", {
      path: "/data/notes.md",
    });
    expect(result.chunks).toBe(7);
  });

  it("sends Authorization header", async () => {
    build(() => new Response(JSON.stringify({ sessions: 0 }), { status: 200 }));
    await client.pulse();
    const headers = fetchMock.calls[0].init?.headers as Record<string, string>;
    expect(headers.Authorization).toBe(`Bearer ${API_KEY}`);
  });

  it("health hits GET /health", async () => {
    build(({ url }) => {
      expect(url).toBe(`${BASE_URL}/health`);
      return new Response(JSON.stringify({ status: "ok" }), { status: 200 });
    });
    const h = await client.health();
    expect(h.status).toBe("ok");
  });

  it("checkpoint converts openQuestions camelCase", async () => {
    build(({ init }) => {
      const body = JSON.parse(String(init?.body));
      expect(body.open_questions).toEqual(["q1", "q2"]);
      return new Response(JSON.stringify({ ok: true }), { status: 200 });
    });
    await client.checkpoint({
      session: "s1",
      established: "e",
      intent: "i",
      pursuing: "p",
      summary: "sum",
      openQuestions: ["q1", "q2"],
    });
  });
});
