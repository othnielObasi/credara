'use client';

import { useEffect, useState } from 'react';
import { tradeApi, type Invoice, type Order } from '../../lib/api/trade';
import { fmt } from '../../lib/format';

type Props = {
  businessId: string | null;
  businessName: string;
  onNotify: (title: string, message?: string) => void;
};

export function TradeWorkflowPanel({ businessId, businessName, onNotify }: Props) {
  const [orders, setOrders] = useState<Order[]>([]);
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [buyerName, setBuyerName] = useState('');
  const [description, setDescription] = useState('');
  const [amount, setAmount] = useState('24500');
  const [loading, setLoading] = useState(false);

  async function refresh() {
    if (!businessId) return;
    const [o, i] = await Promise.all([tradeApi.listOrders(businessId), tradeApi.listInvoices(businessId)]);
    setOrders(o);
    setInvoices(i);
  }

  useEffect(() => {
    if (businessId) void refresh().catch(() => undefined);
  }, [businessId]);

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
      onNotify('Order created', 'Trade order saved to the backend.');
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

  return (
    <div className="page-stack">
      <section className="panel">
        <h3>Create trade order</h3>
        <p style={{ color: 'var(--muted)' }}>Seller: {businessName || 'Your business'}</p>
        <div className="two-grid" style={{ marginTop: 16 }}>
          <label>Buyer<input value={buyerName} onChange={(e) => setBuyerName(e.target.value)} placeholder="Global Retail Ltd" /></label>
          <label>Amount (USDC)<input value={amount} onChange={(e) => setAmount(e.target.value)} /></label>
        </div>
        <label style={{ display: 'grid', gap: 8, marginTop: 12 }}>Description<textarea value={description} onChange={(e) => setDescription(e.target.value)} rows={2} /></label>
        <div className="top-actions" style={{ marginTop: 16 }}>
          <button type="button" className="btn" disabled={loading} onClick={createOrder}>Create order</button>
          <button type="button" className="btn secondary" disabled={!businessId || loading} onClick={refresh}>Refresh</button>
        </div>
      </section>
      <section className="two-grid">
        <div className="table-panel">
          <div className="panel-head"><strong>Orders</strong><span>{orders.length}</span></div>
          {orders.length === 0 ? <p className="empty-state">No orders yet. Create your first trade order.</p> : (
            <table><thead><tr><th>Buyer</th><th>Amount</th><th>Status</th><th /></tr></thead><tbody>
              {orders.map((o) => (
                <tr key={o.id}><td>{o.buyer_name}</td><td>{fmt(o.total_amount, '')} {o.currency}</td><td>{o.status}</td>
                  <td><button type="button" className="btn secondary small" disabled={loading} onClick={() => issueInvoice(o)}>Invoice</button></td></tr>
              ))}
            </tbody></table>
          )}
        </div>
        <div className="table-panel">
          <div className="panel-head"><strong>Invoices</strong><span>{invoices.length}</span></div>
          {invoices.length === 0 ? <p className="empty-state">Issue an invoice from an order.</p> : (
            <table><thead><tr><th>Number</th><th>Amount</th><th>Status</th></tr></thead><tbody>
              {invoices.map((i) => <tr key={i.id}><td>{i.invoice_number}</td><td>{fmt(i.amount, '')}</td><td>{i.status}</td></tr>)}
            </tbody></table>
          )}
        </div>
      </section>
    </div>
  );
}
