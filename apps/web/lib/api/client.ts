export const API_BASE = process.env.NEXT_PUBLIC_API_BASE || '/api/v1';
export const REAL_BASE = `${API_BASE}/real`;

/** Absolute API origin for browser redirects (Auth0). Relative `/api/v1` proxies set cookies on the web host, but Auth0 callbacks hit the API host. */
export const API_ORIGIN = (
  process.env.NEXT_PUBLIC_API_ORIGIN ||
  (API_BASE.startsWith('http://') || API_BASE.startsWith('https://')
    ? new URL(API_BASE).origin
    : 'https://credara-api.vercel.app')
).replace(/\/$/, '');

export const OAUTH_LOGIN_URL = `${API_ORIGIN}/api/v1/auth/oauth/login`;

export class ApiError extends Error {
  readonly detail: string;

  constructor(
    message: string,
    readonly status: number,
    detail?: string,
  ) {
    super(detail || message);
    this.name = 'ApiError';
    this.detail = detail || message;
  }
}

function parseErrorBody(text: string, status: number): ApiError {
  const trimmed = text.trim();
  if (trimmed.startsWith('{')) {
    try {
      const body = JSON.parse(trimmed) as { detail?: string | Array<{ msg?: string }> };
      if (typeof body.detail === 'string') {
        return new ApiError(trimmed, status, body.detail);
      }
      if (Array.isArray(body.detail)) {
        const msg = body.detail.map((d) => d.msg).filter(Boolean).join('; ') || trimmed;
        return new ApiError(trimmed, status, msg);
      }
    } catch {
      /* fall through */
    }
  }
  return new ApiError(trimmed || `HTTP ${status}`, status);
}

export function getAuthToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('credara.authToken');
}

export function setAuthSession(token: string, role: string) {
  localStorage.setItem('credara.authToken', token);
  localStorage.setItem('credara.role', role);
}

export function clearAuthSession() {
  localStorage.removeItem('credara.authToken');
  localStorage.removeItem('credara.role');
}

async function parseResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const text = await res.text();
    throw parseErrorBody(text, res.status);
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

export async function apiRequest<T>(path: string, options: RequestInit = {}, token?: string | null): Promise<T> {
  const authToken = token ?? getAuthToken();
  const headers: Record<string, string> = {
    ...(authToken ? { Authorization: `Bearer ${authToken}` } : {}),
    ...(options.headers as Record<string, string> | undefined),
  };
  // Default JSON only when the caller did not set Content-Type (form login must stay urlencoded).
  if (options.body && !Object.keys(headers).some((key) => key.toLowerCase() === 'content-type')) {
    headers['Content-Type'] = 'application/json';
  }
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
    cache: 'no-store',
  });
  return parseResponse<T>(res);
}

export async function realRequest<T>(path: string, options: RequestInit = {}, token?: string | null): Promise<T> {
  const authToken = token ?? getAuthToken();
  const res = await fetch(`${REAL_BASE}${path}`, {
    ...options,
    headers: {
      ...(options.body ? { 'Content-Type': 'application/json' } : {}),
      ...(authToken ? { Authorization: `Bearer ${authToken}` } : {}),
      ...(options.headers || {}),
    },
    cache: 'no-store',
  });
  return parseResponse<T>(res);
}
