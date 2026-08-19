// 127.0.0.1, not "localhost" — on this machine "localhost" can resolve to
// the IPv6 loopback first, which an unrelated container may also occupy on
// port 8000. 127.0.0.1 is unambiguous IPv4 and always reaches this backend.
export const API_ORIGIN = 'http://127.0.0.1:8000';
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
  let data: unknown = null;
  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      // Non-JSON body (e.g. a bare 500 from an unhandled server error) — surface
      // it as a real ApiError instead of letting the parse failure look like a
      // network/connectivity problem to the caller.
      throw new ApiError(response.status, `Server error (${response.status}). Please try again.`);
    }
  }

  if (!response.ok) {
    throw new ApiError(response.status, extractErrorMessage(data));
  }
  return data as T;
}

export const api = {
  get: <T>(path: string, token?: string | null) => request<T>(path, { method: 'GET', token }),
  post: <T>(path: string, body?: unknown, token?: string | null) =>
    request<T>(path, { method: 'POST', body: body ? JSON.stringify(body) : undefined, token }),
  patch: <T>(path: string, body?: unknown, token?: string | null) =>
    request<T>(path, { method: 'PATCH', body: body ? JSON.stringify(body) : undefined, token }),
  del: <T>(path: string, token?: string | null) => request<T>(path, { method: 'DELETE', token }),
};

/** Downloads an authenticated endpoint's response as a file, triggered entirely client-side
 * (a plain <a href> can't carry an Authorization header, so this fetches as a blob instead). */
export async function downloadAuthorized(path: string, token: string, filename: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!response.ok) throw new ApiError(response.status, 'Download failed');
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

/** `path` is a stored image URL, which already includes the /api/v1 prefix. */
export async function fetchAuthorizedBlobUrl(path: string, token: string): Promise<string> {
  const response = await fetch(`${API_ORIGIN}${path}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!response.ok) throw new ApiError(response.status, 'Could not load image');
  const blob = await response.blob();
  return URL.createObjectURL(blob);
}
