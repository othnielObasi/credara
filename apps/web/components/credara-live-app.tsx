'use client';

import { FormEvent, ReactNode, useEffect, useMemo, useState } from 'react';

type Role = 'sme' | 'buyer' | 'financier' | 'admin' | 'developer';
type PageKey =
  | 'dashboard'
  | 'buyerInbox'
  | 'contractDetail'
  | 'invoiceDetail'
  | 'delivery'
  | 'receivables'
  | 'directory'
  | 'opportunities'
  | 'proposals'
  | 'marketplace'
  | 'dealRoom'
  | 'wallets'
  | 'settlement'
  | 'settlementLedger'
  | 'reconciliation'
  | 'repayments'
  | 'proof'
  | 'evidence'
  | 'credit'
  | 'kyb'
  | 'onboarding'
  | 'businessProfile'
  | 'invitations'
  | 'members'
  | 'settings'
  | 'admin'
  | 'riskRules'
  | 'permissions'
  | 'launch'
  | 'apiExplorer';

type Wallet = {
  id: string;
  owner: string;
  role: Role | string;
  type: string;
  address: string;
  network: string;
  asset: string;
  stablecoinBalance: number;
  polBalance: number;
  status: string;
};

type PaymentIntent = {
  id: string;
  type: string;
  payer: string;
  payee: string;
  amount: number;
  asset: string;
  status: string;
  tx: string;
  confirmations: number;
  requiredConfirmations: number;
  reference: string;
};

type LedgerRow = {
  time: string;
  track: string;
  event: string;
  source: string;
  description: string;
  amount: number;
  status: string;
  verifier: string;
  docs: string[];
  role: string;
  reference: string;
};

type Escrow = {
  id: string;
  smartLcId: string;
  contract: string;
  asset: string;
  requiredAmount: number;
  fundedAmount: number;
  fundingParty: string;
  seller: string;
  status: string;
  confirmations: number;
  releaseCondition: string;
  refundCondition: string;
};

type SettingsState = {
  profile: Record<string, string | boolean>;
  workspace: Record<string, string | boolean>;
  notifications: Record<string, boolean>;
  security: Record<string, string | boolean>;
  developer: Record<string, string>;
  admin: Record<string, string | boolean>;
};

type AppState = {
  workspaceId: string | null;
  userId: string | null;
  token: string | null;
  connected: boolean;
  error: string | null;
  lastSync: string | null;
  page: PageKey;
  role: Role;
  settings: SettingsState;
  wallets: Wallet[];
  paymentIntents: PaymentIntent[];
  ledger: LedgerRow[];
  escrows: Escrow[];
  apiKeys: Array<{ id: string; name: string; key_prefix: string; scopes: string[]; status: string }>;
  invitations: Array<{ id: string; type: string; from: string; to: string; target: string; status: string; role: string; message: string }>;
  members: Array<{ name: string; email: string; role: string; status: string }>;
  reconciliation: { expected: number; onChain: number; ledger: number; variance: number; smartLcState: string; lastChecked: string; decision: string };
  authMode: 'signin' | 'signup';
};

const personas: Record<Role, [string, string, string, string]> = {
  sme: ['Acme Textiles Ltd', 'Amara Okafor', 'SME Admin', 'SME workspace'],
  buyer: ['Global Retail Ltd', 'Daniel Reed', 'Buyer Ops', 'Buyer workspace'],
  financier: ['Credara Capital', 'Maya Chen', 'Underwriter', 'Financier workspace'],
  admin: ['Credara Risk', 'Ravi Singh', 'Risk Admin', 'Admin workspace'],
  developer: ['Credara Dev Team', 'Dev User', 'Developer', 'Developer portal'],
};

const navGroups: Array<{ title: string; pages: Array<{ key: PageKey; label: string }> }> = [
  { title: 'Command', pages: [{ key: 'dashboard', label: 'Dashboard' }, { key: 'buyerInbox', label: 'Buyer Inbox' }] },
  { title: 'Trade Records', pages: [{ key: 'contractDetail', label: 'Contract Detail' }, { key: 'invoiceDetail', label: 'Invoice Detail' }, { key: 'delivery', label: 'Delivery Proof' }, { key: 'receivables', label: 'Receivables' }] },
  { title: 'Network', pages: [{ key: 'directory', label: 'Directory' }, { key: 'opportunities', label: 'Opportunities' }, { key: 'proposals', label: 'Proposals' }, { key: 'marketplace', label: 'Marketplace' }, { key: 'dealRoom', label: 'Deal Room' }] },
  { title: 'Settlement', pages: [{ key: 'wallets', label: 'Wallets' }, { key: 'settlement', label: 'Smart LC' }, { key: 'settlementLedger', label: 'Settlement Ledger' }, { key: 'reconciliation', label: 'Reconciliation' }, { key: 'repayments', label: 'Repayments' }] },
  { title: 'Trust', pages: [{ key: 'proof', label: 'Proof Ledger' }, { key: 'evidence', label: 'Evidence' }, { key: 'credit', label: 'Credit' }, { key: 'kyb', label: 'KYB' }] },
  { title: 'Setup', pages: [{ key: 'onboarding', label: 'Onboarding' }, { key: 'businessProfile', label: 'Business Profile' }, { key: 'invitations', label: 'Invitations' }, { key: 'members', label: 'Members' }, { key: 'settings', label: 'Settings' }] },
  { title: 'Platform', pages: [{ key: 'admin', label: 'Admin' }, { key: 'riskRules', label: 'Risk Rules' }, { key: 'permissions', label: 'Permissions' }, { key: 'launch', label: 'Launch' }, { key: 'apiExplorer', label: 'API Explorer' }] },
];

const roleAllowed: Record<Role, PageKey[]> = {
  sme: ['dashboard', 'contractDetail', 'invoiceDetail', 'delivery', 'receivables', 'directory', 'opportunities', 'proposals', 'marketplace', 'wallets', 'settlement', 'settlementLedger', 'reconciliation', 'repayments', 'proof', 'evidence', 'credit', 'kyb', 'onboarding', 'businessProfile', 'invitations', 'members', 'settings'],
  buyer: ['dashboard', 'buyerInbox', 'contractDetail', 'invoiceDetail', 'delivery', 'directory', 'opportunities', 'wallets', 'settlement', 'settlementLedger', 'reconciliation', 'repayments', 'proof', 'evidence', 'credit', 'kyb', 'onboarding', 'businessProfile', 'invitations', 'members', 'settings'],
  financier: ['dashboard', 'marketplace', 'dealRoom', 'receivables', 'evidence', 'credit', 'kyb', 'wallets', 'settlementLedger', 'reconciliation', 'repayments', 'proof', 'directory', 'onboarding', 'businessProfile', 'invitations', 'members', 'settings'],
  admin: ['dashboard', 'admin', 'riskRules', 'permissions', 'kyb', 'proof', 'evidence', 'settlementLedger', 'reconciliation', 'wallets', 'onboarding', 'businessProfile', 'invitations', 'members', 'settings', 'launch', 'apiExplorer'],
  developer: ['dashboard', 'settings', 'apiExplorer', 'onboarding', 'businessProfile', 'members', 'proof', 'wallets', 'settlementLedger'],
};

