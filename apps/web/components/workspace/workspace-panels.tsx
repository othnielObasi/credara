'use client';

import { useEffect, useState } from 'react';
import { enterpriseApi } from '../../lib/api/enterprise';
import { realApi } from '../../lib/api/real';
import { fmt, titleCase } from '../../lib/format';

type Notify = (title: string, message?: string) => void;

type SettingsState = {
  profile: Record<string, string | boolean>;
  workspace: Record<string, string | boolean>;
  notifications: Record<string, boolean>;
  security: Record<string, string | boolean>;
  developer: Record<string, string>;
  admin: Record<string, string | boolean>;
};

export function SettingsPanel({
  workspaceId,
  settings,
  onSaved,
  onNotify,
  onCreateApiKey,
}: {
  workspaceId: string | null;
  settings: SettingsState;
  onSaved: (patch: SettingsState) => void;
  onNotify: Notify;
  onCreateApiKey: () => void;
}) {
  const [draft, setDraft] = useState(settings);
  const [saving, setSaving] = useState(false);

  useEffect(() => setDraft(settings), [settings]);

  async function save() {
    if (!workspaceId) return onNotify('No workspace', 'Complete onboarding first.');
    setSaving(true);
    try {
      await realApi.saveSettings({
        workspace_id: workspaceId,
        profile: draft.profile,
        workspace: draft.workspace,
        notifications: draft.notifications,
        security: draft.security,
        developer: draft.developer,
        admin: draft.admin,
      });
      onSaved(draft);
      onNotify('Settings saved', 'Profile and workspace preferences updated.');
    } catch (e) {
      onNotify('Save failed', e instanceof Error ? e.message.slice(0, 120) : 'Error');
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="page-stack">
      <section className="page-intro"><p className="eyebrow">Credara workflow</p><h2>Settings</h2><p>Profile, workspace, notifications and developer API settings — persisted to the backend.</p></section>
      <section className="two-grid">
        <div className="panel">
          <h3>Profile</h3>
          <label>Name<input value={String(draft.profile.name || '')} onChange={(e) => setDraft({ ...draft, profile: { ...draft.profile, name: e.target.value } })} /></label>
          <label>Email<input value={String(draft.profile.email || '')} onChange={(e) => setDraft({ ...draft, profile: { ...draft.profile, email: e.target.value } })} /></label>
          <label>Language<input value={String(draft.profile.language || '')} onChange={(e) => setDraft({ ...draft, profile: { ...draft.profile, language: e.target.value } })} /></label>
          <label>Timezone<input value={String(draft.profile.timezone || '')} onChange={(e) => setDraft({ ...draft, profile: { ...draft.profile, timezone: e.target.value } })} /></label>
        </div>
        <div className="panel">
          <h3>Workspace</h3>
          <label>Workspace name<input value={String(draft.workspace.name || '')} onChange={(e) => setDraft({ ...draft, workspace: { ...draft.workspace, name: e.target.value } })} /></label>
          <label>Region<input value={String(draft.workspace.region || '')} onChange={(e) => setDraft({ ...draft, workspace: { ...draft.workspace, region: e.target.value } })} /></label>
          <label>Environment<input value={String(draft.workspace.environment || '')} onChange={(e) => setDraft({ ...draft, workspace: { ...draft.workspace, environment: e.target.value } })} /></label>
        </div>
      </section>
      <section className="two-grid">
        <div className="panel">
          <h3>Notifications</h3>
          {Object.entries(draft.notifications).map(([key, val]) => (
            <label key={key} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <input type="checkbox" checked={val} onChange={(e) => setDraft({ ...draft, notifications: { ...draft.notifications, [key]: e.target.checked } })} />
              {titleCase(key)}
            </label>
          ))}
        </div>
        <div className="panel">
          <h3>Developer</h3>
          <p><small>API key</small><br /><code>{draft.developer.apiKey}</code></p>
          <label>Webhook<input value={draft.developer.webhook || ''} onChange={(e) => setDraft({ ...draft, developer: { ...draft.developer, webhook: e.target.value } })} /></label>
          <label>Events<input value={draft.developer.events || ''} onChange={(e) => setDraft({ ...draft, developer: { ...draft.developer, events: e.target.value } })} /></label>
          <div className="top-actions" style={{ marginTop: 12 }}>
            <button type="button" className="btn secondary" onClick={onCreateApiKey}>Generate API key</button>
          </div>
        </div>
      </section>
      <button type="button" className="btn" disabled={saving} onClick={save}>{saving ? 'Saving…' : 'Save settings'}</button>
    </div>
  );
}

export function InvitationsPanel({
  workspaceId,
  businessName,
  invitations,
  onRefresh,
  onNotify,
}: {
  workspaceId: string | null;
  businessName: string;
  invitations: Array<Record<string, unknown>>;
  onRefresh: () => Promise<void>;
  onNotify: Notify;
}) {
  const [toEmail, setToEmail] = useState('');
  const [inviteType, setInviteType] = useState('trade_contract');
  const [role, setRole] = useState('buyer');
  const [loading, setLoading] = useState(false);

  async function sendInvite() {
    const recipient = toEmail.trim();
    if (!workspaceId || !recipient) return onNotify('Missing fields', 'Recipient email required.');
    setLoading(true);
    try {
      await realApi.createInvitation({
        from_workspace_id: workspaceId,
        from_business_name: businessName || 'Workspace',
        to_email: recipient,
        invite_type: inviteType,
        invited_role: role,
        target_type: 'workflow',
        target_id: `WF-${Date.now().toString().slice(-6)}`,
        target_route: '/contractDetail',
        message: 'Join this trade workflow on Credara',
      });
      setToEmail('');
      await onRefresh();
      onNotify('Invitation sent', `Invite queued for ${recipient}`);
    } catch (e) {
      onNotify('Failed', e instanceof Error ? e.message.slice(0, 120) : 'Error');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="page-stack">
      <section className="panel">
        <h3>Send invitation</h3>
        <div className="two-grid">
          <label>Email<input type="email" value={toEmail} onChange={(e) => setToEmail(e.target.value)} placeholder="buyer@company.example" /></label>
          <label>Role<select value={role} onChange={(e) => setRole(e.target.value)}><option value="buyer">Buyer</option><option value="financier">Financier</option><option value="sme">SME</option></select></label>
        </div>
        <label>Type<select value={inviteType} onChange={(e) => setInviteType(e.target.value)}><option value="trade_contract">Trade contract</option><option value="invoice_confirmation">Invoice confirmation</option><option value="deal_room">Deal room</option></select></label>
        <button type="button" className="btn" disabled={loading} onClick={sendInvite} style={{ marginTop: 12 }}>Send invite</button>
      </section>
      <section className="table-panel">
        <div className="panel-head"><strong>Invitations</strong><span>{invitations.length}</span></div>
        {invitations.length === 0 ? <p className="empty-state">No invitations yet.</p> : (
          <table><thead><tr><th>Type</th><th>From</th><th>To</th><th>Status</th></tr></thead><tbody>
            {invitations.map((i) => (
              <tr key={String(i.id)}>
                <td>{String(i.invite_type || i.type)}</td>
                <td>{String(i.from_business_name || i.from)}</td>
                <td>{String(i.to_email || i.to)}</td>
                <td>{titleCase(String(i.status))}</td>
              </tr>
            ))}
          </tbody></table>
        )}
      </section>
    </div>
  );
}

export function BuyerInboxPanel({ apiRole, onNotify }: { apiRole: string; onNotify: Notify }) {
  const [actions, setActions] = useState<Awaited<ReturnType<typeof enterpriseApi.listBuyerActions>>>([]);
  const [loading, setLoading] = useState(false);
  const canAct = apiRole === 'buyer' || apiRole === 'admin';

  async function refresh() {
    if (!canAct) return;
    setActions(await enterpriseApi.listBuyerActions());
  }

  useEffect(() => {
    void refresh().catch(() => undefined);
  }, [apiRole]);

  async function decide(actionId: string, decision: string) {
    setLoading(true);
    try {
      await enterpriseApi.decideBuyerAction(actionId, decision);
      await refresh();
      onNotify('Action updated', `Marked as ${decision}.`);
    } catch (e) {
      onNotify('Failed', e instanceof Error ? e.message.slice(0, 120) : 'Error');
    } finally {
      setLoading(false);
    }
  }

  if (!canAct) return <p className="empty-state">Buyer inbox requires a buyer account.</p>;

  return (
    <div className="page-stack">
      <section className="page-intro"><p className="eyebrow">Buyer workspace</p><h2>Buyer Inbox</h2><p>Invoice confirmations, delivery reviews and settlement decisions.</p></section>
      {actions.length === 0 ? <p className="empty-state">No pending buyer actions.</p> : (
        <table><thead><tr><th>Action</th><th>Description</th><th>Status</th><th /></tr></thead><tbody>
          {actions.map((a) => (
            <tr key={a.id}>
              <td>{a.title}</td>
              <td>{a.description}</td>
              <td>{titleCase(a.status)}</td>
              <td className="top-actions" style={{ gap: 6 }}>
                {a.status === 'pending' ? (
                  <>
                    <button type="button" className="btn small" disabled={loading} onClick={() => decide(a.id, 'approved')}>Approve</button>
                    <button type="button" className="btn secondary small" disabled={loading} onClick={() => decide(a.id, 'rejected')}>Reject</button>
                  </>
                ) : null}
              </td>
            </tr>
          ))}
        </tbody></table>
      )}
      <button type="button" className="btn secondary" onClick={refresh}>Refresh</button>
    </div>
  );
}

export function MarketplacePanel({ apiRole, onNotify }: { apiRole: string; onNotify: Notify }) {
  const [deals, setDeals] = useState<Awaited<ReturnType<typeof enterpriseApi.listMarketplaceDeals>>>([]);
  const [loading, setLoading] = useState(false);
  const canAct = apiRole === 'financier' || apiRole === 'admin';

  useEffect(() => {
    if (!canAct) return;
    void enterpriseApi.listMarketplaceDeals().then(setDeals).catch(() => undefined);
  }, [apiRole]);

  async function expressInterest(receivableId: string) {
    setLoading(true);
    try {
      const res = await enterpriseApi.expressInterest(receivableId);
      onNotify('Interest expressed', `Recommended advance: ${fmt(Number(res.recommended_advance || 0), '')}`);
    } catch (e) {
      onNotify('Failed', e instanceof Error ? e.message.slice(0, 120) : 'Error');
    } finally {
      setLoading(false);
    }
  }

  if (!canAct) return <p className="empty-state">Marketplace requires a financier account.</p>;

  return (
    <div className="page-stack">
      <section className="page-intro"><p className="eyebrow">Financier workspace</p><h2>Marketplace</h2><p>Verified receivables with proof bundles and risk inputs.</p></section>
      {deals.length === 0 ? <p className="empty-state">No receivables listed yet. SMEs must tokenize invoices first.</p> : (
        <table><thead><tr><th>Debtor</th><th>Face value</th><th>Advance</th><th>Proof</th><th /></tr></thead><tbody>
          {deals.map((d) => (
            <tr key={d.receivable_id}>
              <td>{d.debtor_name}</td>
              <td>{fmt(d.face_value, '')} {d.currency}</td>
              <td>{fmt(d.recommended_advance, '')}</td>
              <td>{d.polygon_tx_hash ? <span className="pill green">Anchored</span> : <span className="pill amber">Pending</span>}</td>
              <td><button type="button" className="btn small" disabled={loading} onClick={() => expressInterest(d.receivable_id)}>Express interest</button></td>
            </tr>
          ))}
        </tbody></table>
      )}
    </div>
  );
}

export function DealRoomPanel({ apiRole, onNotify }: { apiRole: string; onNotify: Notify }) {
  const [summary, setSummary] = useState<Awaited<ReturnType<typeof enterpriseApi.dealRoomSummary>> | null>(null);
  const [rows, setRows] = useState<Awaited<ReturnType<typeof enterpriseApi.dealRoomReceivables>>>([]);
  const [loading, setLoading] = useState(false);
  const canAct = apiRole === 'financier' || apiRole === 'admin';

  useEffect(() => {
    if (!canAct) return;
    void Promise.all([enterpriseApi.dealRoomSummary(), enterpriseApi.dealRoomReceivables()]).then(([s, r]) => {
      setSummary(s);
      setRows(r);
    }).catch(() => undefined);
  }, [apiRole]);

  async function makeOffer(receivableId: string) {
    setLoading(true);
    try {
      await enterpriseApi.createDealOffer(receivableId);
      onNotify('Offer created', 'Financing offer submitted to deal room.');
    } catch (e) {
      onNotify('Failed', e instanceof Error ? e.message.slice(0, 120) : 'Error');
    } finally {
      setLoading(false);
    }
  }

  if (!canAct) return <p className="empty-state">Deal room requires a financier account.</p>;

  return (
    <div className="page-stack">
      <section className="page-intro"><p className="eyebrow">Financier workspace</p><h2>Deal Room</h2><p>Review receivable evidence and submit financing offers.</p></section>
      {summary && (
        <section className="metric-grid">
          <div className="metric-card"><span>Receivables</span><strong>{summary.receivable_count}</strong></div>
          <div className="metric-card"><span>Face value</span><strong>{fmt(summary.total_face_value, '')}</strong></div>
          <div className="metric-card"><span>Recommended advance</span><strong>{fmt(summary.recommended_advance, '')}</strong></div>
          <div className="metric-card"><span>Risk band</span><strong>{titleCase(summary.risk_band)}</strong></div>
        </section>
      )}
      {rows.length === 0 ? <p className="empty-state">No deals in the room yet.</p> : (
        <table><thead><tr><th>Debtor</th><th>Face value</th><th>Buyer confirmed</th><th /></tr></thead><tbody>
          {rows.map((row) => (
            <tr key={String(row.receivable?.id)}>
              <td>{String(row.receivable?.debtor_name || row.risk_inputs?.debtor_name || '—')}</td>
              <td>{fmt(Number(row.receivable?.face_value || 0), '')}</td>
              <td>{row.risk_inputs?.buyer_confirmed ? 'Yes' : 'No'}</td>
              <td><button type="button" className="btn small" disabled={loading} onClick={() => makeOffer(String(row.receivable?.id))}>Make offer</button></td>
            </tr>
          ))}
        </tbody></table>
      )}
    </div>
  );
}
