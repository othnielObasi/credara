import { apiRequest } from './client';

export type TrustScore = {
  business_id: string;
  score: number;
  grade: string;
  factors_json: Record<string, unknown>;
};

export type FinanceReadiness = {
  business_id: string;
  verified_invoice_value: number;
  completed_transactions: number;
  dispute_rate: number;
  recommended_limit: number;
};

export const financeApi = {
  getScore: (businessId: string) => apiRequest<TrustScore>(`/finance/businesses/${businessId}/score`, { method: 'POST' }),
  getReadiness: (businessId: string) => apiRequest<FinanceReadiness>(`/finance/businesses/${businessId}/readiness`, { method: 'POST' }),
};
