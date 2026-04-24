// @wbx-modified copilot-a3f7·MTN | 2026-04-24 | TS Recall client matching real contract | prev: 0.1.0
import {
  RecallAuthError,
  RecallConnectionError,
  RecallServerError,
  RecallToolError,
} from "./errors.js";
import type { ToolResponse } from "./types.js";

export interface RecallClientOptions {
  baseUrl: string;
  apiKey: string;
  /** Per-request timeout in ms. Default 30000. */
  timeoutMs?: number;
  /** Custom fetch (for testing). Defaults to global fetch. */
  fetch?: typeof fetch;
}

/**
 * Isomorphic Recall client. Works in Node 18+, Bun, Deno, and modern
 * browsers (provided CORS is enabled on the Recall server).
 *
 * Every tool returns `{ result: string, tool: string, by: string }`.
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

  async callTool(name: string, args: Record<string, unknown> = {}): Promise<ToolResponse> {
    const url = `${this.baseUrl}/tool/${name}`;
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), this.timeoutMs);

    let response: Response;
    try {
      response = await this.fetchImpl(url, {
        method: "POST",
        headers: {
          "X-API-Key": this.apiKey,
          "Content-Type": "application/json",
          "User-Agent": "recall-client-ts/0.2.0",
        },
        body: JSON.stringify(args),
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

    if (!data || typeof data !== "object") {
      throw new RecallToolError(name, `unexpected response shape: ${text}`);
    }
    const obj = data as Record<string, unknown>;
    if ("error" in obj && obj.error) {
      throw new RecallToolError(name, String(obj.error));
    }
    return {
      result: String(obj.result ?? ""),
      tool: String(obj.tool ?? name),
      by: String(obj.by ?? ""),
    };
  }

  // ── typed wrappers (exact server signatures) ───────────────────────────

  remember(
    content: string,
    options: { source?: string; tags?: string } = {},
  ): Promise<ToolResponse> {
    return this.callTool("remember", {
      content,
      source: options.source ?? "agent-observation",
      tags: options.tags ?? "",
    });
  }

  recall(
    query: string,
    options: { n?: number; type?: string } = {},
  ): Promise<ToolResponse> {
    return this.callTool("recall", {
      query,
      n: options.n ?? 5,
      type: options.type ?? "all",
    });
  }

  reflect(args: {
    domain: string;
    hypothesis: string;
    reasoning: string;
    result: string;
    revisedBelief: string;
    nextTime: string;
    confidence?: number;
    session?: string;
  }): Promise<ToolResponse> {
    return this.callTool("reflect", {
      domain: args.domain,
      hypothesis: args.hypothesis,
      reasoning: args.reasoning,
      result: args.result,
      revised_belief: args.revisedBelief,
      next_time: args.nextTime,
      confidence: args.confidence ?? 0.7,
      session: args.session ?? "",
    });
  }

  antiPattern(args: {
    domain: string;
    temptation: string;
    whyWrong: string;
    signature: string;
    instead: string;
    session?: string;
  }): Promise<ToolResponse> {
    return this.callTool("anti_pattern", {
      domain: args.domain,
      temptation: args.temptation,
      why_wrong: args.whyWrong,
      signature: args.signature,
      instead: args.instead,
      session: args.session ?? "",
    });
  }

  sessionClose(args: {
    sessionId: string;
    reasoningChanged: string;
    doDifferently: string;
    stillUncertain: string;
    temptations: string;
  }): Promise<ToolResponse> {
    return this.callTool("session_close", {
      session_id: args.sessionId,
      reasoning_changed: args.reasoningChanged,
      do_differently: args.doDifferently,
      still_uncertain: args.stillUncertain,
      temptations: args.temptations,
    });
  }

  checkpoint(args: {
    intent: string;
    established: string;
    pursuing: string;
    openQuestions: string;
    session?: string;
    domain?: string;
  }): Promise<ToolResponse> {
    return this.callTool("checkpoint", {
      intent: args.intent,
      established: args.established,
      pursuing: args.pursuing,
      open_questions: args.openQuestions,
      session: args.session ?? "",
      domain: args.domain ?? "",
    });
  }

  pulse(options: { domain?: string; includeReasoning?: boolean } = {}): Promise<ToolResponse> {
    return this.callTool("pulse", {
      domain: options.domain ?? "",
      include_reasoning: options.includeReasoning ?? true,
    });
  }

  memoryStats(): Promise<ToolResponse> {
    return this.callTool("memory_stats");
  }

  /**
   * Soft-archive all chunks matching `source`. NOTE: takes a source label,
   * not a chunk id. Server marks chunks `archived=true`.
   */
  forget(source: string): Promise<ToolResponse> {
    return this.callTool("forget", { source });
  }

  reindex(path = ""): Promise<ToolResponse> {
    return this.callTool("reindex", { path });
  }

  indexFile(filepath: string): Promise<ToolResponse> {
    return this.callTool("index_file", { filepath });
  }

  maintenance(pull = true): Promise<ToolResponse> {
    return this.callTool("maintenance", { pull });
  }

  snapshotIndex(): Promise<ToolResponse> {
    return this.callTool("snapshot_index");
  }

  // ── plain HTTP endpoint (no auth) ──────────────────────────────────────

  async health(): Promise<Record<string, unknown>> {
    const url = `${this.baseUrl}/health`;
    let response: Response;
    try {
      response = await this.fetchImpl(url);
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
}
