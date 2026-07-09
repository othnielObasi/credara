export const API_BASE = process.env.NEXT_PUBLIC_API_BASE || '/api/v1';
export const REAL_BASE = `${API_BASE}/real`;

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
    this.name = 'ApiError';
  }
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
  if (!res.ok) throw new ApiError((await res.text()) || `HTTP ${res.status}`, res.status);
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

export async function apiRequest<T>(path: string, options: RequestInit = {}, token?: string | null): Promise<T> {
  const authToken = token ?? getAuthToken();
  const res = await fetch(`${API_BASE}${path}`, {
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
