'use client';

type LandingPageProps = {
  onSignIn: () => void;
  onSignUp: () => void;
};

export default function LandingPage({ onSignIn, onSignUp }: LandingPageProps) {
  const scrollTo = (id: string) => document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' });

  return (
    <div className="landing-page">
      <header className="landing-nav">
        <div className="brand-row"><div className="brand-mark">C</div><strong>credara</strong></div>
        <nav className="landing-links" aria-label="Sections">
          <button type="button" onClick={() => scrollTo('workflow')}>How it works</button>
          <button type="button" onClick={() => scrollTo('polygon')}>Polygon</button>
          <button type="button" onClick={() => scrollTo('uae')}>UAE corridor</button>
        </nav>
        <div className="top-actions">
          <button type="button" className="btn secondary" onClick={onSignIn}>Sign in</button>
          <button type="button" className="btn" onClick={onSignUp}>Create workspace</button>
        </div>
      </header>

      <section className="landing-hero">
        <div>
          <small className="eyebrow">Polygon · DIFC · SME trade finance</small>
          <h1>Tokenized receivables, smart LCs, and <span>on-chain trade credit</span></h1>
          <p>Verify invoices and delivery proof, tokenize receivables, and settle with stablecoin Smart LC escrow — built for UAE trade corridors like Jebel Ali.</p>
          <div className="hero-actions">
            <button type="button" className="btn dark" onClick={onSignUp}>Start live workspace</button>
            <button type="button" className="btn secondary" onClick={() => scrollTo('workflow')}>See the flow</button>
          </div>
        </div>
        <div className="panel">
          <strong>Hackathon Problem #1</strong>
          <p style={{ color: 'var(--muted)' }}>$2T trade finance gap · 40% SME rejection · 7–10 day LC processing</p>
          <div className="metric-grid" style={{ marginTop: 16 }}>
            <div className="metric-card"><span>Invoice confirmed</span><strong>Trade</strong></div>
            <div className="metric-card"><span>Proof anchored</span><strong>Polygon</strong></div>
            <div className="metric-card"><span>Stablecoin escrow</span><strong>Settlement</strong></div>
          </div>
        </div>
      </section>

      <section className="landing-band">
        <div className="trust-strip">
          <div><small className="eyebrow">Verify</small><strong>Multi-party proof</strong><p>Buyer + logistics + SME evidence bundles.</p></div>
          <div><small className="eyebrow">Finance</small><strong>Tokenized receivables</strong><p>Finance-ready assets for lenders.</p></div>
          <div><small className="eyebrow">Settle</small><strong>Smart LC escrow</strong><p>MockUSDC demo · AED-ready design.</p></div>
          <div><small className="eyebrow">Score</small><strong>Trade credit</strong><p>On-chain attestation on Polygon.</p></div>
        </div>
      </section>

      <div id="workflow" />
      <section className="landing-process">
        <h2>Invoice to settlement in five steps</h2>
        <div className="process-line">
          {[
            ['Create & confirm invoice', 'SME issues; buyer confirms obligation.'],
            ['Verify delivery proof', 'OTP, logistics, buyer confirmation.'],
            ['Anchor proof on Polygon', 'Hash on-chain; documents off-chain.'],
            ['Tokenize receivable', 'Financier reviews and offers advance.'],
            ['Smart LC stablecoin release', 'Escrow pays when conditions met.'],
          ].map(([t, b], i) => (
            <div key={t} className="process-step"><div className="process-num">{i + 1}</div><div><strong>{t}</strong><p style={{ color: 'var(--muted)', margin: '6px 0 0' }}>{b}</p></div></div>
          ))}
        </div>
      </section>

      <div id="polygon" />
      <section className="landing-band">
        <h2>Polygon infrastructure</h2>
        <div className="health-grid" style={{ gridTemplateColumns: 'repeat(3, 1fr)' }}>
          <div className="health-card"><strong>ProofRegistry</strong><span>Invoice + delivery bundle hashes</span></div>
          <div className="health-card"><strong>ReceivableRegistry</strong><span>Tokenized receivable state</span></div>
          <div className="health-card"><strong>SmartLCFactory</strong><span>Programmable LC escrow</span></div>
        </div>
      </section>

      <div id="uae" />
      <section className="landing-usecase">
        <div className="landing-usecase-inner">
          <div>
            <h2>Jebel Ali supplier financing</h2>
            <p>A verified UAE supplier delivers to a buyer, anchors proof on Polygon Amoy, and unlocks stablecoin settlement before the buyer&apos;s 90-day term.</p>
            <button type="button" className="btn dark" onClick={onSignUp}>Open workspace</button>
          </div>
          <div className="visual-row"><strong>UAE / DIFC pilot ready</strong><span className="pill green">Corridor</span></div>
        </div>
      </section>

      <section className="landing-final">
        <div className="landing-final-inner">
          <div><h2>Build on real API data</h2><p>Sign up to create orders, invoices, payment intents, and settlement ledger rows — backed by Postgres, not demo seed data.</p></div>
          <button type="button" className="btn" onClick={onSignUp}>Get started</button>
        </div>
      </section>
      <footer className="landing-footer">© 2026 Credara · Enterprise trade finance on Polygon</footer>
    </div>
  );
}
