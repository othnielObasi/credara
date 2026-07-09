import { realRequest } from './client';

export type WorkspaceMeResponse = {
  user: { id: string; email: string; full_name: string; role: string };
  workspaces: Array<{
    workspace: { id: string; business_id: string; name: string; primary_role: string; environment: string; region?: string };
    business: { id: string; legal_name: string; country: string; status: string } | null;
    membership: { id: string; role: string; status: string };
    progress: { percent: number; kyb_status: string; wallet_status: string; first_workflow: string | null } | null;
  }>;
};

export const realApi = {
  workspacesMe: () => realRequest<WorkspaceMeResponse>('/workspaces/me'),

  startOnboarding: (body: Record<string, unknown>) =>
    realRequest<{ workspace: { id: string; business_id: string }; user: { id: string } }>('/onboarding/start', {
      method: 'POST',
      body: JSON.stringify(body),
    }),

  navigationForRole: (role: string) =>
    realRequest<{ role: string; allowed_pages: string[] }>(`/access/navigation/${role}`),

  getSettings: (workspaceId: string) =>
    realRequest<Record<string, unknown>>(`/settings?workspace_id=${encodeURIComponent(workspaceId)}`),

  saveSettings: (body: Record<string, unknown>) =>
    realRequest<{ id: string; saved: boolean }>('/settings', { method: 'PUT', body: JSON.stringify(body) }),

  listInvitations: () => realRequest<Array<Record<string, unknown>>>('/invitations'),

  listApiKeys: (workspaceId: string) =>
    realRequest<Array<Record<string, unknown>>>(`/api-keys?workspace_id=${encodeURIComponent(workspaceId)}`),

  createApiKey: (body: Record<string, unknown>) =>
    realRequest<Record<string, unknown>>('/api-keys', { method: 'POST', body: JSON.stringify(body) }),

  listWallets: (workspaceId: string) =>
    realRequest<Array<Record<string, unknown>>>(`/wallets?workspace_id=${encodeURIComponent(workspaceId)}`),

  createWallet: (body: Record<string, unknown>) =>
    realRequest<Record<string, unknown>>('/wallets', { method: 'POST', body: JSON.stringify(body) }),

  listPaymentIntents: (workspaceId: string) =>
    realRequest<Array<Record<string, unknown>>>(`/payment-intents?workspace_id=${encodeURIComponent(workspaceId)}`),

  createPaymentIntent: (body: Record<string, unknown>) =>
    realRequest<Record<string, unknown>>('/payment-intents', { method: 'POST', body: JSON.stringify(body) }),

  submitPaymentIntent: (intentId: string, body: Record<string, unknown>) =>
    realRequest<Record<string, unknown>>(`/payment-intents/${intentId}/submit`, {
      method: 'POST',
      body: JSON.stringify(body),
    }),

  confirmPaymentIntent: (intentId: string, body: Record<string, unknown>) =>
    realRequest<Record<string, unknown>>(`/payment-intents/${intentId}/confirm`, {
      method: 'POST',
      body: JSON.stringify(body),
    }),

  listEscrows: (workspaceId: string) =>
    realRequest<Array<Record<string, unknown>>>(`/escrows?workspace_id=${encodeURIComponent(workspaceId)}`),

  createEscrow: (body: Record<string, unknown>) =>
    realRequest<Record<string, unknown>>('/escrows', { method: 'POST', body: JSON.stringify(body) }),

  fundEscrow: (escrowId: string, body: Record<string, unknown>) =>
    realRequest<Record<string, unknown>>(`/escrows/${escrowId}/fund`, { method: 'POST', body: JSON.stringify(body) }),

  releaseEscrow: (escrowId: string, body: Record<string, unknown>) =>
    realRequest<Record<string, unknown>>(`/escrows/${escrowId}/release`, { method: 'POST', body: JSON.stringify(body) }),

  listLedger: (workspaceId: string) =>
    realRequest<Array<Record<string, unknown>>>(`/ledger?workspace_id=${encodeURIComponent(workspaceId)}`),

  reconcile: (type: string, referenceId: string, expectedAmount: number) =>
    realRequest<Record<string, unknown>>(
      `/reconciliation/${type}/${referenceId}?expected_amount=${encodeURIComponent(expectedAmount)}`,
      { method: 'POST' },
    ),
};
