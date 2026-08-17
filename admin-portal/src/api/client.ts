export const API_ORIGIN = 'http://localhost:8000';
export const API_BASE_URL = `${API_ORIGIN}/api/v1`;

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

function extractErrorMessage(payload: unknown): string {
  if (payload && typeof payload === 'object' && 'detail' in payload) {
    const detail = (payload as { detail: unknown }).detail;
    if (typeof detail === 'string') return detail;
    if (Array.isArray(detail) && detail.length > 0) {
      const first = detail[0];
      if (first && typeof first === 'object' && 'msg' in first) {
        return String((first as { msg: unknown }).msg);
      }
      return String(first);
    }
  }
  return 'Something went wrong. Please try again.';
}

async function request<T>(
  path: string,
  options: RequestInit & { token?: string | null } = {},
): Promise<T> {
  const { token, headers, ...rest } = options;
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...rest,
    headers: {
      ...(rest.body ? { 'Content-Type': 'application/json' } : {}),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...headers,
    },
  });

  const text = await response.text();
  const data = text ? JSON.parse(text) : null;

  if (!response.ok) {
    throw new ApiError(response.status, extractErrorMessage(data));
  }
  return data as T;
}

export const api = {
  get: <T>(path: string, token?: string | null) => request<T>(path, { method: 'GET', token }),
  post: <T>(path: string, body?: unknown, token?: string | null) =>
    request<T>(path, { method: 'POST', body: body ? JSON.stringify(body) : undefined, token }),
};

/** `path` is a stored image URL, which already includes the /api/v1 prefix. */
export async function fetchAuthorizedBlobUrl(path: string, token: string): Promise<string> {
  const response = await fetch(`${API_ORIGIN}${path}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!response.ok) throw new ApiError(response.status, 'Could not load image');
  const blob = await response.blob();
  return URL.createObjectURL(blob);
}
