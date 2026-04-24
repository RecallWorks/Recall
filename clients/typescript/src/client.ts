// @wbx-modified copilot-a3f7·MTN | 2026-04-24 | TS Recall client | prev: NEW
import {
  RecallAuthError,
  RecallConnectionError,
  RecallServerError,
  RecallToolError,
} from "./errors.js";
import type { CheckpointInput, Hit, RememberResult, ToolResult } from "./types.js";

export interface RecallClientOptions {
  baseUrl: string;
  apiKey: string;
  /** Per-request timeout in ms. Default 30000. */
  timeoutMs?: number;
  /** Custom fetch (for testing or runtime polyfills). Defaults to global fetch. */
  fetch?: typeof fetch;
}

interface RawHit {
  id?: string;
  content?: string;
  score?: number;
  tags?: string[];
  metadata?: Record<string, unknown>;
}

/**
 * Isomorphic Recall client. Works in Node 18+, Bun, Deno, and modern browsers
 * (provided CORS is enabled on the Recall server).
 */
export class RecallClient {
  readonly baseUrl: string;
  readonly apiKey: string;
  private readonly timeoutMs: number;
  private readonly fetchImpl: typeof fetch;

  constructor(options: RecallClientOptions) {
    if (!options.baseUrl) throw new Error("RecallClient: baseUrl is required");
    if (!options.apiKey) throw new Error("RecallClient: apiKey is required");
    this.baseUrl = options.baseUrl.replace(/\/+$/, "");
    this.apiKey = options.apiKey;
    this.timeoutMs = options.timeoutMs ?? 30000;
    this.fetchImpl = options.fetch ?? globalThis.fetch;
    if (!this.fetchImpl) {
      throw new Error("RecallClient: no fetch implementation available");
    }
  }

  // ── core dispatch ──────────────────────────────────────────────────────

  async callTool<T = Record<string, unknown>>(
    name: string,
    payload: Record<string, unknown> = {},
  ): Promise<T> {
    const url = `${this.baseUrl}/tool/${name}`;
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), this.timeoutMs);

    let response: Response;
    try {
      response = await this.fetchImpl(url, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${this.apiKey}`,
          "Content-Type": "application/json",
          "User-Agent": "recall-client-ts/0.1.0",
        },
        body: JSON.stringify(payload),
        signal: controller.signal,
      });
    } catch (err) {
      throw new RecallConnectionError(
        `Cannot reach ${url}: ${err instanceof Error ? err.message : String(err)}`,
      );
    } finally {
      clearTimeout(timeout);
    }

    const text = await response.text();

    if (response.status === 401 || response.status === 403) {
      throw new RecallAuthError(`Auth failed (${response.status}): ${text}`);
    }
    if (response.status >= 500) {
      throw new RecallServerError(
        `Server error ${response.status}: ${text}`,
        response.status,
      );
    }
    if (response.status >= 400) {
      throw new RecallToolError(name, `HTTP ${response.status}: ${text}`);
    }

    let data: unknown;
    try {
      data = text ? JSON.parse(text) : {};
    } catch {
      throw new RecallToolError(name, `Invalid JSON response: ${text}`);
    }

    if (data && typeof data === "object" && "error" in data && (data as { error: unknown }).error) {
      throw new RecallToolError(name, String((data as { error: unknown }).error));
    }
    return data as T;
  }

  // ── typed wrappers ─────────────────────────────────────────────────────

  async remember(
    content: string,
    options: { tags?: string[]; metadata?: Record<string, unknown> } = {},
  ): Promise<RememberResult> {
    const payload: Record<string, unknown> = { content };
    if (options.tags?.length) payload.tags = options.tags;
    if (options.metadata) payload.metadata = options.metadata;
    const raw = await this.callTool<{ id?: string; artifact_path?: string }>(
      "remember",
      payload,
    );
    return { id: raw.id ?? "", artifactPath: raw.artifact_path };
  }

  async recall(
    query: string,
    options: { limit?: number; tags?: string[] } = {},
  ): Promise<Hit[]> {
    const payload: Record<string, unknown> = { query, limit: options.limit ?? 5 };
    if (options.tags?.length) payload.tags = options.tags;
    const raw = await this.callTool<{ hits?: RawHit[]; results?: RawHit[] }>(
      "recall",
      payload,
    );
    const items = raw.hits ?? raw.results ?? [];
    return items.map((h) => ({
      id: h.id,
      content: h.content ?? "",
      score: h.score ?? 0,
      tags: h.tags ?? [],
      metadata: h.metadata ?? {},
    }));
  }

  async reflect(summary: string, tags?: string[]): Promise<ToolResult> {
    const payload: Record<string, unknown> = { summary };
    if (tags?.length) payload.tags = tags;
    return this.toToolResult(await this.callTool("reflect", payload));
  }

  async checkpoint(input: CheckpointInput): Promise<ToolResult> {
    return this.toToolResult(
      await this.callTool("checkpoint", {
        session: input.session,
        established: input.established,
        intent: input.intent,
        pursuing: input.pursuing,
        summary: input.summary,
        open_questions: input.openQuestions ?? [],
      }),
    );
  }

  async pulse(): Promise<Record<string, unknown>> {
    return this.callTool("pulse");
  }

  async memoryStats(): Promise<Record<string, unknown>> {
    return this.callTool("memory_stats");
  }

  async forget(id: string, source = "user-request"): Promise<ToolResult> {
    return this.toToolResult(await this.callTool("forget", { id, source }));
  }

  async health(): Promise<Record<string, unknown>> {
    const url = `${this.baseUrl}/health`;
    let response: Response;
    try {
      response = await this.fetchImpl(url, {
        headers: { Authorization: `Bearer ${this.apiKey}` },
      });
    } catch (err) {
      throw new RecallConnectionError(
        `Cannot reach health: ${err instanceof Error ? err.message : String(err)}`,
      );
    }
    if (!response.ok) {
      throw new RecallServerError(
        `Health failed: ${response.status}`,
        response.status,
      );
    }
    return (await response.json()) as Record<string, unknown>;
  }

  private toToolResult(raw: Record<string, unknown>): ToolResult {
    const ok = "ok" in raw ? Boolean(raw.ok) : true;
    const error = typeof raw.error === "string" ? raw.error : undefined;
    const data: Record<string, unknown> = {};
    for (const [k, v] of Object.entries(raw)) {
      if (k !== "ok" && k !== "error") data[k] = v;
    }
    return { ok, data, error };
  }
}
