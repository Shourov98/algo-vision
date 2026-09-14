const baseUrl = (process.env.NEXT_PUBLIC_API_BASE_URL ?? "/api/v1").replace(/\/$/, "");

interface ErrorPayload {
  error?: {
    code?: string;
    message?: string;
    details?: unknown;
  };
}

export class ApiError extends Error {
  constructor(
    public readonly code: string,
    message: string,
    public readonly status: number,
    public readonly details?: unknown,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

function isErrorPayload(value: unknown): value is ErrorPayload {
  return typeof value === "object" && value !== null;
}

async function readJson(response: Response): Promise<unknown> {
  return response.json().catch(() => null);
}

function toApiError(response: Response, payload: unknown): ApiError {
  const error = isErrorPayload(payload) ? payload.error : undefined;
  return new ApiError(
    error?.code ?? "UNKNOWN",
    (error?.message ?? response.statusText) || "Request failed",
    response.status,
    error?.details,
  );
}

export async function apiFetch<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  if (!headers.has("Accept")) headers.set("Accept", "application/json");

  let response: Response;
  try {
    response = await fetch(`${baseUrl}/${path.replace(/^\//, "")}`, {
      credentials: "include",
      ...init,
      headers,
    });
  } catch {
    throw new ApiError("NETWORK_ERROR", "Unable to reach the service.", 0);
  }

  const payload = await readJson(response);
  if (!response.ok) throw toApiError(response, payload);
  return payload as T;
}
