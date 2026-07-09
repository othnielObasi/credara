import { apiRequest } from './client';

export type AuthResponse = { access_token: string; role: string };

export async function registerUser(payload: {
  email: string;
  full_name: string;
  password: string;
  role: string;
}) {
  return apiRequest<AuthResponse>('/auth/register', { method: 'POST', body: JSON.stringify(payload) });
}

export async function loginUser(email: string, password: string) {
  const form = new URLSearchParams();
  form.set('username', email);
  form.set('password', password);
  return apiRequest<AuthResponse>('/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: form.toString(),
  });
}