const pageTitles: Record<PageKey, [string, string]> = {
  dashboard: ['Workspace Dashboard', 'Live trade finance workflow, risk and settlement status.'],
  buyerInbox: ['Buyer Inbox', 'Contract, invoice, delivery and settlement actions for buyers.'],
  contractDetail: ['Contract Detail', 'Commercial terms, parties, proof rules and Smart LC state.'],
  invoiceDetail: ['Invoice Detail', 'Buyer confirmation, delivery proof, financing and settlement evidence.'],
  delivery: ['Delivery Proof', 'Evidence, logistics verification and buyer confirmation.'],
  receivables: ['Receivables', 'Tokenized invoice assets and finance readiness.'],
  directory: ['Business Directory', 'Verified buyers, sellers, financiers and service partners.'],
  opportunities: ['Opportunities', 'Trade opportunities that can become contracts and invoices.'],
  proposals: ['Proposals', 'Seller responses, buyer review and counterparty actions.'],
  marketplace: ['Financier Marketplace', 'Receivables and evidence bundles for underwriting.'],
  dealRoom: ['Deal Room', 'Financier workspace for receivable evidence review.'],
  wallets: ['Wallets & Payments', 'Stablecoin payment intents and wallet balances.'],
  settlement: ['Smart LC Settlement', 'Escrow funding, release conditions and contract state.'],
  settlementLedger: ['Settlement Ledger', 'Confirmed, pending and fallback settlement receipts.'],
  reconciliation: ['Reconciliation', 'Match payment, chain receipt, ledger and escrow state.'],
  repayments: ['Repayments', 'Repayment schedule, allocation and status.'],
  proof: ['Proof Ledger', 'Hash receipts and proof events across the workflow.'],
  evidence: ['Evidence Bundles', 'Documents and proof packages for each financing decision.'],
  credit: ['Trade Credit', 'Credit score, readiness and score attestations.'],
  kyb: ['KYB', 'Business verification and risk flags.'],
  onboarding: ['Onboarding', 'Workspace setup, KYB, wallet and first workflow.'],
  businessProfile: ['Business Profile', 'Legal identity, roles, region and operating profile.'],
  invitations: ['Invitations', 'Counterparty invitations and target workflow routing.'],
  members: ['Members', 'Workspace users, roles and statuses.'],
  settings: ['Settings', 'Profile, workspace, security, API and webhook settings.'],
  admin: ['Admin Console', 'Risk operations and governance review.'],
  riskRules: ['Risk Rules', 'Rules that block unsafe financing and settlement actions.'],
  permissions: ['Permissions', 'Role capability matrix.'],
  launch: ['Launch Readiness', 'Production rollout milestones and controls.'],
  apiExplorer: ['API Explorer', 'Gateway endpoints, keys, webhooks and sample calls.'],
};

const initialState: AppState = {
  workspaceId: null,
  userId: null,
  token: null,
  connected: false,
  error: null,
  lastSync: null,
  page: 'dashboard',
  role: 'sme',
  settings: {
    profile: { name: 'Amara Okafor', email: 'amara@acme.example', language: 'English', timezone: 'UTC +0' },
    workspace: { name: 'Acme Textiles Ltd', role: 'SME', environment: 'sandbox', region: 'UAE / UK' },
    notifications: { payment: true, proof: true, kyb: true, invites: true },
    security: { mfa: true, sso: false, sessionTimeout: '30 minutes' },
    developer: { apiKey: 'No live key generated', webhook: 'https://api.acme.example/credara/webhooks', mode: 'sandbox', events: 'proof.anchored, receivable.created, payment.confirmed' },
    admin: { riskRules: true, auditExport: true },
  },
  wallets: [
    { id: 'WAL-SME-001', owner: 'Acme Textiles Ltd', role: 'sme', type: 'Business wallet', address: '0xB8fA1bA7C0E9dA4F91A2bC8821aD98aE2213B011', network: 'Polygon Amoy', asset: 'MockUSDC', stablecoinBalance: 50000, polBalance: 18, status: 'Active' },
    { id: 'WAL-FIN-001', owner: 'Credara Capital', role: 'financier', type: 'Treasury wallet', address: '0xF1nA9cE002bcA77e0199882fA09331CfedA01009', network: 'Polygon Amoy', asset: 'MockUSDC', stablecoinBalance: 250000, polBalance: 44.1, status: 'Active' },
  ],
  paymentIntents: [
    { id: 'PI-2026-001', type: 'Smart LC escrow funding', payer: 'Global Retail Ltd', payee: 'SmartLC LC-015', amount: 24500, asset: 'MockUSDC', status: 'Confirmed', tx: '0x9a20...19d2a', confirmations: 5, requiredConfirmations: 3, reference: 'LC-015' },
  ],
  ledger: [
    { time: 'Jun 04 09:35:42', track: 'Seller', event: 'advance-payout', source: 'Credara Capital', description: 'Financier advanced 80% of receivable value to seller wallet.', amount: 19600, status: 'Confirmed', verifier: '0xadv...45fa', docs: ['Invoice', 'Receipt', 'Proof'], role: 'sme', reference: 'REC-045' },
    { time: 'Jun 04 09:40:11', track: 'Buyer', event: 'escrow-funded', source: 'Buyer wallet', description: 'Smart LC escrow funded and held pending release conditions.', amount: 24500, status: 'Confirmed', verifier: '0x9a20...19d2a', docs: ['Contract', 'Receipt', 'Proof'], role: 'buyer', reference: 'LC-015' },
  ],
  escrows: [
    { id: 'ESC-015', smartLcId: 'LC-015', contract: '0xSLC...015', asset: 'MockUSDC', requiredAmount: 24500, fundedAmount: 24500, fundingParty: 'Global Retail Ltd', seller: 'Acme Textiles Ltd', status: 'Funded', confirmations: 5, releaseCondition: 'delivery verified + no open dispute', refundCondition: 'deadline missed or dispute upheld' },
  ],
  apiKeys: [],
  invitations: [
    { id: 'INVITE-001', type: 'Trade Contract', from: 'Global Retail Ltd', to: 'Acme Textiles Ltd', target: 'TC-2026-0012', status: 'Pending action', role: 'seller', message: 'Review and accept trade contract' },
    { id: 'INVITE-002', type: 'Invoice Confirmation', from: 'Acme Textiles Ltd', to: 'Global Retail Ltd', target: 'INV-2025-045', status: 'Accepted', role: 'buyer', message: 'Buyer confirmed invoice obligation' },
  ],
  members: [
    { name: 'Amara Okafor', email: 'amara@acme.example', role: 'SME Admin', status: 'Active' },
    { name: 'Daniel Reed', email: 'daniel@globalretail.example', role: 'Buyer Ops', status: 'Invited' },
    { name: 'Maya Chen', email: 'maya@credaracapital.example', role: 'Underwriter', status: 'Active' },
  ],
  reconciliation: { expected: 24500, onChain: 24500, ledger: 24500, variance: 0, smartLcState: 'Funded', lastChecked: 'Not run', decision: 'Valid / reconciled' },
  authMode: 'signup',
};

const apiBase = process.env.NEXT_PUBLIC_API_BASE || '/api/v1';
const realBase = `${apiBase}/real`;

function fmt(value: number | string | undefined) {
  return `£${Number(value || 0).toLocaleString('en-GB')}`;
}

