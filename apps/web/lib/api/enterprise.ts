import { apiRequest } from './client';

export type BuyerAction = {
  id: string;
  action_type: string;
  title: string;
  description: string;
  status: string;
  invoice_id?: string | null;
  order_id?: string | null;
};

export type MarketplaceDeal = {
  receivable_id: string;
  seller_business_id: string;
  debtor_name: string;
  face_value: number;
  currency: string;
  status: string;
  recommended_advance: number;
  proof_hash: string;
  polygon_tx_hash: string | null;
  risk_inputs: Record<string, unknown>;
};

export type DealRoomSummary = {
  receivable_count: number;
  total_face_value: number;
  recommended_advance: number;
  risk_band: string;
  open_disputes: number;
  proof_receipts: number;
};

export const enterpriseApi = {
  listBuyerActions: (status?: string) => {
    const q = status ? `?status=${encodeURIComponent(status)}` : '';
    return apiRequest<BuyerAction[]>(`/buyer-inbox/actions${q}`);
  },

  decideBuyerAction: (actionId: string, decision: string, reason?: string) =>
    apiRequest<BuyerAction>(`/buyer-inbox/actions/${actionId}/decision`, {
      method: 'POST',
      body: JSON.stringify({ decision, reason }),
    }),

  listMarketplaceDeals: (opts?: { minAmount?: number; maxAmount?: number; currency?: string }) => {
    const params = new URLSearchParams();
    if (opts?.minAmount != null) params.set('min_amount', String(opts.minAmount));
    if (opts?.maxAmount != null) params.set('max_amount', String(opts.maxAmount));
    if (opts?.currency) params.set('currency', opts.currency);
    const q = params.toString();
    return apiRequest<MarketplaceDeal[]>(`/network/financier-marketplace/deals${q ? `?${q}` : ''}`);
  },

  expressInterest: (receivableId: string) =>
    apiRequest<Record<string, unknown>>(`/network/financier-marketplace/deals/${receivableId}/express-interest`, {
      method: 'POST',
      body: JSON.stringify({}),
    }),

  dealRoomSummary: () => apiRequest<DealRoomSummary>('/deal-room/summary'),

  dealRoomReceivables: () =>
    apiRequest<Array<{ receivable: Record<string, unknown>; invoice: Record<string, unknown> | null; offers: unknown[]; recommended_advance: number; risk_inputs: Record<string, unknown> }>>('/deal-room/receivables'),

  createDealOffer: (receivableId: string, advanceRateBps = 8000) =>
    apiRequest<Record<string, unknown>>(`/deal-room/receivables/${receivableId}/offers?advance_rate_bps=${advanceRateBps}`, {
      method: 'POST',
    }),
};
