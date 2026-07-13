'use client';

import { useCallback, useEffect, useState } from 'react';
import { proofApi } from '../../lib/api/proof';
import { tradeApi, type DeliveryProof, type Invoice, type Order, type Receivable } from '../../lib/api/trade';
import { fmt, titleCase } from '../../lib/format';

type Role = 'sme' | 'buyer' | 'financier' | 'admin' | 'developer';

type Props = {
  businessId: string | null;
  businessName: string;
  apiRole: Role;
  onNotify: (title: string, message?: string) => void;
};

export function TradeWorkflowPanel({ businessId, businessName, apiRole, onNotify }: Props) {
  const [orders, setOrders] = useState<Order[]>([]);
  const [buyerOrders, setBuyerOrders] = useState<Order[]>([]);
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [receivables, setReceivables] = useState<Receivable[]>([]);
  const [proofs, setProofs] = useState<DeliveryProof[]>([]);
  const [anchorUrl, setAnchorUrl] = useState<string | null>(null);
  const [anchorOnChain, setAnchorOnChain] = useState<boolean | null>(null);
  const [buyerName, setBuyerName] = useState('');
  const [description, setDescription] = useState('');
  const [amount, setAmount] = useState('24500');
  const [loading, setLoading] = useState(false);

  const isSme = apiRole === 'sme' || apiRole === 'admin';
  const isBuyer = apiRole === 'buyer' || apiRole === 'admin';

  const refresh = useCallback(async () => {
    const tasks: Promise<void>[] = [];
    if (businessId && isSme) {
      tasks.push(
        tradeApi.listOrders({ sellerBusinessId: businessId }).then(setOrders),
        tradeApi.listInvoices({ sellerBusinessId: businessId }).then(setInvoices),
        tradeApi.listReceivables(businessId).then(setReceivables),
      );
    }
    if (isBuyer && businessId) {
      tasks.push(
        tradeApi.listOrders({ pendingBuyer: true }).then(setBuyerOrders),
        tradeApi.listOrders({ buyerBusinessId: businessId }).then((claimed) => {
          setBuyerOrders((prev) => {
            const ids = new Set(prev.map((o) => o.id));
            return [...prev, ...claimed.filter((o) => !ids.has(o.id))];
          });
        }),
        tradeApi.listInvoices({ buyerBusinessId: businessId }).then((buyerInvoices) => {
          if (isSme) {
            setInvoices((prev) => {
              const ids = new Set(prev.map((i) => i.id));
              return [...prev, ...buyerInvoices.filter((i) => !ids.has(i.id))];
            });
          } else {
            setInvoices(buyerInvoices);
          }
        }),
      );
    }
    await Promise.all(tasks);
    if (orders[0]?.id) {
      const dp = await tradeApi.listDeliveryProofs(orders[0].id).catch(() => []);
      setProofs(dp);
    }
  }, [businessId, isBuyer, isSme, orders]);

  useEffect(() => {
    void refresh().catch(() => undefined);
  }, [businessId, apiRole]);

  async function createOrder() {
    if (!businessId) return onNotify('Complete onboarding', 'A business profile is required.');
    if (!buyerName.trim() || !description.trim()) return onNotify('Missing fields', 'Buyer and description required.');
    setLoading(true);
    try {
      await tradeApi.createOrder({
        seller_business_id: businessId,
        buyer_name: buyerName.trim(),
        description: description.trim(),
        total_amount: Number(amount),
        currency: 'USDC',
      });
      setBuyerName('');
      setDescription('');
      await refresh();
      onNotify('Order created', 'Trade order saved. Buyer must confirm the order next.');
    } catch (e) {
      onNotify('Failed', e instanceof Error ? e.message.slice(0, 120) : 'Error');
    } finally {
      setLoading(false);
    }
  }

  async function confirmOrder(order: Order) {
    if (!businessId) return onNotify('Business required', 'Buyer business profile required.');
    setLoading(true);
    try {
      await tradeApi.confirmOrder(order.id, businessId);
      await refresh();
      onNotify('Order confirmed', 'Buyer bound to trade order.');
    } catch (e) {
      onNotify('Failed', e instanceof Error ? e.message.slice(0, 120) : 'Error');
    } finally {
      setLoading(false);
    }
  }

  async function issueInvoice(order: Order) {
    setLoading(true);
    try {
      const due = new Date();
      due.setDate(due.getDate() + 45);
      await tradeApi.createInvoice({
        order_id: order.id,
        invoice_number: `INV-${Date.now().toString().slice(-6)}`,
        amount: order.total_amount,
        due_date: due.toISOString(),
      });
      await refresh();
      onNotify('Invoice issued', `Invoice for ${order.buyer_name}.`);
    } catch (e) {
      onNotify('Failed', e instanceof Error ? e.message.slice(0, 120) : 'Error');
    } finally {
      setLoading(false);
    }
  }

  async function buyerConfirmInvoice(invoice: Invoice) {
    if (!businessId) return onNotify('Business required', 'Buyer business profile required.');
    setLoading(true);
    try {
      await tradeApi.buyerConfirmInvoice(invoice.id, businessId);
      await refresh();
      onNotify('Invoice confirmed', 'Buyer obligation confirmed on backend.');
    } catch (e) {
      onNotify('Failed', e instanceof Error ? e.message.slice(0, 120) : 'Error');
    } finally {
      setLoading(false);
    }
  }

  async function submitDelivery(order: Order) {
    setLoading(true);
    try {
      await tradeApi.submitDeliveryProof({
        order_id: order.id,
        evidence_uri: `s3://credara/delivery/${order.id}.pdf`,
        otp_code: '883142',
        gps_lat: '25.0657',
        gps_lng: '55.1713',
        metadata_json: { buyer_confirmed: true, logistics_tracking_status: 'delivered', corridor: 'Jebel Ali' },
      });
      await refresh();
      onNotify('Delivery proof submitted', 'Evidence scored and order marked delivered.');
    } catch (e) {
      onNotify('Failed', e instanceof Error ? e.message.slice(0, 120) : 'Error');
    } finally {
      setLoading(false);
    }
  }

  async function tokenizeReceivable(invoice: Invoice) {
    setLoading(true);
    try {
      await tradeApi.createReceivable(invoice.id);
      await refresh();
      onNotify('Receivable created', 'Tokenization-ready asset created from confirmed invoice.');
    } catch (e) {
      onNotify('Failed', e instanceof Error ? e.message.slice(0, 120) : 'Error');
    } finally {
      setLoading(false);
    }
  }

  async function anchorOnPolygon(invoice?: Invoice) {
    setLoading(true);
    try {
      const result = await proofApi.anchor({
        invoice_id: invoice?.id,
        business_id: businessId || undefined,
      });
      setAnchorUrl(result.explorer_url || null);
      setAnchorOnChain(Boolean(result.on_chain));
      onNotify(
        result.on_chain ? 'Anchored on Polygon Amoy' : 'Simulated proof receipt',
        result.on_chain
          ? (result.explorer_url || result.polygon_tx_hash || 'On-chain')
          : 'Not broadcast — configure Amoy relayer for Polygonscan',
      );
    } catch (e) {
      onNotify('Anchor failed', e instanceof Error ? e.message.slice(0, 120) : 'Error');
    } finally {
      setLoading(false);
    }
  }

  const confirmedInvoices = invoices.filter((i) => i.status === 'buyer_confirmed');

  return (
    <div className="page-stack">
      <section className="soft-banner">
        <div className="mark">Flow</div>
        <div>
          <strong>Trade → confirm → invoice → delivery → receivable → Polygon</strong>
          <span>Signed in as {titleCase(apiRole)}. Buyer steps require a buyer account JWT.</span>
        </div>
      </section>

      {anchorOnChain !== null && (
        <section className="panel">
          <strong>Credara proof receipt · Polygon Amoy</strong>
          <p style={{ color: 'var(--muted)', margin: '8px 0' }}>
            {anchorOnChain
              ? 'Live transaction anchored by Credara'
              : 'Simulated receipt only — not broadcast on Polygon. Configure RELAYER_PRIVATE_KEY + PROOF_REGISTRY_ADDRESS for a live Amoy tx.'}
          </p>
          {anchorOnChain && anchorUrl ? (
            <a className="btn secondary" href={anchorUrl} target="_blank" rel="noreferrer">View on Polygonscan</a>
          ) : (
            <span className="pill amber">Simulated</span>
          )}
        </section>
      )}

      {isSme && (
        <section className="panel">
          <h3>1 · Create trade order (SME)</h3>
          <p style={{ color: 'var(--muted)' }}>Seller: {businessName || 'Your business'}</p>
          <div className="two-grid" style={{ marginTop: 16 }}>
            <label>Buyer<input value={buyerName} onChange={(e) => setBuyerName(e.target.value)} placeholder="Global Retail Ltd" /></label>
            <label>Amount (USDC)<input value={amount} onChange={(e) => setAmount(e.target.value)} /></label>
          </div>
          <label style={{ display: 'grid', gap: 8, marginTop: 12 }}>Description<textarea value={description} onChange={(e) => setDescription(e.target.value)} rows={2} /></label>
          <div className="top-actions" style={{ marginTop: 16 }}>
            <button type="button" className="btn" disabled={loading || !businessId} onClick={createOrder}>Create order</button>
          </div>
        </section>
      )}

      {isBuyer && (
        <section className="panel">
          <h3>2 · Confirm order (Buyer)</h3>
          {buyerOrders.length === 0 ? (
            <p className="empty-state">No orders awaiting buyer confirmation.</p>
          ) : (
            <div className="table-wrap"><table><thead><tr><th>Buyer</th><th>Amount</th><th>Status</th><th /></tr></thead><tbody>
              {buyerOrders.map((o) => (
                <tr key={o.id}>
                  <td>{o.buyer_name}</td>
                  <td>{fmt(o.total_amount, '')} {o.currency}</td>
                  <td>{titleCase(o.status)}</td>
                  <td>
                    {!o.buyer_business_id ? (
                      <button type="button" className="btn secondary small" disabled={loading} onClick={() => confirmOrder(o)}>Confirm</button>
                    ) : (
                      <span className="pill green">Bound</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody></table></div>
          )}
        </section>
      )}

      {isSme && (
        <section className="two-grid">
          <div className="table-panel">
            <div className="panel-head"><strong>Orders</strong><span>{orders.length}</span></div>
            {orders.length === 0 ? <p className="empty-state">No orders yet.</p> : (
              <div className="table-wrap"><table><thead><tr><th>Buyer</th><th>Amount</th><th>Status</th><th /></tr></thead><tbody>
                {orders.map((o) => (
                  <tr key={o.id}>
                    <td>{o.buyer_name}</td>
                    <td>{fmt(o.total_amount, '')}</td>
                    <td>{titleCase(o.status)}</td>
                    <td className="top-actions" style={{ gap: 6 }}>
                      <button type="button" className="btn secondary small" disabled={loading} onClick={() => issueInvoice(o)}>Invoice</button>
                      <button type="button" className="btn secondary small" disabled={loading} onClick={() => submitDelivery(o)}>Delivery</button>
                    </td>
                  </tr>
                ))}
              </tbody></table></div>
            )}
          </div>
          <div className="table-panel">
            <div className="panel-head"><strong>Invoices</strong><span>{invoices.length}</span></div>
            {invoices.length === 0 ? <p className="empty-state">Issue an invoice from an order.</p> : (
              <div className="table-wrap"><table><thead><tr><th>Number</th><th>Amount</th><th>Status</th><th /></tr></thead><tbody>
                {invoices.map((i) => (
                  <tr key={i.id}>
                    <td>{i.invoice_number}</td>
                    <td>{fmt(i.amount, '')}</td>
                    <td>{titleCase(i.status)}</td>
                    <td className="top-actions" style={{ gap: 6 }}>
                      {i.status === 'buyer_confirmed' ? (
                        <button type="button" className="btn secondary small" disabled={loading} onClick={() => tokenizeReceivable(i)}>Receivable</button>
                      ) : null}
                      <button type="button" className="btn secondary small" disabled={loading} onClick={() => anchorOnPolygon(i)}>Anchor</button>
                    </td>
                  </tr>
                ))}
              </tbody></table></div>
            )}
          </div>
        </section>
      )}

      {isBuyer && invoices.length > 0 && (
        <section className="panel">
          <h3>3 · Confirm invoice (Buyer)</h3>
          <div className="table-wrap"><table><thead><tr><th>Number</th><th>Amount</th><th>Status</th><th /></tr></thead><tbody>
            {invoices.map((i) => (
              <tr key={i.id}>
                <td>{i.invoice_number}</td>
                <td>{fmt(i.amount, '')}</td>
                <td>{titleCase(i.status)}</td>
                <td>
                  {i.status !== 'buyer_confirmed' ? (
                    <button type="button" className="btn small" disabled={loading} onClick={() => buyerConfirmInvoice(i)}>Confirm</button>
                  ) : (
                    <span className="pill green">Confirmed</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody></table></div>
        </section>
      )}

      <section className="two-grid">
        <div className="table-panel">
          <div className="panel-head"><strong>Delivery proofs</strong><span>{proofs.length}</span></div>
          {proofs.length === 0 ? <p className="empty-state">Submit delivery proof from an order.</p> : (
            <div className="table-wrap"><table><thead><tr><th>Order</th><th>Score</th><th>Status</th></tr></thead><tbody>
              {proofs.map((p) => <tr key={p.id}><td>{p.order_id.slice(0, 8)}…</td><td>{p.confidence_score}%</td><td>{titleCase(p.status)}</td></tr>)}
            </tbody></table></div>
          )}
        </div>
        <div className="table-panel">
          <div className="panel-head"><strong>Receivables</strong><span>{receivables.length}</span></div>
          {receivables.length === 0 ? (
            <p className="empty-state">{confirmedInvoices.length ? 'Tokenize a confirmed invoice.' : 'Buyer must confirm invoice first.'}</p>
          ) : (
            <div className="table-wrap"><table><thead><tr><th>Debtor</th><th>Face value</th><th>Status</th></tr></thead><tbody>
              {receivables.map((r) => <tr key={r.id}><td>{r.debtor_name}</td><td>{fmt(r.face_value, '')}</td><td>{titleCase(r.status)}</td></tr>)}
            </tbody></table></div>
          )}
        </div>
      </section>

      <div className="top-actions">
        <button type="button" className="btn secondary" disabled={loading} onClick={refresh}>Refresh</button>
        <button type="button" className="btn" disabled={loading || !businessId} onClick={() => anchorOnPolygon()}>Anchor latest proof on Polygon</button>
      </div>
    </div>
  );
}

export function DeliveryProofPanel({ businessId, apiRole, onNotify }: Omit<Props, 'businessName'>) {
  const [orders, setOrders] = useState<Order[]>([]);
  const [proofs, setProofs] = useState<DeliveryProof[]>([]);
  const [loading, setLoading] = useState(false);
  const isSme = apiRole === 'sme' || apiRole === 'admin';

  useEffect(() => {
    if (!businessId || !isSme) return;
    void tradeApi.listOrders({ sellerBusinessId: businessId }).then(setOrders).catch(() => undefined);
  }, [businessId, isSme]);

  async function submit(order: Order) {
    setLoading(true);
    try {
      await tradeApi.submitDeliveryProof({
        order_id: order.id,
        evidence_uri: `s3://credara/delivery/${order.id}.pdf`,
        otp_code: '883142',
        gps_lat: '25.0657',
        gps_lng: '55.1713',
        metadata_json: { buyer_confirmed: true, logistics_tracking_status: 'delivered' },
      });
      const dp = await tradeApi.listDeliveryProofs(order.id);
      setProofs(dp);
      onNotify('Delivery proof submitted', `Confidence score updated for ${order.buyer_name}.`);
    } catch (e) {
      onNotify('Failed', e instanceof Error ? e.message.slice(0, 120) : 'Error');
    } finally {
      setLoading(false);
    }
  }

  if (!isSme) return <p className="empty-state">Delivery proof submission requires an SME account.</p>;

  return (
    <div className="page-stack">
      <section className="panel">
        <h3>Delivery proof</h3>
        <p style={{ color: 'var(--muted)' }}>OTP + GPS + buyer confirmation metadata for Jebel Ali corridor demo.</p>
        {orders.length === 0 ? <p className="empty-state">Create a trade order first.</p> : (
          <div className="table-wrap"><table><thead><tr><th>Buyer</th><th>Status</th><th /></tr></thead><tbody>
            {orders.map((o) => (
              <tr key={o.id}><td>{o.buyer_name}</td><td>{titleCase(o.status)}</td>
                <td><button type="button" className="btn small" disabled={loading} onClick={() => submit(o)}>Submit proof</button></td></tr>
            ))}
          </tbody></table></div>
        )}
      </section>
      {proofs.length > 0 && (
        <section className="table-panel">
          <strong>Latest proofs</strong>
          <div className="table-wrap"><table><thead><tr><th>Score</th><th>Status</th><th>Hash</th></tr></thead><tbody>
            {proofs.map((p) => <tr key={p.id}><td>{p.confidence_score}%</td><td>{titleCase(p.status)}</td><td><code>{p.proof_hash?.slice(0, 16)}…</code></td></tr>)}
          </tbody></table></div>
        </section>
      )}
    </div>
  );
}

export function ReceivablesPanel({ businessId, apiRole, onNotify }: Omit<Props, 'businessName'>) {
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [receivables, setReceivables] = useState<Receivable[]>([]);
  const [loading, setLoading] = useState(false);
  const isSme = apiRole === 'sme' || apiRole === 'admin';

  async function refresh() {
    if (!businessId) return;
    const [i, r] = await Promise.all([
      tradeApi.listInvoices({ sellerBusinessId: businessId }),
      tradeApi.listReceivables(businessId),
    ]);
    setInvoices(i);
    setReceivables(r);
  }

  useEffect(() => {
    void refresh().catch(() => undefined);
  }, [businessId]);

  async function create(invoice: Invoice) {
    setLoading(true);
    try {
      await tradeApi.createReceivable(invoice.id);
      await refresh();
      onNotify('Receivable tokenized', `${invoice.invoice_number} is finance-ready.`);
    } catch (e) {
      onNotify('Failed', e instanceof Error ? e.message.slice(0, 120) : 'Error');
    } finally {
      setLoading(false);
    }
  }

  if (!isSme) return <p className="empty-state">Receivable creation requires an SME account.</p>;

  const confirmed = invoices.filter((i) => i.status === 'buyer_confirmed');

  return (
    <div className="page-stack">
      <section className="table-panel">
        <div className="panel-head"><strong>Tokenized receivables</strong><span>{receivables.length}</span></div>
        {receivables.length === 0 ? <p className="empty-state">No receivables yet.</p> : (
          <div className="table-wrap"><table><thead><tr><th>Debtor</th><th>Face value</th><th>Status</th><th>Proof</th></tr></thead><tbody>
            {receivables.map((r) => (
              <tr key={r.id}><td>{r.debtor_name}</td><td>{fmt(r.face_value, '')}</td><td>{titleCase(r.status)}</td><td><code>{r.proof_hash.slice(0, 12)}…</code></td></tr>
            ))}
          </tbody></table></div>
        )}
      </section>
      <section className="panel">
        <h3>Create from confirmed invoice</h3>
        {confirmed.length === 0 ? <p className="empty-state">Buyer must confirm an invoice first.</p> : (
          <div className="table-wrap"><table><thead><tr><th>Invoice</th><th>Amount</th><th /></tr></thead><tbody>
            {confirmed.map((i) => (
              <tr key={i.id}><td>{i.invoice_number}</td><td>{fmt(i.amount, '')}</td>
                <td><button type="button" className="btn small" disabled={loading} onClick={() => create(i)}>Tokenize</button></td></tr>
            ))}
          </tbody></table></div>
        )}
      </section>
    </div>
  );
}

export function ProofLedgerPage({ onNotify }: { onNotify: (title: string, message?: string) => void }) {
  const [bundles, setBundles] = useState<Awaited<ReturnType<typeof proofApi.listBundles>>>([]);
  const [loading, setLoading] = useState(false);

  async function refresh() {
    setBundles(await proofApi.listBundles());
  }

  useEffect(() => {
    void refresh().catch(() => undefined);
  }, []);

  async function anchor(bundleId: string) {
    setLoading(true);
    try {
      const result = await proofApi.anchor({ bundle_id: bundleId });
      await refresh();
      onNotify(
        result.on_chain ? 'Anchored on Amoy' : 'Simulated anchor',
        result.on_chain
          ? (result.explorer_url || result.polygon_tx_hash || 'On-chain')
          : 'Not broadcast — configure Amoy relayer',
      );
    } catch (e) {
      onNotify('Failed', e instanceof Error ? e.message.slice(0, 120) : 'Error');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="page-stack">
      <section className="page-intro"><p className="eyebrow">Credara</p><h2>Proof Ledger</h2><p>Credara proof bundles and Polygon Amoy transaction receipts.</p></section>
      <section className="table-panel">
        <div className="panel-head">
          <strong>Proof bundles</strong>
          <button type="button" className="btn secondary small" disabled={loading} onClick={refresh}>Refresh</button>
        </div>
        {bundles.length === 0 ? <p className="empty-state">No proof bundles yet. Complete a trade workflow step first.</p> : (
          <div className="table-wrap"><table><thead><tr><th>Type</th><th>Hash</th><th>Status</th><th>Tx</th><th /></tr></thead><tbody>
            {bundles.map((b) => (
              <tr key={b.id}>
                <td>{b.bundle_type}</td>
                <td><code>{b.proof_hash.slice(0, 14)}…</code></td>
                <td>{titleCase(b.status)}{b.on_chain === false || (!b.explorer_url && b.status !== 'anchored') ? <span className="pill amber" style={{ marginLeft: 8 }}>Simulated</span> : null}</td>
                <td>{b.explorer_url ? <a href={b.explorer_url} target="_blank" rel="noreferrer">Polygonscan</a> : '—'}</td>
                <td>{!b.on_chain ? <button type="button" className="btn small" disabled={loading} onClick={() => anchor(b.id)}>Anchor</button> : null}</td>
              </tr>
            ))}
          </tbody></table></div>
        )}
      </section>
    </div>
  );
}
