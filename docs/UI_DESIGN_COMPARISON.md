# UI Design Comparison: Main React App vs Standalone HTML

**Date:** 2026-07-09  
**Scope:** `apps/web/components/credara-live-app.tsx`, `apps/web/app/globals.css`, `apps/web/public/credara-enterprise-ui-v11.html`, `credara-ui.html`  
**Purpose:** Document how the runnable Next.js UI differs from the self-contained standalone enterprise UI.

---

## Summary

The repository ships **two UIs** that share a visual language but differ sharply in depth:

| | **Main UI (Next.js)** | **Standalone UI (HTML)** |
|---|---|---|
| **Files** | `credara-live-app.tsx` (~760 LOC) + `globals.css` (~817 LOC) | `credara-enterprise-ui-v11.html` (~461 KB, ~10K lines) |
| **Served at** | `/` and `/workspace` | `/credara-enterprise-ui-v11.html` (static file) |
| **Stack** | React 19 + Next.js 15 | Vanilla JS, inline CSS, no build step |
| **Self-contained** | Needs Next + API for live mode | Opens in a browser with zero dependencies |
| **Workspace pages** | ~30 nav items, ~8 real views | ~31 dedicated page renderers |
| **Landing** | 1 hero + auth card | 10+ marketing sections + footer |

`credara-ui.html` (repo root) and `apps/web/public/credara-enterprise-ui-v11.html` are **byte-identical**.

**Bottom line:** The standalone HTML is the **complete product design** — a self-contained enterprise trade-finance simulator with investor-grade landing and a walkable demo. The main React UI is a **partial reimplementation**: same shell and nav labels, similar visual tokens, but roughly **15–20% of the standalone's page depth**, with real API wiring limited to auth and payments/escrow.

---

## What Actually Runs

| Asset | Role | Served? |
|-------|------|---------|
| `apps/web/components/credara-live-app.tsx` | Main React app | **Yes** — `/` and `/workspace` |
| `apps/web/app/globals.css` | Design system | **Yes** |
| `apps/web/public/credara-enterprise-ui-v11.html` | Full standalone SPA | Static file only |
| `credara-ui.html` (repo root) | Duplicate of public HTML | **Not served** by Next.js |

The v12 migration moved off the iframe wrapper. The live app is a **React reimplementation**, not a port of the full HTML experience.

---

## Visual Design

Both use Inter, light backgrounds, glass panels, status pills, and a sidebar workspace. They are **cousins, not clones**.

### Color & Brand

**Standalone** — indigo/violet primary, gradient logo, richer palette:

```css
:root {
  --indigo: #5b5cf6;
  --navy: #07142f;
  --teal: #16a37b;
  /* gradient brand mark */
}
```

**Main React UI** — single blue accent, darker square logo:

```css
:root {
  --blue: #3157ff;
  --blue-dark: #203bd1;
  /* square #111827 brand mark */
}
```

### Layout Polish

| Element | Standalone | Main React |
|---------|------------|------------|
| Landing nav | Fixed, scroll anchors (Solution, Workflow, Polygon) | Simple top bar, no scroll sections |
| Hero | Two-column + flow visual card + eligible amount | Two-column hero + auth form only |
| Buttons | Primary / secondary / dark / success / danger | Primary / secondary / ghost |
| Workspace nav | Icons per item (⌂, CT, ID, ◈…) | Text-only buttons |
| Mobile | Sidebar backdrop + responsive rules | Basic responsive grid |
| Modals | `#modalRoot`, `#drawerRoot`, `#toastRoot` | Toast only |
| Dashboard | KPI strip + focus object + next-actions queue | 4 metrics + 2 panels |

The standalone UI is more **pitch-ready** (investor narrative, UAE/Jebel Ali corridor, Polygon contract names). The React UI is more **app-like** but thinner.

---

## Public / Landing Experience

### Standalone — Full Marketing Site

Section flow:

```text
Hero → Trust strip → Scale metrics ($2T gap, 40% rejection…)
  → 5-step process flow → Verify trade → Anchor on Polygon
  → Smart LC settlement → Developer API code window
  → Reliability panel → UAE corridor use case → Final CTA → Footer
```

Entry options:

- **Sign in / Sign up** (auth overlay)
- **View demo workspace** — instant access, no backend required

### Main React — Minimal Gate

- One hero block + auth form (sign up / sign in)
- No demo-without-login
- No process-flow sections, investor metrics, or Polygon stack explainer
- Must authenticate to enter the workspace

---

## Workspace Information Architecture

Nav coverage is similar on paper, but **implementation depth differs sharply**.

### Standalone: 31 Dedicated Page Renderers

