// @wbx-modified copilot-a3f7·MTN | 2026-04-24 | response envelope type | prev: typed Hits
export interface ToolResponse {
  /** Tool's return value, always a string from the server. */
  result: string;
  /** Echo of the tool name. */
  tool: string;
  /** Authenticated user identifier from the server's API-key map. */
  by: string;
}
