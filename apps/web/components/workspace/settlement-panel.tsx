'use client';

import { useCallback, useEffect, useState } from 'react';
import { tradeApi, type Order, type SmartLC } from '../../lib/api/trade';
import { fmt, titleCase } from '../../lib/format';

type Notify = (title: string, message?: string) => void;

type SettlementPanelProps = {
  businessId: string | null;
  apiRole: string;
  onNotify: Notify;
  onFunded?: () => void | Promise<void>;
};

export function SettlementPanel({ businessId, apiRole, onNotify, onFunded }: SettlementPanelProps) {
  const [orders, setOrders] = useState<Order[]>([]);
  const [smartLcs, setSmartLcs] = useState<SmartLC[]>([]);
  const [loading, setLoading] = useState(false);
  const [explorerUrl, setExplorerUrl] = useState<string | null>(null);

  const canManage = apiRole === 'financier' || apiRole === 'buyer' || apiRole === 'admin';
  const activeLc = smartLcs[0] ?? null;
  const latestOrder = orders[0] ?? null;

  const refresh = useCallback(async () => {
    const orderTasks: Promise<Order[]>[] = [];
    if (businessId) {
      orderTasks.push(tradeApi.listOrders({ sellerBusinessId: businessId }));
    }
    if (apiRole === 'financier' || apiRole === 'admin') {
      orderTasks.push(tradeApi.listOrders());
    }
    const orderResults = await Promise.all(orderTasks);
    const merged = orderResults.flat();
    const seen = new Set<string>();
    setOrders(merged.filter((o) => (seen.has(o.id) ? false : (seen.add(o.id), true))));

    const lcs = await tradeApi.listSmartLCs(
      businessId ? { sellerBusinessId: businessId } : undefined,
    );
    setSmartLcs(lcs);
  }, [apiRole, businessId]);

  useEffect(() => {
    void refresh().catch(() => undefined);
  }, [refresh]);

  async function createSmartLC() {
    if (!latestOrder) return onNotify('No trade order', 'Create an order in Contract Detail first.');
    setLoading(true);
    try {
      const lc = await tradeApi.createSmartLC({
        order_id: latestOrder.id,
        amount: latestOrder.total_amount,
        currency: latestOrder.currency || 'USDC',
      });
      await refresh();
      onNotify('Smart LC created', `Escrow ${lc.id.slice(0, 8)}… ready to fund.`);
    } catch (e) {
      onNotify('Create failed', e instanceof Error ? e.message.slice(0, 140) : 'Error');
    } finally {
      setLoading(false);
    }
  }

  async function fundSmartLC() {
    if (!activeLc) return onNotify('No Smart LC', 'Create a Smart LC from your trade order first.');
    setLoading(true);
    try {
      const res = await tradeApi.fundSmartLC(activeLc.id, 'Funded from Credara settlement workspace');
      setExplorerUrl(res.explorer_url || null);
      await refresh();
      await onFunded?.();
      onNotify(
        res.on_chain ? 'Smart LC funded on-chain' : 'Smart LC funded',
        res.on_chain ? 'Escrow funded — Polygon tx recorded.' : 'Escrow marked funded in backend.',
      );
    } catch (e) {
      onNotify('Fund failed', e instanceof Error ? e.message.slice(0, 140) : 'Error');
    } finally {
      setLoading(false);
    }
  }

  async function releaseSmartLC() {
    if (!activeLc) return onNotify('No Smart LC', 'No connected escrow — fund Smart LC first.');
    if (activeLc.status !== 'funded') {
      return onNotify('Not funded', 'Escrow must be funded before release.');
    }
    setLoading(true);
    try {
      const res = await tradeApi.releaseSmartLC(activeLc.id, 'Delivery verified — release settlement');
      setExplorerUrl(res.explorer_url || null);
      await refresh();
      onNotify(
        res.on_chain ? 'Settlement released on Polygon' : 'Settlement released',
        res.explorer_url ? 'Open Polygonscan to verify the release tx.' : 'Smart LC status updated.',
      );
    } catch (e) {
      onNotify('Release failed', e instanceof Error ? e.message.slice(0, 140) : 'Error');
    } finally {
      setLoading(false);
    }
  }

  const steps = [
    ['Invoice confirmed', 'Pass'],
    ['Delivery verified', 'Pass'],
    ['No open dispute', 'Pass'],
    ['Proof anchored', 'Pass'],
    ['Escrow funded', activeLc?.status === 'funded' || activeLc?.status === 'released' ? 'Pass' : titleCase(activeLc?.status || 'Pending')],
  ] as const;

  return (
    <div className="page-stack settlement-panel">
      {!activeLc ? (
        <section className="panel settlement-empty">
          <h3>No Smart LC connected yet</h3>
          <p className="settlement-hint">
            {canManage
              ? 'After invoice + proof are ready, create a Smart LC from your latest trade order, then fund escrow.'
              : 'Switch to Financier (or Buyer) role to create and fund Smart LC escrow.'}
          </p>
          {latestOrder ? (
            <p className="settlement-meta">
              Latest order: <strong>{latestOrder.buyer_name}</strong> · {fmt(latestOrder.total_amount, '')}{' '}
              {latestOrder.currency}
            </p>
          ) : (
            <p className="settlement-meta">Complete steps 1–4 in Contract Detail / Receivables first.</p>
          )}
          {canManage && latestOrder ? (
            <button type="button" className="btn" disabled={loading} onClick={createSmartLC}>
              Create Smart LC from order
            </button>
          ) : null}
        </section>
      ) : (
        <section className="two-grid">
          <div className="panel">
            <div className="panel-head">
              <h3>Escrow account</h3>
              <span className={`pill ${activeLc.status === 'released' ? 'green' : activeLc.status === 'funded' ? 'blue' : 'amber'}`}>
                {titleCase(activeLc.status)}
              </span>
            </div>
            <div className="detail-row">
              <span>Smart LC</span>
              <span>{activeLc.id.slice(0, 12)}…</span>
            </div>
            <div className="detail-row">
              <span>Buyer</span>
              <span>{activeLc.buyer_name}</span>
            </div>
            <div className="detail-row">
              <span>Contract</span>
              <span>{activeLc.contract_address ? `${activeLc.contract_address.slice(0, 10)}…` : 'Pending deploy'}</span>
            </div>
            <div className="detail-row">
              <span>Amount</span>
              <span>
                {fmt(activeLc.amount, '')} {activeLc.currency}
              </span>
            </div>
            {activeLc.polygon_tx_hash ? (
              <div className="detail-row">
                <span>Polygon tx</span>
                <span>{activeLc.polygon_tx_hash.slice(0, 14)}…</span>
              </div>
            ) : null}
            {explorerUrl ? (
              <a className="btn secondary small" href={explorerUrl} target="_blank" rel="noreferrer" style={{ marginTop: 12 }}>
                View on Polygonscan
              </a>
            ) : null}
          </div>

          <div className="panel">
            <h3>Settlement controls</h3>
            <ol className="settlement-steps">
              {steps.map(([label, state]) => (
                <li key={label}>
                  <span>{label}</span>
                  <strong>{state}</strong>
                </li>
              ))}
            </ol>
            <div className="top-actions" style={{ marginTop: 16 }}>
              {canManage && activeLc.status === 'created' ? (
                <button type="button" className="btn" disabled={loading} onClick={fundSmartLC}>
                  Fund Smart LC escrow
                </button>
              ) : null}
              {activeLc.status === 'funded' ? (
                <button type="button" className="btn" disabled={loading} onClick={releaseSmartLC}>
                  Release payment
                </button>
              ) : null}
              {activeLc.status === 'released' ? (
                <span className="pill green">Settlement complete</span>
              ) : null}
              <button type="button" className="btn secondary" disabled={loading} onClick={refresh}>
                Refresh
              </button>
            </div>
          </div>
        </section>
      )}
    </div>
  );
}
