// @wbx-modified copilot-a3f7·MTN | 2026-04-24 | shared types | prev: NEW
export interface Hit {
  id?: string;
  content: string;
  score: number;
  tags: string[];
  metadata: Record<string, unknown>;
}

export interface RememberResult {
  id: string;
  artifactPath?: string;
}

export interface ToolResult {
  ok: boolean;
  data: Record<string, unknown>;
  error?: string;
}

export interface CheckpointInput {
  session: string;
  established: string;
  intent: string;
  pursuing: string;
  summary: string;
  openQuestions?: string[];
}