Includes screens the React app **does not have as real pages**:

| Standalone-only or much richer | React equivalent |
|-------------------------------|------------------|
| `invoices` (list + actions) | Only `invoiceDetail` (static) |
| `contracts` (list) | Only `contractDetail` (static) |
| `relationships` | Missing |
| `logistics` | Missing (delivery is a stub) |
| `finance` (readiness) | Missing |
| `developers` | Folded into Settings / API Explorer stubs |
| `buyerInbox` | Stub `OperationalPage` (generic rows) |

### Dashboard Comparison

**Standalone:** Dynamic focus object, invoice-driven metrics, guided next-actions from `state.invoices`.

**React:** Hardcoded £24,500 story — `verifiedCount: 1`, `verifiedValue: 24500` regardless of backend data.

---

## Demo Data & Interactivity

### Standalone — Rich In-Memory Simulation

`initialState` includes:

- 5 invoices (Draft → Disputed lifecycle)
- 2 receivables, settlements, credit history
- Proof events, activity feed, audit log
- Directory profiles, relationships, trade contracts
- Opportunities, proposals, buyer inbox, logistics
- Risk rules, evidence bundles, repayment schedule
- Polygon contract addresses and tx list

**Demo tooling:**

- `guidedNext()` — walks full trade-finance story (invoice → confirm → delivery → proof → receivable → offer → LC → release)
- Demo control bar — "Run next workflow step", "Simulate chain confirmation", "Reset demo"
- `enterDemo()` — workspace without auth
- `resetDemo()` — restore seeded state

### Main React — Thin Seed + Partial Live Merge

Same demo characters (Acme Textiles, Global Retail, £24,500) but **far less state**. Most pages ignore API data and show static tables.

Live wiring exists only on the **settlement slice**:

```text
wallets → payment intents → escrow → ledger → reconciliation
```

---

## Backend / Live API Wiring

| Capability | Standalone | Main React |
|------------|------------|------------|
| Works offline | Yes — full demo | No — needs sign-in for real path |
| Auth | Simulated / optional | Real JWT register/login |
| `realApi()` layer | Partial; falls back to local sim | Primary path after login |
| Payment/escrow/ledger | Live + local fallback | Live with demo fallback if empty |
| Trade workflow (invoice CRUD, proof anchor) | Client-side simulation | Not implemented |
| Invitations | UI + partial `realApi` | Seed data only |
| Settings save | Partial | Read-only display |

### React: Wired Endpoints (`/api/v1/real/*`)

| Flow | Endpoints | UI trigger |
|------|-----------|------------|
| Auth | `POST /auth/register`, `POST /auth/login` | Sign up / Sign in |
| Workspace | `GET /real/workspaces/me`, `POST /real/onboarding/start` | Auto on login |
| Load state | `GET /real/settings`, `/api-keys`, `/wallets`, `/payment-intents`, `/escrows`, `/ledger` | `loadOperationalState()` |
| API keys | `POST /real/api-keys` | Settings / API Explorer |
| Payments | `POST /real/payment-intents`, `.../submit`, `.../confirm` | Create payment intent → fund escrow |
| Escrow | `POST /real/escrows`, `.../fund`, `.../release` | Wallets / Settlement pages |
| Ledger | `GET /real/ledger` | Sync backend |
| Reconciliation | `POST /real/reconciliation/{type}/{id}` | Reconciliation page |

### React: Not Wired (Despite Nav + Backend Existing)

| Feature | Backend exists | UI behavior |
|---------|----------------|-------------|
| Invitations | `POST/GET /real/invitations` | Seed data only |
| Members | via workspace | Seed data only |
| Settings save | `PUT /real/settings` | Read-only display |
| Webhooks | `POST /real/webhooks` | No UI action |
| Trade workflow | `/trade/*`, `/enterprise/*` | Static placeholders |
| Network discovery | `/network/*` | Hardcoded 3-row table |
| KYB | `/kyb/*` | Static "Pending review" |
| Buyer inbox | `/buyer-inbox/*` | Static rows |
| Contract/invoice docs | `/contracts/*`, `/invoices/*` | Hardcoded INV-2025-045 |
| Proof ledger | `/proof-ledger/*` | Reuses ledger or static rows |
| Role navigation API | `GET /real/access/navigation/{role}` | Client-only `roleAllowed` |
| Enterprise endpoints in `lib/api.ts` | 14 mapped routes | Dead code (never imported) |

Rough coverage: **~12 of 31** `real_workflow` endpoints are used; **0** enterprise/trade/network routes from the main UI.

### Data Flow Pattern (React)

