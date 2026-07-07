const API_BASE = process.env.WEB_PUBLIC_API_BASE || 'http://localhost:8000/api/v1';

export async function apiGet<T>(path: string, token?: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
    cache: 'no-store',
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function apiPost<T>(path: string, body: unknown, token?: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify(body ?? {}),
    cache: 'no-store',
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export const enterpriseEndpoints = {
  buyerInbox: '/buyer-inbox/actions',
  logistics: '/logistics/verifications',
  dealRoom: '/deal-room/summary',
  repayments: '/repayments',
  evidenceBundles: '/evidence/bundles',
  riskRules: '/risk-rules',
  apiExplorer: '/developer/endpoints',
  permissions: '/permissions/matrix',
  networkSummary: '/network/summary',
  businessDirectory: '/network/directory',
  counterpartyInvitations: '/network/invitations',
  tradeContracts: '/network/trade-contracts',
  tradeOpportunities: '/network/opportunities',
  financierMarketplace: '/network/financier-marketplace/deals',
};
