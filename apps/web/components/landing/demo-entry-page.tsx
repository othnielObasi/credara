'use client';

type DemoEntryPageProps = {
  onSignIn: () => void;
  onSignUp: () => void;
};

const RELEASE_TX =
  'https://amoy.polygonscan.com/tx/0x5743a885e54063da6c4056d73e4b49113918558fd09d8973c9074de8e57af9de';

export default function DemoEntryPage({ onSignIn, onSignUp }: DemoEntryPageProps) {
  return (
    <div className="demo-entry">
      <header className="demo-entry-header">
        <div className="brand-row">
          <div className="brand-mark">C</div>
          <div>
            <strong>Credara</strong>
            <span>Live judge demo</span>
          </div>
        </div>
        <a className="btn ghost small" href="/">
          Marketing site
        </a>
      </header>

      <section className="demo-entry-hero panel">
        <p className="eyebrow">Smart Commerce · Polygon Amoy</p>
        <h1>Open the live demo workspace</h1>
        <p className="demo-entry-lead">
          Sign up as <strong>SME</strong> to start. Judge demo mode is on by default — invoice → proof →
          finance → Smart LC in ~3 minutes.
        </p>
        <div className="demo-entry-actions">
          <button type="button" className="btn" onClick={onSignUp}>
            Start demo (sign up)
          </button>
          <button type="button" className="btn secondary" onClick={onSignIn}>
            Sign in
          </button>
        </div>
        <p className="demo-entry-hint">
          Email/password recommended for judges · Auth0 optional ·{' '}
          <a href={RELEASE_TX} target="_blank" rel="noreferrer">
            View live release tx on Polygonscan
          </a>
        </p>
      </section>

      <section className="demo-entry-steps panel">
        <h2>Judge path (5 steps)</h2>
        <ol className="demo-entry-step-list">
          <li>
            <strong>SME</strong> — order → invoice → delivery proof
          </li>
          <li>
            <strong>Buyer</strong> — confirm invoice (switch role in sidebar)
          </li>
          <li>
            <strong>SME</strong> — receivable → anchor proof (look for Anchored + Polygonscan)
          </li>
          <li>
            <strong>Financier</strong> — deal room → fund Smart LC
          </li>
          <li>
            <strong>System</strong> — verify delivery → release settlement
          </li>
        </ol>
      </section>
    </div>
  );
}
