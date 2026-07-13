import { apiRequest } from './client';

export type ProofBundle = {
  id: string;
  business_id: string;
  bundle_type: string;
  proof_hash: string;
  status: string;
  on_chain?: boolean;
  polygon_tx_hash: string | null;
  explorer_url: string | null;
  created_at: string;
};

export type AnchorResult = {
  bundle_id: string;
  proof_hash: string;
  polygon_tx_hash: string | null;
  on_chain: boolean;
  status?: string;
  explorer_url: string | null;
};

export const proofApi = {
  listBundles: () => apiRequest<ProofBundle[]>('/proof-ledger'),

  anchor: (body: { bundle_id?: string; invoice_id?: string; business_id?: string }) =>
    apiRequest<AnchorResult>('/proof-ledger/anchor', { method: 'POST', body: JSON.stringify(body) }),
};
