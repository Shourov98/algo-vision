export class EngineInvariantError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "EngineInvariantError";
  }
}
