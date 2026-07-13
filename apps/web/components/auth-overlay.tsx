'use client';

import type { Dispatch, FormEvent, SetStateAction } from 'react';
import { titleCase } from '../lib/format';
import { OAUTH_LOGIN_URL } from '../lib/api';

type Role = 'sme' | 'buyer' | 'financier' | 'admin' | 'developer';

type AuthForm = {
  fullName: string;
  email: string;
  password: string;
  businessName: string;
  role: Role;
  country: string;
  registrationNumber: string;
  sector: string;
};

type AuthOverlayProps = {
  authMode: 'signin' | 'signup';
  authForm: AuthForm;
  setAuthForm: Dispatch<SetStateAction<AuthForm>>;
  setAuthMode: (mode: 'signin' | 'signup') => void;
  onClose: () => void;
  onSignUp: (event: FormEvent) => void;
  onSignIn: (event: FormEvent) => void;
};

const SIGNUP_ROLES: { role: 'sme' | 'buyer' | 'financier'; title: string; hint: string; recommended?: boolean }[] = [
  { role: 'sme', title: 'SME', hint: 'Create invoice & anchor proof', recommended: true },
  { role: 'buyer', title: 'Buyer', hint: 'Confirm trade obligations' },
  { role: 'financier', title: 'Financier', hint: 'Fund Smart LC escrow' },
];

export default function AuthOverlay({
  authMode,
  authForm,
  setAuthForm,
  setAuthMode,
  onClose,
  onSignUp,
  onSignIn,
}: AuthOverlayProps) {
  const isSignup = authMode === 'signup';

  return (
    <div
      className="auth-overlay"
      role="dialog"
      aria-modal="true"
      aria-labelledby="auth-dialog-title"
      onClick={onClose}
    >
      <form
        className="auth-panel"
        onSubmit={isSignup ? onSignUp : onSignIn}
        onClick={(e) => e.stopPropagation()}
      >
        <header className="auth-panel-header">
          <div className="brand-row">
            <div className="brand-mark">C</div>
            <div>
              <strong>Credara</strong>
              <span>Enterprise trade finance</span>
            </div>
          </div>
          <button type="button" className="auth-panel-close" onClick={onClose} aria-label="Close">
            ×
          </button>
        </header>

        <div className="auth-panel-tabs" role="tablist" aria-label="Authentication mode">
          <button
            type="button"
            role="tab"
            aria-selected={isSignup}
            className={isSignup ? 'active' : ''}
            onClick={() => setAuthMode('signup')}
          >
            Sign up
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={!isSignup}
            className={!isSignup ? 'active' : ''}
            onClick={() => setAuthMode('signin')}
          >
            Sign in
          </button>
        </div>

        <div className="auth-panel-body">
          <p className="eyebrow">Polygon Amoy · Live workspace</p>
          <h2 id="auth-dialog-title">{isSignup ? 'Create your demo workspace' : 'Welcome back'}</h2>
          <p className="auth-panel-lead">
            {isSignup
              ? 'Start as SME for the 3-minute judge path — invoice, proof anchor, Smart LC settlement.'
              : 'Sign in to load your persistent workspace and continue the live demo.'}
          </p>

          <div className="auth-judge-callout">
            <span className="auth-judge-callout-icon" aria-hidden="true">
              i
            </span>
            <p>
              <strong>Judges:</strong> sign up as <strong>SME</strong> · Judge demo mode is on by default ·
              email/password is fastest if Auth0 is slow
            </p>
          </div>

          {isSignup && (
            <div className="auth-field-grid">
              <label className="auth-field">
                <span>Full name</span>
                <input
                  value={authForm.fullName}
                  onChange={(e) => setAuthForm({ ...authForm, fullName: e.target.value })}
                  placeholder="Your name"
                  autoComplete="name"
                />
              </label>
              <label className="auth-field">
                <span>Business name</span>
                <input
                  value={authForm.businessName}
                  onChange={(e) => setAuthForm({ ...authForm, businessName: e.target.value })}
                  placeholder="Acme Trading LLC"
                  autoComplete="organization"
                />
              </label>
            </div>
          )}

          {isSignup && (
            <fieldset className="auth-role-picker">
              <legend>Workspace role</legend>
              <div className="auth-role-grid">
                {SIGNUP_ROLES.map(({ role, title, hint, recommended }) => (
                  <button
                    key={role}
                    type="button"
                    className={`auth-role-card${authForm.role === role ? ' selected' : ''}`}
                    onClick={() => setAuthForm({ ...authForm, role })}
                  >
                    {recommended && <span className="auth-role-badge">Recommended</span>}
                    <strong>{title}</strong>
                    <span>{hint}</span>
                  </button>
                ))}
              </div>
            </fieldset>
          )}

          <label className="auth-field">
            <span>Email</span>
            <input
              type="email"
              value={authForm.email}
              onChange={(e) => setAuthForm({ ...authForm, email: e.target.value })}
              placeholder="you@company.com"
              autoComplete="email"
              required
            />
          </label>

          <label className="auth-field">
            <span>Password</span>
            <input
              type="password"
              value={authForm.password}
              onChange={(e) => setAuthForm({ ...authForm, password: e.target.value })}
              placeholder={isSignup ? 'At least 8 characters' : 'Your password'}
              autoComplete={isSignup ? 'new-password' : 'current-password'}
              minLength={isSignup ? 8 : undefined}
              required
            />
          </label>

          <button className="btn auth-submit" type="submit">
            {isSignup ? 'Create live workspace' : 'Sign in to workspace'}
          </button>

          <div className="auth-divider">
            <span>or</span>
          </div>

          <button
            type="button"
            className="btn secondary full auth-oauth"
            onClick={() => {
              window.location.href = OAUTH_LOGIN_URL;
            }}
          >
            Continue with Auth0
          </button>

          <p className="auth-panel-foot">
            Live on Polygon Amoy · {titleCase(authForm.role)} workspace · ~3 min judge demo
          </p>
        </div>
      </form>
    </div>
  );
}
