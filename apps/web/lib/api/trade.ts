import { apiRequest } from './client';

export type Order = {
  id: string;
  seller_business_id: string;
  buyer_business_id: string | null;
  buyer_name: string;
  description: string;
  total_amount: number;
  currency: string;
  status: string;
};

export type Invoice = {
  id: string;
  order_id: string;
  invoice_number: string;
  amount: number;
  currency: string;
  status: string;
  proof_hash: string | null;
};

export type DeliveryProof = {
  id: string;
  order_id: string;
  evidence_uri: string;
  confidence_score: number;
  status: string;
  proof_hash: string | null;
};

export type Receivable = {
  id: string;
  invoice_id: string;
  seller_business_id: string;
  debtor_name: string;
  face_value: number;
  currency: string;
  maturity_date: string;
  proof_hash: string;
  status: string;
  token_id: number | null;
  polygon_tx_hash: string | null;
};

export const tradeApi = {
  listOrders: (opts?: { sellerBusinessId?: string; buyerBusinessId?: string; pendingBuyer?: boolean }) => {
    const params = new URLSearchParams();
    if (opts?.sellerBusinessId) params.set('seller_business_id', opts.sellerBusinessId);
    if (opts?.buyerBusinessId) params.set('buyer_business_id', opts.buyerBusinessId);
    if (opts?.pendingBuyer) params.set('pending_buyer', 'true');
    const q = params.toString();
    return apiRequest<Order[]>(`/trade/orders${q ? `?${q}` : ''}`);
  },

  createOrder: (body: {
    seller_business_id: string;
    buyer_name: string;
    description: string;
    total_amount: number;
    currency?: string;
  }) => apiRequest<Order>('/trade/orders', { method: 'POST', body: JSON.stringify(body) }),

  confirmOrder: (orderId: string, buyerBusinessId: string) =>
    apiRequest<Order>(`/trade/orders/${orderId}/confirm`, {
      method: 'POST',
      body: JSON.stringify({ buyer_business_id: buyerBusinessId }),
    }),

  listInvoices: (opts?: { sellerBusinessId?: string; buyerBusinessId?: string }) => {
    const params = new URLSearchParams();
    if (opts?.sellerBusinessId) params.set('seller_business_id', opts.sellerBusinessId);
    if (opts?.buyerBusinessId) params.set('buyer_business_id', opts.buyerBusinessId);
    const q = params.toString();
    return apiRequest<Invoice[]>(`/trade/invoices${q ? `?${q}` : ''}`);
  },

  createInvoice: (body: { order_id: string; invoice_number: string; amount: number; due_date: string }) =>
    apiRequest<Invoice>('/trade/invoices', { method: 'POST', body: JSON.stringify(body) }),

  buyerConfirmInvoice: (invoiceId: string, buyerBusinessId: string) =>
    apiRequest<Invoice>(`/trade/invoices/${invoiceId}/buyer-confirm`, {
      method: 'POST',
      body: JSON.stringify({ buyer_business_id: buyerBusinessId }),
    }),

  listDeliveryProofs: (orderId?: string) => {
    const q = orderId ? `?order_id=${encodeURIComponent(orderId)}` : '';
    return apiRequest<DeliveryProof[]>(`/trade/delivery-proofs${q}`);
  },

  submitDeliveryProof: (body: {
    order_id: string;
    evidence_uri: string;
    otp_code?: string;
    gps_lat?: string;
    gps_lng?: string;
    metadata_json?: Record<string, unknown>;
  }) => apiRequest<DeliveryProof>('/trade/delivery-proofs', { method: 'POST', body: JSON.stringify(body) }),

  listReceivables: (sellerBusinessId?: string) => {
    const q = sellerBusinessId ? `?seller_business_id=${encodeURIComponent(sellerBusinessId)}` : '';
    return apiRequest<Receivable[]>(`/trade/receivables${q}`);
  },

  createReceivable: (invoiceId: string) =>
    apiRequest<Receivable>('/trade/receivables', { method: 'POST', body: JSON.stringify({ invoice_id: invoiceId }) }),
};
