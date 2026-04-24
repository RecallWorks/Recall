// @wbx-modified copilot-a3f7·MTN | 2026-04-24 | typed errors | prev: NEW
export class RecallError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "RecallError";
  }
}

export class RecallConnectionError extends RecallError {
  constructor(message: string) {
    super(message);
    this.name = "RecallConnectionError";
  }
}

export class RecallAuthError extends RecallError {
  constructor(message: string) {
    super(message);
    this.name = "RecallAuthError";
  }
}

export class RecallServerError extends RecallError {
  readonly statusCode: number;
  constructor(message: string, statusCode: number) {
    super(message);
    this.name = "RecallServerError";
    this.statusCode = statusCode;
  }
}

export class RecallToolError extends RecallError {
  readonly tool: string;
  constructor(tool: string, message: string) {
    super(`${tool}: ${message}`);
    this.name = "RecallToolError";
    this.tool = tool;
  }
}