```text
initialState (demo seed)
       │
       ▼
  Sign in / Sign up ──► JWT in localStorage
       │
       ▼
  loadOperationalState() ──► merge API data OR keep demo fallback
       │
       ├── wallets/payments/escrows/ledger  → live when backend returns rows
       ├── invitations/members/network/etc. → always demo unless extended
       └── metrics/dashboard                → partly computed, partly hardcoded
```

**Notable behaviors:**

1. **Demo fallback:** If API returns empty arrays, UI keeps seeded wallets, ledger, and escrows.
2. **Role switch is cosmetic:** Dropdown updates client state only; does not re-auth or call `/real/access/navigation/{role}`.
3. **Fake chain tx:** Payment submit sends synthetic hash (`0xui${timestamp}`), not a real Polygon tx.
4. **Hardcoded demo amounts:** Escrow creation always uses `LC-015`, `24500`, `Acme Textiles Ltd`.

---

## Architecture Model

```text
STANDALONE (self-contained)
┌─────────────────────────────────────────┐
│  Landing (10+ sections)                 │
│  Auth overlay OR enterDemo()            │
├─────────────────────────────────────────┤
│  Workspace shell                        │
│  state = rich initialState              │
│  render() → 31 view functions           │
│  guidedNext() / demo controls           │
│  realApi() optional overlay             │
└─────────────────────────────────────────┘

MAIN REACT (Next.js)
┌─────────────────────────────────────────┐
│  PublicSurface (hero + auth only)       │
├─────────────────────────────────────────┤
│  Workspace shell                        │
│  useCredaraApp() hook                   │
│  PageRenderer → ~8 real components      │
│           → stubs for rest              │
│  authFetch() for /real/* settlement     │
└─────────────────────────────────────────┘
```

---

## Verdict by Dimension

| Dimension | Standalone | Main React |
|-----------|------------|------------|
| Pitch / judge demo | **Strong** | Weak |
| Visual richness | **Strong** | Moderate |
| Self-contained portability | **Strong** | Requires stack |
| Live backend integration | Partial | **Stronger** (settlement path) |
| Code maintainability | Monolith HTML | **Stronger** (typed React) |
| Product completeness | **Strong** | ~15–20% depth |
| Production path | Demo-first | Backend-first (incomplete surface) |

---

## Dead Code & Unused Dependencies

| Item | Status |
|------|--------|
| `apps/web/lib/api.ts` | Full enterprise client — never imported |
| `@tanstack/react-query` | In `package.json`, unused |
| `viem` | In `package.json`, unused |
| `credara-ui.html` | Duplicate of public HTML, not served |
| Env var `WEB_PUBLIC_API_BASE` | React reads `NEXT_PUBLIC_API_BASE` instead |

---

## Infrastructure Notes

| Concern | Status |
|---------|--------|
| API base URL | `NEXT_PUBLIC_API_BASE` or fallback `/api/v1` |
| Production proxy | Caddy routes `/api/*` → API, rest → web |
| Local dev | No Next.js rewrites — needs API on `:8000` + CORS, or proxy |
| Docker web | Runs `npm run dev`, not production `next start` |

---

## Practical Implication

- **`make dev` → `:3000`** serves the **slimmer React UI**.
- The **full product design** still lives primarily in the **standalone HTML**.
- Two UIs coexist awkwardly: richer experience is not the default route.

---

## Recommended Consolidation Paths

### Option A — Port standalone into React (incremental)

1. Port landing sections from HTML into React public pages.
2. Port page view functions one workspace area at a time (trade → network → trust).
3. Wire each ported page to existing backend routes.
4. Remove demo fallback once authenticated; show empty states instead.
5. Delete duplicate HTML files when parity is reached.

### Option B — Serve standalone as default, React for live slices

1. Default route serves standalone HTML for demo/pitch.
2. Keep React app for authenticated settlement workflow only.
3. Deep-link between them where live API is needed.

### High-Impact Wiring Fixes (React)

1. Wire invitations, settings PUT, and members from `/real/*`.
2. Connect trade/network pages to `/enterprise/*` and `/network/*` via `lib/api.ts`.
3. Use `/real/access/navigation/{role}` instead of hardcoded `roleAllowed`.
4. Add Next.js rewrites for `/api` in dev; align env var names.

---

## Related Docs

- `docs/CODEBASE_REVIEW.md` — Security and wiring gaps (2026-07-07)
- `docs/REAL_WORKFLOW_WIRING_V11.md` — Backend endpoint details for `/real/*`
- `docs/ROLE_FILTERED_SETTINGS.md` — Role-filtered navigation spec
- `docs/UI_NETWORK_DISCOVERY_UPDATE.md` — Network layer UI notes
- `README.md` — v12 Enterprise UI Alignment Update section
