import { apiRequest } from './client';

export type Order = {
  id: string;
  seller_business_id: string;
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

export const tradeApi = {
  listOrders: (sellerBusinessId?: string) => {
    const q = sellerBusinessId ? `?seller_business_id=${encodeURIComponent(sellerBusinessId)}` : '';
    return apiRequest<Order[]>(`/trade/orders${q}`);
  },

  createOrder: (body: {
    seller_business_id: string;
    buyer_name: string;
    description: string;
    total_amount: number;
    currency?: string;
  }) => apiRequest<Order>('/trade/orders', { method: 'POST', body: JSON.stringify(body) }),

  listInvoices: (sellerBusinessId?: string) => {
    const q = sellerBusinessId ? `?seller_business_id=${encodeURIComponent(sellerBusinessId)}` : '';
    return apiRequest<Invoice[]>(`/trade/invoices${q}`);
  },

  createInvoice: (body: { order_id: string; invoice_number: string; amount: number; due_date: string }) =>
    apiRequest<Invoice>('/trade/invoices', { method: 'POST', body: JSON.stringify(body) }),
};
