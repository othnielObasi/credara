'use client';

type LandingPageProps = {
  onSignIn: () => void;
  onSignUp: () => void;
};

export default function LandingPage({ onSignIn, onSignUp }: LandingPageProps) {
  const scrollTo = (id: string) => document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' });

  return (
    <div className="landing-page landing">
      <header className="landing-nav">
        <div className="brand-row"><div className="brand-mark">C</div><strong>Credara</strong></div>
        <nav className="landing-links" aria-label="Sections">
          <button type="button" onClick={() => scrollTo('solution')}>Solution</button>
          <button type="button" onClick={() => scrollTo('workflow')}>How it works</button>
          <button type="button" onClick={() => scrollTo('uae')}>For teams</button>
          <button type="button" onClick={() => scrollTo('polygon')}>Polygon stack</button>
        </nav>
        <div className="top-actions">
          <button type="button" className="btn secondary" onClick={onSignIn}>Sign in</button>
          <button type="button" className="btn" onClick={onSignUp}>Sign up</button>
        </div>
      </header>

      <section className="landing-hero">
        <div>
          <small className="eyebrow">Built on Polygon for UAE stablecoin and SME trade finance rails</small>
          <h1>Tokenized receivables, smart LCs, and <span>on-chain trade credit.</span></h1>
          <p>Credara helps SMEs, buyers, and financiers convert verified invoices, delivery proof, and settlement events into finance-ready receivables on Polygon — with stablecoin settlement and enterprise-grade compliance workflows.</p>
          <div className="hero-actions">
            <button type="button" className="btn dark" onClick={onSignUp}>Start enterprise demo</button>
            <button type="button" className="btn secondary" onClick={() => scrollTo('workflow')}>See process flow</button>
          </div>
        </div>
        <div className="visual-card">
          <div className="visual-top"><h3>Credara trade finance flow</h3><span className="pill green">Experimentable</span></div>
          <div className="chain-panel">
            <small>Receivables eligible for finance</small>
            <div className="amount">£182,700</div>
            <p>Buyer-confirmed invoices + verified delivery proof + Polygon proof receipt + Smart LC settlement.</p>
          </div>
          <div className="flow-steps">
            <div className="flow-row"><div className="flow-icon">▤</div><div><strong>Invoice confirmed</strong><span>Buyer validates obligation</span></div><span className="pill blue">Trade</span></div>
            <div className="flow-row"><div className="flow-icon">◎</div><div><strong>Proof anchored on Polygon</strong><span>ProofRegistry + ReceivableRegistry</span></div><span className="pill indigo">On-chain</span></div>
            <div className="flow-row"><div className="flow-icon">£</div><div><strong>Stablecoin settlement</strong><span>Mock USDC now, AED stablecoin-ready</span></div><span className="pill teal">Payment</span></div>
          </div>
        </div>
      </section>

      <section className="landing-band">
        <div className="trust-strip">
          <div><small className="eyebrow">Product focus</small><strong>SME trade finance infrastructure</strong><p style={{ color: 'var(--muted)', fontSize: 13, margin: '6px 0 0' }}>Not a generic wallet or marketplace. Credara converts verified commerce into financeable proof.</p></div>
          <div><small className="eyebrow">Polygon rail</small><strong>Amoy-ready</strong><p style={{ color: 'var(--muted)', fontSize: 13, margin: '6px 0 0' }}>ProofRegistry, SmartLC, receivables, and score attestations.</p></div>
          <div><small className="eyebrow">Settlement</small><strong>Stablecoin-ready</strong><p style={{ color: 'var(--muted)', fontSize: 13, margin: '6px 0 0' }}>Mock USDC now; AED stablecoin path for UAE adoption.</p></div>
          <div><small className="eyebrow">Launch context</small><strong>UAE / DIFC</strong><p style={{ color: 'var(--muted)', fontSize: 13, margin: '6px 0 0' }}>Designed for regulated SME trade corridors and fintech partners.</p></div>
        </div>
      </section>

      <section className="scale-section">
        <div className="scale-kicker">Built for a real market gap</div>
        <h2>One integrated platform for verified trade, capital access, and settlement.</h2>
        <p>Credara is designed around the Polygon challenge requirement: tokenized receivables, smart contract-based letters of credit, and on-chain trade credit scoring for SMEs.</p>
        <div className="trust-strip scale-metrics">
          <div className="scale-metric"><strong>$2T+</strong><span>global trade finance gap Credara targets</span></div>
          <div className="scale-metric"><strong>40%</strong><span>SME applications rejected due to weak evidence</span></div>
          <div className="scale-metric"><strong>7–10d</strong><span>manual LC processing Credara compresses</span></div>
          <div className="scale-metric"><strong>15M+</strong><span>TEUs at Jebel Ali scale opportunity</span></div>
        </div>
      </section>

      <section className="architecture-section">
        <div className="scale-kicker">Product architecture</div>
        <h2>One shared trust layer. Four connected workspaces.</h2>
        <p>Each party works in their own space but acts on the same verified record — so no one re-checks anyone else&apos;s paperwork.</p>
        <div className="architecture-grid">
          <div className="architecture-card">
            <small className="eyebrow">SME raises</small>
            <strong>SME Workspace</strong>
            <p>Orders, invoices, delivery proof, receivables, finance readiness and trust/credit scoring.</p>
          </div>
          <div className="architecture-card">
            <small className="eyebrow">Buyer confirms</small>
            <strong>Buyer Workspace</strong>
            <p>Supplier verification, invoice confirmation, delivery confirmation, and dispute handling.</p>
          </div>
          <div className="architecture-card">
            <small className="eyebrow">Financier funds</small>
            <strong>Financier Workspace</strong>
            <p>Verified receivables, credit score, financing offers, Smart LC funding and repayment tracking.</p>
          </div>
          <div className="architecture-card">
            <small className="eyebrow">Admin audits</small>
            <strong>Admin / Risk Workspace</strong>
            <p>KYB review, suspicious proof review, dispute resolution and full audit trail.</p>
          </div>
        </div>
      </section>

      <div id="workflow" />
      <section className="process-panel">
        <div className="process-inner">
          <div>
            <h2>How Credara works from invoice to settlement.</h2>
            <p>This is the complete product flow judges and enterprise users should understand before entering the demo workspace.</p>
          </div>
          <div className="process-line">
            {[
              ['Invoice is created and confirmed', 'The SME creates an invoice and the buyer confirms the trade obligation.'],
              ['Delivery proof is verified', 'OTP, buyer confirmation, timestamp, and logistics signals create proof confidence.'],
              ['Proof is anchored on Polygon', 'Private documents stay off-chain while proof hashes and lifecycle events become verifiable receipts.'],
              ['Receivable becomes finance-ready', 'The verified invoice becomes a tokenized receivable available for financier review.'],
              ['Smart LC settles with stablecoins', 'Escrow releases funds only when agreed delivery and proof conditions are satisfied.'],
            ].map(([t, b], i) => (
              <div key={t} className="process-step"><div className="process-num">{i + 1}</div><div><strong>{t}</strong><span>{b}</span></div></div>
            ))}
          </div>
        </div>
      </section>

      <div id="solution" />
      <section className="infra-section">
        <div className="infra-copy">
          <div className="tag">Verify trade</div>
          <h2>Turn invoices and delivery proof into trusted evidence.</h2>
          <p>Credara captures buyer confirmation, delivery evidence, OTP/QR handover, dispute state, and payment terms in one structured workflow.</p>
          <div className="infra-points">
            <div className="infra-point">Buyer-confirmed invoice state</div>
            <div className="infra-point">Delivery proof confidence scoring</div>
            <div className="infra-point">KYB and risk controls before financing</div>
          </div>
        </div>
        <div className="infra-visual">
          <div className="visual-list">
            <div className="visual-row"><div className="vicon">▤</div><div><strong>Invoice INV-2025-045</strong><span>Buyer confirmed · £24,500</span></div><span className="pill green">Verified</span></div>
            <div className="visual-row"><div className="vicon">✓</div><div><strong>Delivery proof</strong><span>OTP + buyer confirmation + timestamp</span></div><span className="pill green">High confidence</span></div>
            <div className="visual-row"><div className="vicon">K</div><div><strong>KYB profile</strong><span>Beneficial ownership and sanctions checks</span></div><span className="pill amber">Review</span></div>
          </div>
        </div>
      </section>

      <div id="polygon" />
      <section className="infra-section reverse">
        <div className="infra-copy">
          <div className="tag">Anchor on Polygon</div>
          <h2>Keep documents private, but make proof verifiable.</h2>
          <p>Private commercial records stay off-chain. Credara anchors proof hashes and lifecycle events through Polygon contracts, giving financiers and auditors tamper-evident receipts.</p>
          <div className="infra-points">
            <div className="infra-point">ProofRegistry for invoice and delivery bundle hashes</div>
            <div className="infra-point">ReceivableRegistry for tokenized receivable state</div>
            <div className="infra-point">CreditScoreAttestation for on-chain score snapshots</div>
          </div>
        </div>
        <div className="infra-visual">
          <div className="receipt-card">
            <small>Polygon proof receipt</small>
            <strong>Proof anchored</strong>
            <code>Network: Polygon Amoy · Chain ID: 80002<br />Tx: 0x7f3a9e2b4c8f01aa...ab24c</code>
          </div>
          <div className="visual-list">
            <div className="visual-row"><div className="vicon">◎</div><div><strong>ProofRegistry</strong><span>Invoice + delivery bundle hash</span></div><span className="pill indigo">On-chain</span></div>
            <div className="visual-row"><div className="vicon">◈</div><div><strong>ReceivableRegistry</strong><span>Receivable token/reference state</span></div><span className="pill indigo">On-chain</span></div>
          </div>
        </div>
      </section>

      <section className="infra-section">
        <div className="infra-copy">
          <div className="tag">Settle with Smart LC</div>
          <h2>Stablecoin escrow that releases only when trade proof is verified.</h2>
          <p>Credara&apos;s Smart LC workflow replaces slow paper-heavy processing with condition-based settlement: fund, verify, release, dispute, refund, or expire.</p>
          <div className="infra-points">
            <div className="infra-point">Mock USDC settlement in demo mode</div>
            <div className="infra-point">AED stablecoin-ready design for UAE adoption</div>
            <div className="infra-point">Dispute locks and admin/risk controls</div>
          </div>
        </div>
        <div className="infra-visual">
          <div className="visual-list">
            <div className="visual-row"><div className="vicon">1</div><div><strong>LC funded</strong><span>Buyer or financier funds escrow</span></div><span className="pill blue">Mock USDC</span></div>
            <div className="visual-row"><div className="vicon">2</div><div><strong>Delivery verified</strong><span>Proof conditions met</span></div><span className="pill green">Release enabled</span></div>
            <div className="visual-row"><div className="vicon">3</div><div><strong>Settlement released</strong><span>Seller payout recorded</span></div><span className="pill green">Settled</span></div>
          </div>
        </div>
      </section>

      <div id="developers" />
      <section className="infra-section reverse">
        <div className="infra-copy">
          <div className="tag">Developer infrastructure</div>
          <h2>APIs and webhooks for fintechs, lenders, and trade platforms.</h2>
          <p>Credara should be adopted as infrastructure, not only as a dashboard. Developers can integrate proof anchoring, receivable creation, Smart LC settlement, and credit-score reads.</p>
          <div className="infra-points">
            <div className="infra-point">API-first integration for lending and merchant platforms</div>
            <div className="infra-point">Webhook events for receivable, proof, LC, and score changes</div>
            <div className="infra-point">Polygon transaction references exposed to enterprise systems</div>
          </div>
        </div>
        <div className="infra-visual" style={{ padding: 0, background: 'transparent', border: 0, boxShadow: 'none', minHeight: 0 }}>
          <div className="code-window">
            <div className="code-top"><span className="code-dot" /><span className="code-dot" /><span className="code-dot" /></div>
            <pre>{`POST /api/v1/proofs/anchor
{
  "invoice_id": "INV-2025-045",
  "proof_bundle_hash": "0xproof45",
  "network": "polygon-amoy"
}

GET /api/v1/businesses/acme/trade-credit-score`}</pre>
          </div>
        </div>
      </section>

      <section className="reliability-panel">
        <div className="reliability-inner">
          <div>
            <h2>Built for enterprise reliability and auditability.</h2>
            <p>Credara is not only a workflow tool. It is an operational layer with relayers, indexers, outbox jobs, audit trails, and compliance controls.</p>
          </div>
          <div className="health-grid">
            <div className="health-card"><strong>Relayer outbox</strong><span>Retries failed Polygon writes safely</span></div>
            <div className="health-card"><strong>Indexer sync</strong><span>Reconciles on-chain state into dashboards</span></div>
            <div className="health-card"><strong>Audit logs</strong><span>Every sensitive action records who, what, why</span></div>
            <div className="health-card"><strong>Risk controls</strong><span>Dispute locks, KYB review, manual overrides</span></div>
          </div>
        </div>
      </section>

      <div id="uae" />
      <section className="landing-usecase">
        <div className="landing-usecase-inner">
          <div>
            <h2>UAE corridor use case: Jebel Ali supplier financing.</h2>
            <p>A verified SME supplier delivers goods to a buyer, anchors proof on Polygon, tokenizes the receivable, and receives a finance offer before the buyer&apos;s payment term expires.</p>
            <button type="button" className="btn dark" onClick={onSignUp}>Run this demo flow</button>
          </div>
          <div className="corridor-card">
            <div className="route">
              <div className="route-node">SME Supplier</div>
              <div className="route-line" />
              <div className="route-node">Buyer</div>
            </div>
            <div className="visual-list">
              <div className="visual-row"><div className="vicon">▤</div><div><strong>Invoice confirmed</strong><span>£24,500 receivable</span></div><span className="pill green">Verified</span></div>
              <div className="visual-row"><div className="vicon">◎</div><div><strong>Polygon receipt</strong><span>ProofRegistry transaction</span></div><span className="pill indigo">Anchored</span></div>
              <div className="visual-row"><div className="vicon">£</div><div><strong>Finance offer</strong><span>80% advance available</span></div><span className="pill blue">Offer</span></div>
            </div>
          </div>
        </div>
      </section>

      <section className="landing-final">
        <div className="landing-final-inner">
          <div><h2>Build on real API data</h2><p>Sign up to create orders, invoices, payment intents, and settlement ledger rows — backed by Postgres, not demo seed data.</p></div>
          <button type="button" className="btn dark" onClick={onSignUp}>Get started</button>
        </div>
      </section>

      <footer className="landing-footer">© 2026 Credara · Enterprise trade finance infrastructure on Polygon</footer>
    </div>
  );
}