function titleCase(value: string | undefined) {
  return String(value || '').replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
}

function statusTone(status: string) {
  if (/confirmed|active|ready|verified|anchored|tokenized|released|approved|low|valid|funded/i.test(status)) return 'green';
  if (/pending|submitted|review|sent|offer|medium|partial/i.test(status)) return 'amber';
  if (/disputed|rejected|high|failed|blocked/i.test(status)) return 'red';
  return 'grey';
}

function Pill({ children, tone }: { children: string; tone?: string }) {
  return <span className={`pill ${tone || statusTone(children)}`}>{children}</span>;
}

function useCredaraApp(startInWorkspace: boolean) {
  const [state, setState] = useState<AppState>({ ...initialState, page: startInWorkspace ? 'dashboard' : 'dashboard' });
  const [toast, setToast] = useState<{ title: string; message?: string } | null>(null);
  const [authForm, setAuthForm] = useState({ fullName: 'Amara Okafor', email: 'amara@acme.example', password: '', businessName: 'Acme Textiles Ltd', role: 'sme' as Role, country: 'AE', registrationNumber: 'AE-TRD-2026-0012', sector: 'Trade finance' });

  const notify = (title: string, message?: string) => {
    setToast({ title, message });
    window.setTimeout(() => setToast(null), 3200);
  };

  const withState = (patch: Partial<AppState>) => setState((current) => ({ ...current, ...patch }));

  async function authFetch(path: string, options: RequestInit = {}) {
    const token = state.token || (typeof window !== 'undefined' ? localStorage.getItem('credara.authToken') : null);
    const res = await fetch(`${realBase}${path}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...(options.headers || {}),
      },
    });
    if (!res.ok) throw new Error((await res.text()) || `HTTP ${res.status}`);
    return res.json();
  }

  async function platformFetch(path: string, options: RequestInit = {}) {
    const res = await fetch(`${apiBase}${path}`, options);
    if (!res.ok) throw new Error((await res.text()) || `HTTP ${res.status}`);
    return res.json();
  }

  function rememberAuth(token: string, role: Role) {
    localStorage.setItem('credara.authToken', token);
    localStorage.setItem('credara.role', role);
    withState({ token, role });
  }

  async function loadWorkspace() {
    const data = await authFetch('/workspaces/me');
    const first = data.workspaces?.[0];
    const patch: Partial<AppState> = {
      userId: data.user?.id || state.userId,
      role: (data.user?.role as Role) || state.role,
      connected: true,
      error: null,
      lastSync: new Date().toLocaleTimeString(),
    };
    if (first) {
      patch.workspaceId = first.workspace.id;
      patch.settings = {
        ...state.settings,
        profile: { ...state.settings.profile, name: data.user?.full_name || state.settings.profile.name, email: data.user?.email || state.settings.profile.email },
        workspace: { ...state.settings.workspace, name: first.workspace.name, role: first.workspace.primary_role, environment: first.workspace.environment, region: first.workspace.region || state.settings.workspace.region },
      };
    }
    setState((current) => ({ ...current, ...patch }));
    return first?.workspace.id as string | undefined;
  }

  async function ensureWorkspace() {
    const existing = state.workspaceId || (await loadWorkspace());
    if (existing) return existing;
    const p = personas[state.role];
    const data = await authFetch('/onboarding/start', {
      method: 'POST',
      body: JSON.stringify({
        role: state.role,
        business_name: authForm.businessName || p[0],
        country: authForm.country,
        registration_number: authForm.registrationNumber,
        sector: authForm.sector,
        wallet_address: state.wallets[0]?.address,
      }),
    });
    withState({ workspaceId: data.workspace.id, userId: data.user.id, connected: true, lastSync: new Date().toLocaleTimeString() });
    return data.workspace.id as string;
  }

  async function loadOperationalState(workspaceId?: string) {
    const id = workspaceId || state.workspaceId || (await ensureWorkspace());
    const q = `workspace_id=${encodeURIComponent(id)}`;
    const [settings, apiKeys, wallets, payments, escrows, ledger] = await Promise.all([
      authFetch(`/settings?${q}`).catch(() => null),
      authFetch(`/api-keys?${q}`).catch(() => []),
      authFetch(`/wallets?${q}`).catch(() => []),
      authFetch(`/payment-intents?${q}`).catch(() => []),
      authFetch(`/escrows?${q}`).catch(() => []),
      authFetch(`/ledger?${q}`).catch(() => []),
    ]);
    setState((current) => ({
      ...current,
      settings: settings
        ? {
            profile: { ...current.settings.profile, ...(settings.profile || {}) },
            workspace: { ...current.settings.workspace, ...(settings.workspace || {}) },
            notifications: { ...current.settings.notifications, ...(settings.notifications || {}) },
            security: { ...current.settings.security, ...(settings.security || {}) },
            developer: { ...current.settings.developer, ...(settings.developer || {}), apiKey: apiKeys[0]?.key_prefix ? `${apiKeys[0].key_prefix}...` : current.settings.developer.apiKey },
            admin: { ...current.settings.admin, ...(settings.admin || {}) },
          }
        : current.settings,
      apiKeys,
      wallets: wallets.length ? wallets.map(mapWallet) : current.wallets,
      paymentIntents: payments.length ? payments.map((p: Record<string, unknown>) => mapPayment(p, current.role, current.settings.workspace.name as string)) : current.paymentIntents,
      escrows: escrows.length ? escrows.map(mapEscrow) : current.escrows,
      ledger: ledger.length ? ledger.map(mapLedger) : current.ledger,
      connected: true,
      error: null,
      lastSync: new Date().toLocaleTimeString(),
    }));
  }

  async function signUp(event: FormEvent) {
    event.preventDefault();
    if (authForm.password.length < 8) return notify('Password required', 'Use at least 8 characters.');
    try {
      const auth = await platformFetch('/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: authForm.email, full_name: authForm.fullName, password: authForm.password, role: authForm.role }),
      });
      rememberAuth(auth.access_token, auth.role);
      withState({ role: auth.role, page: 'onboarding' });
      const id = await ensureWorkspace();
      await loadOperationalState(id);
      notify('Workspace created', 'Credara is now using live backend records.');
    } catch (error) {
      notify('Signup failed', error instanceof Error ? error.message.slice(0, 140) : 'Unknown error');
    }
  }

  async function signIn(event: FormEvent) {
    event.preventDefault();
    try {
      const form = new URLSearchParams();
      form.set('username', authForm.email);
      form.set('password', authForm.password);
      const auth = await platformFetch('/auth/login', { method: 'POST', headers: { 'Content-Type': 'application/x-www-form-urlencoded' }, body: form.toString() });
      rememberAuth(auth.access_token, auth.role);
      const id = await loadWorkspace();
      await loadOperationalState(id);
      notify('Signed in', 'Live workspace loaded.');
    } catch (error) {
      notify('Sign in failed', error instanceof Error ? error.message.slice(0, 140) : 'Unknown error');
    }
  }

  async function connectLive() {
    try {
      if (!state.token && !localStorage.getItem('credara.authToken')) return notify('Sign in required', 'Create or sign into a workspace first.');
      const id = await loadWorkspace();
      await loadOperationalState(id);
      notify('Backend connected', 'Persistent records are loaded.');
    } catch (error) {
      withState({ connected: false, error: error instanceof Error ? error.message : 'Connection failed' });
      notify('Backend not connected', error instanceof Error ? error.message.slice(0, 140) : 'Connection failed');
    }
  }

  function signOut() {
    localStorage.removeItem('credara.authToken');
    localStorage.removeItem('credara.role');
    setState({ ...initialState });
    notify('Signed out', 'You are back on the public surface.');
  }

  async function createApiKey() {
    try {
      const workspaceId = await ensureWorkspace();
      const data = await authFetch('/api-keys', { method: 'POST', body: JSON.stringify({ workspace_id: workspaceId, name: 'Default integration key', scopes: ['proof:read', 'receivables:write', 'payments:write'] }) });
      setState((current) => ({ ...current, settings: { ...current.settings, developer: { ...current.settings.developer, apiKey: data.api_key } }, apiKeys: [{ id: data.id, name: 'Default integration key', key_prefix: data.key_prefix, scopes: data.scopes, status: data.status }, ...current.apiKeys] }));
      notify('API key generated', 'Copy it now; the backend stores only the hash.');
    } catch (error) {
      notify('API key failed', error instanceof Error ? error.message.slice(0, 140) : 'Unknown error');
    }
  }

  async function createPaymentIntent(): Promise<PaymentIntent | null> {
    try {
      const workspaceId = await ensureWorkspace();
      const walletAddress = state.wallets[0]?.address || initialState.wallets[0].address;
      let wallets = await authFetch(`/wallets?workspace_id=${encodeURIComponent(workspaceId)}`);
      let wallet = wallets.find((w: Record<string, unknown>) => w.address === walletAddress);
      if (!wallet) {
        wallet = await authFetch('/wallets', { method: 'POST', body: JSON.stringify({ workspace_id: workspaceId, owner_name: state.settings.workspace.name, address: walletAddress, stablecoin_balance: 50000, gas_balance: 18 }) });
      }
      const intent = await authFetch('/payment-intents', {
        method: 'POST',
        body: JSON.stringify({ workspace_id: workspaceId, intent_type: 'Smart LC escrow funding', payer_wallet_id: wallet.id, payee_reference: 'SmartLC LC-015', reference_type: 'smart_lc', reference_id: 'LC-015', amount: 24500, idempotency_key: `ui-${Date.now()}` }),
      });
      const mapped = mapPayment({ ...intent, intent_type: 'Smart LC escrow funding', reference_id: 'LC-015' }, state.role, state.settings.workspace.name as string);
      setState((current) => ({ ...current, paymentIntents: [mapped, ...current.paymentIntents] }));
      notify('Payment intent persisted', intent.id);
      return mapped;
    } catch (error) {
      notify('Payment intent failed', error instanceof Error ? error.message.slice(0, 140) : 'Unknown error');
      return null;
    }
  }

  async function confirmPayment(payment?: PaymentIntent | null): Promise<PaymentIntent | null> {
    try {
      const latest = payment || state.paymentIntents[0];
      if (!latest) {
        notify('No payment intent', 'Create one first.');
        return null;
      }
      await authFetch(`/payment-intents/${latest.id}/submit`, { method: 'POST', body: JSON.stringify({ tx_hash: `0xui${Date.now().toString(16)}`, confirmations: 1 }) });
      const confirmed = await authFetch(`/payment-intents/${latest.id}/confirm`, { method: 'POST', body: JSON.stringify({ confirmations: 3, on_chain_amount: latest.amount }) });
      setState((current) => ({ ...current, paymentIntents: current.paymentIntents.map((p) => (p.id === latest.id ? { ...p, status: titleCase(confirmed.status), confirmations: confirmed.confirmations, tx: 'confirmed on backend' } : p)) }));
      await refreshLedger();
      notify('Payment confirmed', 'Ledger entries were generated by the backend.');
      return { ...latest, status: titleCase(confirmed.status), confirmations: confirmed.confirmations };
    } catch (error) {
      notify('Confirmation failed', error instanceof Error ? error.message.slice(0, 140) : 'Unknown error');
      return null;
    }
  }

  async function confirmLatestPayment() {
    return confirmPayment();
  }

  async function ensureEscrow() {
    const workspaceId = await ensureWorkspace();
    const escrows = await authFetch(`/escrows?workspace_id=${encodeURIComponent(workspaceId)}`);
    if (escrows[0]) return escrows[0];
    return authFetch('/escrows', { method: 'POST', body: JSON.stringify({ workspace_id: workspaceId, smart_lc_id: 'LC-015', contract_address: '0xSLC...015', required_amount: 24500, funding_party: state.settings.workspace.name, seller: 'Acme Textiles Ltd', asset: 'MockUSDC' }) });
  }

  async function fundEscrow() {
    try {
      let latest: PaymentIntent | null = state.paymentIntents[0] || (await createPaymentIntent());
      if (latest && latest.status !== 'Confirmed') latest = await confirmPayment(latest);
      if (!latest) throw new Error('No confirmed payment intent available.');
      const escrow = await ensureEscrow();
      const funded = await authFetch(`/escrows/${escrow.id}/fund`, { method: 'POST', body: JSON.stringify({ payment_intent_id: latest.id }) });
      setState((current) => ({ ...current, escrows: [mapEscrow({ ...escrow, status: funded.status, funded_amount: funded.funded_amount, required_amount: funded.required_amount })] }));
      await refreshLedger();
      notify('Escrow funded', 'Payment intent, escrow and ledger are reconciled.');
    } catch (error) {
      notify('Escrow funding failed', error instanceof Error ? error.message.slice(0, 140) : 'Unknown error');
    }
  }

  async function refreshLedger() {
    try {
      const workspaceId = await ensureWorkspace();
      const rows = await authFetch(`/ledger?workspace_id=${encodeURIComponent(workspaceId)}`);
      setState((current) => ({ ...current, ledger: rows.length ? rows.map(mapLedger) : current.ledger, lastSync: new Date().toLocaleTimeString(), connected: true }));
    } catch (error) {
      notify('Ledger sync failed', error instanceof Error ? error.message.slice(0, 140) : 'Unknown error');
    }
  }

  async function reconcile() {
    try {
      const reference = state.escrows[0]?.id || state.paymentIntents[0]?.id || 'LC-015';
      const type = state.escrows[0]?.id ? 'escrow' : 'payment_intent';
      const expected = state.escrows[0]?.requiredAmount || 24500;
      const rec = await authFetch(`/reconciliation/${type}/${reference}?expected_amount=${encodeURIComponent(expected)}`, { method: 'POST' });
      withState({ reconciliation: { expected: rec.expected_amount, onChain: rec.on_chain_amount, ledger: rec.internal_ledger_amount, variance: rec.variance, smartLcState: titleCase(rec.smart_lc_state), lastChecked: new Date(rec.checked_at).toLocaleTimeString(), decision: titleCase(rec.decision) } });
      notify('Reconciliation complete', `Decision: ${titleCase(rec.decision)}.`);
    } catch (error) {
      notify('Reconciliation failed', error instanceof Error ? error.message.slice(0, 140) : 'Unknown error');
    }
  }

  async function releaseEscrow() {
    try {
      const escrow = state.escrows[0];
      if (!escrow?.id) throw new Error('No backend escrow available.');
      const released = await authFetch(`/escrows/${escrow.id}/release`, { method: 'POST', body: JSON.stringify({ reason: 'Release conditions satisfied from Credara UI' }) });
      setState((current) => ({ ...current, escrows: current.escrows.map((e) => (e.id === escrow.id ? { ...e, status: titleCase(released.status) } : e)) }));
      await refreshLedger();
      notify('Payment released', 'Backend escrow release and settlement ledger were updated.');
    } catch (error) {
      notify('Release failed', error instanceof Error ? error.message.slice(0, 140) : 'Unknown error');
    }
  }

  useEffect(() => {
    const token = localStorage.getItem('credara.authToken');
    const role = localStorage.getItem('credara.role') as Role | null;
    if (!token) return;
    setState((current) => ({ ...current, token, role: role || current.role }));
    void (async () => {
      try {
        const id = await loadWorkspace();
        await loadOperationalState(id);
      } catch (error) {
        withState({ connected: false, error: error instanceof Error ? error.message : 'Connection failed' });
      }
    })();
  }, []);

  return { state, setState, withState, authForm, setAuthForm, toast, notify, signUp, signIn, signOut, connectLive, createApiKey, createPaymentIntent, confirmLatestPayment, fundEscrow, refreshLedger, reconcile, releaseEscrow };
}

function mapWallet(w: Record<string, unknown>): Wallet {
  return { id: String(w.id), owner: String(w.owner_name || 'Workspace wallet'), role: 'sme', type: String(w.wallet_type || 'connected'), address: String(w.address), network: String(w.network || 'Polygon Amoy'), asset: String(w.stablecoin_asset || 'MockUSDC'), stablecoinBalance: Number(w.stablecoin_balance || 0), polBalance: Number(w.gas_balance || 0), status: titleCase(String(w.status || 'active')) };
}

function mapPayment(p: Record<string, unknown>, role: Role, payerName: string): PaymentIntent {
  return { id: String(p.id), type: String(p.intent_type || 'Payment intent'), payer: payerName || personas[role][0], payee: String(p.reference_id || p.reference_type || 'Settlement'), amount: Number(p.amount || 0), asset: String(p.asset || 'MockUSDC'), status: titleCase(String(p.status || 'pending')), tx: String(p.tx_hash || 'awaiting signature'), confirmations: Number(p.confirmations || 0), requiredConfirmations: Number(p.required_confirmations || 3), reference: String(p.reference_id || '') };
}

function mapEscrow(e: Record<string, unknown>): Escrow {
  return { id: String(e.id), smartLcId: String(e.smart_lc_id), contract: String(e.contract_address || 'contract pending'), asset: String(e.asset || 'MockUSDC'), requiredAmount: Number(e.required_amount || 0), fundedAmount: Number(e.funded_amount || 0), fundingParty: String(e.funding_party || 'Workspace wallet'), seller: String(e.seller || 'Seller'), status: titleCase(String(e.status || 'created')), confirmations: ['funded', 'released'].includes(String(e.status)) ? 3 : 0, releaseCondition: String(e.release_condition || 'Invoice confirmed + delivery verified + proof anchored + no dispute'), refundCondition: String(e.refund_condition || 'Deadline missed or dispute upheld') };
}

function mapLedger(r: Record<string, unknown>): LedgerRow {
  return { time: new Date(String(r.timestamp)).toLocaleString(), track: String(r.track || 'Settlement'), event: String(r.event || 'event'), source: String(r.source || 'Credara'), description: String(r.description || ''), amount: Number(r.amount || 0), status: titleCase(String(r.status || 'pending')), verifier: String(r.verifier || '-'), docs: Array.isArray(r.docs) ? (r.docs as string[]) : [], role: String(r.role || 'system'), reference: String(r.reference_id || '') };
}

export default function CredaraLiveApp({ startInWorkspace = false }: { startInWorkspace?: boolean }) {
  const app = useCredaraApp(startInWorkspace);
  const { state, setState, authForm, setAuthForm } = app;
  const currentPersona = personas[state.role];
  const allowed = roleAllowed[state.role];
  const [title, subtitle] = pageTitles[allowed.includes(state.page) ? state.page : allowed[0]];
  const activePage = allowed.includes(state.page) ? state.page : allowed[0];

  const switchPage = (page: PageKey) => setState((current) => ({ ...current, page: allowed.includes(page) ? page : allowed[0] }));
  const metrics = useMemo(() => getMetrics(state), [state]);

  return (
    <main className="credara-app">
      {toastView(app.toast)}
      {!state.token ? (
        <PublicSurface app={app} />
      ) : (
        <div className="workspace-layout">
          <aside className="sidebar">
            <div className="brand-row"><div className="brand-mark">C</div><div><strong>Credara</strong><span>Enterprise trade finance</span></div></div>
            <div className="tenant-card"><div className="tenant-avatar">{currentPersona[0].split(' ').slice(0, 2).map((w) => w[0]).join('')}</div><div><strong>{currentPersona[0]}</strong><span>{currentPersona[3]}</span></div></div>
            <select className="role-select" value={state.role} onChange={(e) => setState((current) => ({ ...current, role: e.target.value as Role, page: roleAllowed[e.target.value as Role][0] }))}>
              {Object.keys(personas).map((role) => <option key={role} value={role}>{titleCase(role)}</option>)}
            </select>
            <nav className="nav-stack">
              {navGroups.map((group) => {
                const pages = group.pages.filter((page) => allowed.includes(page.key));
                if (!pages.length) return null;
                return <div key={group.title} className="nav-group"><p>{group.title}</p>{pages.map((page) => <button key={page.key} className={`nav-item ${activePage === page.key ? 'active' : ''}`} onClick={() => switchPage(page.key)}>{page.label}</button>)}</div>;
              })}
            </nav>
          </aside>
          <section className="workspace-main">
            <header className="topbar">
              <div><p className="eyebrow">Credara Enterprise</p><h1>{title}</h1><span>{subtitle}</span></div>
              <div className="top-actions">
                <button className="btn secondary" onClick={app.connectLive}>{state.connected ? 'Sync live' : 'Connect live'}</button>
                <button className="btn" onClick={() => switchPage('contractDetail')}>New trade</button>
                <button className="btn ghost" onClick={app.signOut}>Sign out</button>
              </div>
            </header>
            <LiveBar state={state} onConnect={app.connectLive} />
            <PageRenderer page={activePage} state={state} app={app} metrics={metrics} switchPage={switchPage} />
          </section>
        </div>
      )}
    </main>
  );

  function PublicSurface({ app }: { app: ReturnType<typeof useCredaraApp> }) {
    const isSignup = state.authMode === 'signup';
    return (
      <section className="public-shell">
        <nav className="public-nav"><div className="brand-row"><div className="brand-mark">C</div><strong>credara</strong></div><div><button className="btn secondary" onClick={() => setState((current) => ({ ...current, authMode: 'signin' }))}>Sign in</button><button className="btn" onClick={() => setState((current) => ({ ...current, authMode: 'signup' }))}>Sign up</button></div></nav>
        <div className="public-grid">
          <div className="hero-copy"><small>Polygon-powered SME trade finance</small><h1>Verified trade, financeable invoices, and stablecoin settlement.</h1><p>Credara connects business onboarding, KYB, trade contracts, invoice proof, receivable financing, Smart LC escrow, settlement ledger and reconciliation in one enterprise workspace.</p><div className="hero-actions"><button className="btn" onClick={() => setState((current) => ({ ...current, authMode: 'signup' }))}>Create workspace</button><button className="btn secondary" onClick={() => setState((current) => ({ ...current, authMode: 'signin' }))}>Sign in to workspace</button></div></div>
          <form className="auth-card" onSubmit={isSignup ? app.signUp : app.signIn}>
            <div className="auth-tabs"><button type="button" className={isSignup ? 'active' : ''} onClick={() => setState((current) => ({ ...current, authMode: 'signup' }))}>Sign up</button><button type="button" className={!isSignup ? 'active' : ''} onClick={() => setState((current) => ({ ...current, authMode: 'signin' }))}>Sign in</button></div>
            <h2>{isSignup ? 'Create workspace' : 'Sign in'}</h2>
            {isSignup && <><label>Full name<input value={authForm.fullName} onChange={(e) => setAuthForm({ ...authForm, fullName: e.target.value })} /></label><label>Business name<input value={authForm.businessName} onChange={(e) => setAuthForm({ ...authForm, businessName: e.target.value })} /></label><label>Role<select value={authForm.role} onChange={(e) => setAuthForm({ ...authForm, role: e.target.value as Role })}>{Object.keys(personas).map((role) => <option key={role} value={role}>{titleCase(role)}</option>)}</select></label></>}
            <label>Email<input value={authForm.email} onChange={(e) => setAuthForm({ ...authForm, email: e.target.value })} /></label>
            <label>Password<input type="password" value={authForm.password} onChange={(e) => setAuthForm({ ...authForm, password: e.target.value })} /></label>
            <button className="btn" type="submit">{isSignup ? 'Create live workspace' : 'Sign in'}</button>
          </form>
        </div>
      </section>
    );
  }
}

function LiveBar({ state, onConnect }: { state: AppState; onConnect: () => void }) {
  return <div className="live-bar"><div><strong><span className={`live-dot ${state.connected ? 'connected' : state.error ? 'failed' : ''}`} />{state.connected ? 'Persistent backend connected' : state.token ? 'Backend not connected' : 'Sign in required for live data'}</strong><span>{state.connected ? `Last sync ${state.lastSync}` : state.error || 'Live actions require an authenticated workspace.'}</span></div><button className="btn secondary small" onClick={onConnect}>Connect</button></div>;
}

function PageRenderer({ page, state, app, metrics, switchPage }: { page: PageKey; state: AppState; app: ReturnType<typeof useCredaraApp>; metrics: ReturnType<typeof getMetrics>; switchPage: (page: PageKey) => void }) {
  if (page === 'dashboard') return <Dashboard state={state} metrics={metrics} switchPage={switchPage} />;
  if (page === 'wallets') return <Wallets state={state} app={app} />;
  if (page === 'settlementLedger') return <Ledger state={state} app={app} />;
  if (page === 'reconciliation') return <Reconciliation state={state} app={app} />;
  if (page === 'settlement') return <Settlement state={state} app={app} />;
  if (page === 'settings') return <Settings state={state} app={app} />;
  if (page === 'apiExplorer') return <ApiExplorer state={state} app={app} />;
  if (page === 'contractDetail' || page === 'invoiceDetail') return <RecordDetail page={page} switchPage={switchPage} />;
  if (['onboarding', 'businessProfile', 'invitations', 'members'].includes(page)) return <SetupPage page={page} state={state} switchPage={switchPage} />;
  if (['proof', 'evidence', 'credit', 'kyb'].includes(page)) return <TrustPage page={page} state={state} />;
  if (['directory', 'opportunities', 'proposals', 'marketplace', 'dealRoom'].includes(page)) return <NetworkPage page={page} state={state} />;
  if (['buyerInbox', 'delivery', 'receivables', 'repayments', 'admin', 'riskRules', 'permissions', 'launch'].includes(page)) return <OperationalPage page={page} state={state} switchPage={switchPage} />;
  return <Dashboard state={state} metrics={metrics} switchPage={switchPage} />;
}

function Dashboard({ state, metrics, switchPage }: { state: AppState; metrics: ReturnType<typeof getMetrics>; switchPage: (page: PageKey) => void }) {
  return <div className="page-stack"><Banner /><section className="metric-grid"><Metric label="Verified invoices" value={metrics.verifiedCount} helper={fmt(metrics.verifiedValue)} /><Metric label="Receivables" value={metrics.recCount} helper={fmt(metrics.recVal)} /><Metric label="Active escrow" value={metrics.activeCount} helper={fmt(metrics.activeVal)} /><Metric label="Trust score" value={`${metrics.trust}/100`} helper="finance readiness" /></section><section className="two-grid"><Panel title="Priority queue" action={<button className="btn secondary small" onClick={() => switchPage('contractDetail')}>Contract</button>}><ActionRows rows={[['Review contract', 'TC-2026-0012', 'contractDetail'], ['Confirm invoice', 'INV-2025-045', 'invoiceDetail'], ['Sync ledger', `${state.ledger.length} rows`, 'settlementLedger']]} switchPage={switchPage} /></Panel><Panel title="Settlement snapshot"><Detail label="Escrow" value={state.escrows[0]?.smartLcId || 'No escrow'} /><Detail label="Status" value={state.escrows[0]?.status || 'Pending'} /><Detail label="Funded" value={fmt(state.escrows[0]?.fundedAmount || 0)} /><button className="btn secondary full" onClick={() => switchPage('settlement')}>Open settlement</button></Panel></section></div>;
}

function Wallets({ state, app }: { state: AppState; app: ReturnType<typeof useCredaraApp> }) {
  const wallet = state.wallets[0];
  return <div className="page-stack"><PageIntro title="Wallets & payments" body="Stablecoin wallet payments with on-chain confirmation and internal reconciliation." /><section className="two-grid"><Panel title="Business wallet" status={wallet?.status}><Detail label="Owner" value={wallet?.owner} /><Detail label="Type" value={wallet?.type} /><Detail label="Network" value={wallet?.network} /><Detail label="Stablecoin balance" value={`${fmt(wallet?.stablecoinBalance || 0)} ${wallet?.asset || ''}`} /><code>{wallet?.address}</code><button className="btn full" onClick={app.fundEscrow}>Fund escrow</button></Panel><Panel title="Payment intent flow"><Stepper steps={[['Approve stablecoin', 'Ready'], ['Fund Smart LC escrow', state.escrows[0]?.status || 'Pending'], ['Wait for confirmations', `${state.paymentIntents[0]?.confirmations || 0}/${state.paymentIntents[0]?.requiredConfirmations || 3}`], ['Escrow marked funded', state.escrows[0]?.status || 'Pending']]} /></Panel></section><TablePanel title="Payment intents" action={<button className="btn secondary small" onClick={app.createPaymentIntent}>Create payment intent</button>} headers={['ID', 'Type', 'Payer', 'Payee', 'Amount', 'Status', 'Tx', 'Confirmations']} rows={state.paymentIntents.map((p) => [p.id, p.type, p.payer, p.payee, `${fmt(p.amount)} ${p.asset}`, p.status, p.tx, `${p.confirmations}/${p.requiredConfirmations}`])} /></div>;
}

function Ledger({ state, app }: { state: AppState; app: ReturnType<typeof useCredaraApp> }) {
  const confirmed = state.ledger.filter((r) => r.status === 'Confirmed').length;
  return <div className="page-stack"><PageIntro title="Settlement Ledger" body="Confirmed, pending and fallback settlement receipts across Credara roles." /><section className="metric-grid"><Metric label="Rows" value={state.ledger.length} helper="visible ledger entries" /><Metric label="Confirmed" value={confirmed} helper="validated receipts" /><Metric label="Pending" value={state.ledger.length - confirmed} helper="not fully confirmed" /><Metric label="Spend" value={fmt(state.ledger.reduce((s, r) => s + r.amount, 0))} helper="MockUSDC rows" /></section><TablePanel title="Settlement Ledger" action={<button className="btn secondary small" onClick={app.refreshLedger}>Sync backend</button>} headers={['Time', 'Track', 'Event', 'Source', 'Amount', 'Status', 'Verifier']} rows={state.ledger.map((r) => [r.time, r.track, `${r.event} — ${r.description}`, r.source, fmt(r.amount), r.status, r.verifier])} /></div>;
}

function Settlement({ state, app }: { state: AppState; app: ReturnType<typeof useCredaraApp> }) {
  const escrow = state.escrows[0];
  return <div className="page-stack"><PageIntro title="Smart LC Settlement" body="Escrow funding, release conditions and settlement controls." /><section className="two-grid"><Panel title="Escrow account" status={escrow?.status}><Detail label="Smart LC" value={escrow?.smartLcId} /><Detail label="Contract" value={escrow?.contract} /><Detail label="Asset" value={escrow?.asset} /><Detail label="Required" value={fmt(escrow?.requiredAmount || 0)} /><Detail label="Funded" value={fmt(escrow?.fundedAmount || 0)} /><Detail label="Release condition" value={escrow?.releaseCondition} /></Panel><Panel title="Settlement controls"><Stepper steps={[['Invoice confirmed', 'Pass'], ['Delivery verified', 'Pass'], ['No open dispute', 'Pass'], ['Proof anchored', 'Pass'], ['Escrow funded', escrow?.status || 'Pending']]} /><button className="btn full" onClick={app.releaseEscrow}>Release payment</button></Panel></section></div>;
}

function Reconciliation({ state, app }: { state: AppState; app: ReturnType<typeof useCredaraApp> }) {
  const r = state.reconciliation;
  return <div className="page-stack"><PageIntro title="Reconciliation" body="Validate expected value against chain amount, internal ledger and Smart LC state." /><section className="metric-grid"><Metric label="Expected" value={fmt(r.expected)} helper="payment target" /><Metric label="On-chain" value={fmt(r.onChain)} helper="confirmed amount" /><Metric label="Ledger" value={fmt(r.ledger)} helper="internal amount" /><Metric label="Variance" value={fmt(r.variance)} helper={r.decision} /></section><Panel title="Reconciliation controls" action={<button className="btn small" onClick={app.reconcile}>Run reconciliation</button>}><Detail label="Smart LC state" value={r.smartLcState} /><Detail label="Last checked" value={r.lastChecked} /><Detail label="Decision" value={r.decision} /></Panel></div>;
}

function Settings({ state, app }: { state: AppState; app: ReturnType<typeof useCredaraApp> }) {
  return <div className="page-stack"><PageIntro title="Settings" body="Profile, workspace, security, developer API and webhook settings." /><section className="two-grid"><Panel title="Profile"><Detail label="Name" value={state.settings.profile.name as string} /><Detail label="Email" value={state.settings.profile.email as string} /><Detail label="Language" value={state.settings.profile.language as string} /><Detail label="Timezone" value={state.settings.profile.timezone as string} /></Panel><Panel title="Developer"><Detail label="API key" value={state.settings.developer.apiKey} /><Detail label="Mode" value={state.settings.developer.mode} /><Detail label="Webhook endpoint" value={state.settings.developer.webhook} /><Detail label="Subscribed events" value={state.settings.developer.events} /><button className="btn full" onClick={app.createApiKey}>Generate / rotate key</button></Panel></section></div>;
}

function ApiExplorer({ state, app }: { state: AppState; app: ReturnType<typeof useCredaraApp> }) {
  const sample = `POST /api/v1/real/payment-intents\nAuthorization: Bearer <token>\n\n{\n  "workspace_id": "${state.workspaceId || '<workspace>'}",\n  "intent_type": "Smart LC escrow funding",\n  "amount": 24500\n}`;
  return <div className="page-stack"><PageIntro title="API Explorer" body="Gateway endpoints, workspace keys, webhooks and sample calls." /><section className="two-grid"><Panel title="Getting started"><Detail label="Base URL" value="/api/v1" /><Detail label="Live workflow API" value="/api/v1/real" /><Detail label="Authentication" value="JWT Bearer token" /><button className="btn" onClick={app.createApiKey}>Create API key</button></Panel><Panel title="Sample request"><pre>{sample}</pre></Panel></section><TablePanel title="Available endpoints" headers={['Method', 'Path', 'Use']} rows={[['POST', '/auth/register', 'Create user'], ['POST', '/real/onboarding/start', 'Create workspace'], ['POST', '/real/payment-intents', 'Create payment intent'], ['GET', '/real/ledger', 'Read settlement ledger'], ['POST', '/real/reconciliation/{type}/{id}', 'Run reconciliation']]} /></div>;
}

function RecordDetail({ page, switchPage }: { page: PageKey; switchPage: (page: PageKey) => void }) {
  const isInvoice = page === 'invoiceDetail';
  return <div className="page-stack"><section className="record-hero"><small>{isInvoice ? 'Invoice' : 'Trade Contract'}</small><h3>{isInvoice ? 'INV-2025-045 · Global Retail Ltd · £24,500' : 'TC-2026-0012 · Textile supply · £24,500'}</h3><p>{isInvoice ? 'Payment claim linked to buyer confirmation, delivery proof, finance readiness and settlement.' : 'Commercial terms, parties, delivery proof, financing and Smart LC settlement in one record.'}</p><div className="record-actions"><button className="btn" onClick={() => switchPage(isInvoice ? 'contractDetail' : 'invoiceDetail')}>{isInvoice ? 'Open linked contract' : 'Open linked invoice'}</button><button className="btn secondary" onClick={() => switchPage('evidence')}>Evidence bundle</button></div></section><section className="two-grid"><Panel title={isInvoice ? 'Invoice summary' : 'Contract summary'}><Detail label="Buyer" value="Global Retail Ltd" /><Detail label="Seller" value="Acme Textiles Ltd" /><Detail label="Amount" value={fmt(24500)} /><Detail label="Status" value={isInvoice ? 'Buyer Confirmed' : 'Active'} /></Panel><Panel title="Proof and settlement"><Detail label="Proof" value="Anchored" /><Detail label="Receivable" value="REC-045" /><Detail label="Smart LC" value="LC-015" /><Detail label="Network" value="Polygon Amoy" /></Panel></section></div>;
}

function SetupPage({ page, state, switchPage }: { page: PageKey; state: AppState; switchPage: (page: PageKey) => void }) {
  if (page === 'invitations') return <TablePanel title="Invitations" headers={['Type', 'From', 'To', 'Target', 'Status']} rows={state.invitations.map((i) => [i.type, i.from, i.to, i.target, i.status])} />;
  if (page === 'members') return <TablePanel title="Members" headers={['Name', 'Email', 'Role', 'Status']} rows={state.members.map((m) => [m.name, m.email, m.role, m.status])} />;
  if (page === 'businessProfile') return <div className="page-stack"><PageIntro title="Business Profile" body="Legal identity, workspace role and operating region." /><Panel title="Business"><Detail label="Workspace" value={state.settings.workspace.name as string} /><Detail label="Role" value={state.settings.workspace.role as string} /><Detail label="Environment" value={state.settings.workspace.environment as string} /><Detail label="Region" value={state.settings.workspace.region as string} /></Panel></div>;
  return <div className="page-stack"><PageIntro title="Onboarding" body="Bring a business into Credara through identity, business profile, KYB, wallet and first workflow." /><section className="metric-grid"><Metric label="Setup" value={state.workspaceId ? 'Live' : 'Pending'} helper="workspace" /><Metric label="KYB" value="Pending" helper="business verification" /><Metric label="Wallet" value={state.wallets[0]?.status || 'Pending'} helper="settlement" /><Metric label="First workflow" value="Contract" helper="recommended" /></section><Panel title="Onboarding paths"><ActionRows rows={[['Self-signup', 'Create profile, KYB and wallet', 'businessProfile'], ['Invitation', 'Join from contract, invoice or deal room', 'invitations'], ['API onboarding', 'Generate keys and webhooks', 'apiExplorer']]} switchPage={switchPage} /></Panel></div>;
}

function TrustPage({ page, state }: { page: PageKey; state: AppState }) {
  const rows = page === 'proof' ? state.ledger.map((r) => [r.event, r.reference, r.status, r.verifier]) : [['Invoice PDF', 'Included', 'INV-2025-045', 'Anchored'], ['Delivery proof', 'Included', 'DXB-JEA-8831', 'Verified'], ['KYB report', 'Included', 'Acme Textiles Ltd', 'Pending review']];
  return <div className="page-stack"><PageIntro title={pageTitles[page][0]} body={pageTitles[page][1]} /><TablePanel title={pageTitles[page][0]} headers={page === 'proof' ? ['Event', 'Reference', 'Status', 'Verifier'] : ['Evidence', 'State', 'Reference', 'Proof']} rows={rows} /></div>;
}

function NetworkPage({ page }: { page: PageKey; state: AppState }) {
  const title = pageTitles[page][0];
  const rows = [['Acme Textiles Ltd', 'Seller', 'Textiles', 'AE', 'Active'], ['Global Retail Ltd', 'Buyer', 'Retail', 'GB', 'Verified'], ['Credara Capital', 'Financier', 'Trade Finance', 'AE', 'Listed']];
  return <div className="page-stack"><PageIntro title={title} body={pageTitles[page][1]} /><TablePanel title={title} headers={['Name', 'Role', 'Sector', 'Country', 'Status']} rows={rows} /></div>;
}

function OperationalPage({ page, state, switchPage }: { page: PageKey; state: AppState; switchPage: (page: PageKey) => void }) {
  const title = pageTitles[page][0];
  const rows = page === 'permissions' ? [['create_invoice', 'SME/Admin', 'Developer API'], ['verify_delivery', 'Buyer/Admin', 'Auditor view'], ['release_settlement', 'Buyer/Admin', 'Ledger proof']] : [['Action required', title, 'Open', 'Ready'], ['Review record', state.settings.workspace.name as string, 'Pending', 'Workspace']];
  return <div className="page-stack"><PageIntro title={title} body={pageTitles[page][1]} /><TablePanel title={title} headers={['Item', 'Scope', 'State', 'Status']} rows={rows} /><Panel title="Related workflow"><ActionRows rows={[['Contract', 'Open trade contract', 'contractDetail'], ['Ledger', 'Inspect settlement ledger', 'settlementLedger'], ['Evidence', 'Review proof bundle', 'evidence']]} switchPage={switchPage} /></Panel></div>;
}

function getMetrics(state: AppState) {
  const confirmed = state.ledger.filter((r) => r.status === 'Confirmed');
  const activeEscrows = state.escrows.filter((e) => !['Released', 'Refunded'].includes(e.status));
  const trust = Math.min(100, 62 + confirmed.length * 4 + state.escrows.filter((e) => e.status === 'Released').length * 5);
  return { verifiedCount: 1, verifiedValue: 24500, recCount: 1, recVal: 24500, activeCount: activeEscrows.length, activeVal: activeEscrows.reduce((sum, e) => sum + e.fundedAmount, 0), trust };
}

function Banner() {
  return <div className="soft-banner"><div className="mark">UAE</div><div><strong>Polygon-powered SME trade finance</strong><span>Tokenized receivables, smart contract LCs, on-chain trade credit scoring and stablecoin settlement readiness.</span></div></div>;
}

function PageIntro({ title, body }: { title: string; body: string }) {
  return <section className="page-intro"><p className="eyebrow">Credara workflow</p><h2>{title}</h2><p>{body}</p></section>;
}

function Metric({ label, value, helper }: { label: string; value: string | number; helper: string }) {
  return <div className="metric-card"><span>{label}</span><strong>{value}</strong><small>{helper}</small></div>;
}

function Panel({ title, children, action, status }: { title: string; children: ReactNode; action?: ReactNode; status?: string }) {
  return <section className="panel"><div className="panel-head"><h3>{title}</h3><div>{status && <Pill>{status}</Pill>}{action}</div></div><div className="panel-body">{children}</div></section>;
}

function Detail({ label, value }: { label: string; value?: string | number | boolean }) {
  return <div className="detail-row"><span>{label}</span><strong>{String(value ?? '-')}</strong></div>;
}

function Stepper({ steps }: { steps: Array<[string, string]> }) {
  return <div className="stepper">{steps.map(([label, status], index) => <div className="step" key={label}><div className="step-num">{index + 1}</div><div><strong>{label}</strong><span>{status}</span></div><Pill>{status}</Pill></div>)}</div>;
}

function TablePanel({ title, headers, rows, action }: { title: string; headers: string[]; rows: Array<Array<string | number>>; action?: ReactNode }) {
  return <section className="table-panel"><div className="panel-head"><h3>{title}</h3>{action}</div><div className="table-wrap"><table><thead><tr>{headers.map((h) => <th key={h}>{h}</th>)}</tr></thead><tbody>{rows.map((row, index) => <tr key={index}>{row.map((cell, i) => <td key={i}>{i === row.length - 1 && typeof cell === 'string' ? <Pill>{cell}</Pill> : String(cell)}</td>)}</tr>)}</tbody></table></div></section>;
}

function ActionRows({ rows, switchPage }: { rows: Array<[string, string, PageKey]>; switchPage: (page: PageKey) => void }) {
  return <div className="action-list">{rows.map(([title, helper, page]) => <div className="action-row" key={title}><div><strong>{title}</strong><span>{helper}</span></div><button className="btn secondary small" onClick={() => switchPage(page)}>Open</button></div>)}</div>;
}

function toastView(toast: { title: string; message?: string } | null) {
  if (!toast) return null;
  return <div className="toast"><strong>{toast.title}</strong>{toast.message && <span>{toast.message}</span>}</div>;
}
