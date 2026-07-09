# UI Production Build Checklist

**Purpose:** Gate document to complete **before** starting any UI port/build work.  
**Use when:** Planning or executing the move from standalone HTML → production React UI.  
**Status:** Active — do not start UI implementation phases until the relevant section is checked.

---

## Where checklists live in this repo

| Document | Scope | When to use |
|----------|-------|-------------|
| **`docs/UI_PRODUCTION_BUILD_CHECKLIST.md`** (this file) | UI port, wiring, parity with standalone | **Before any UI build** |
| `docs/PROCESS_FLOW_IMPLEMENTATION_CHECKLIST.md` | End-to-end product flows (KYB, proof, LC, scoring…) | Sprint planning, flow reviews |
| `docs/UI_DESIGN_COMPARISON.md` | Main React vs standalone HTML gap analysis | Design/reference during UI work |
| `docs/CODEBASE_REVIEW.md` | Security + wiring findings | Before demo/submit; fix P1 items first |
| `security/deployment-readiness-checklist.md` | Testnet/mainnet deploy | Before chain deploy |
| `security/audit-checklist.md` | Smart contract audit prep | Before external audit |

---

## Pre-build gates (required before Phase 0)

Complete these **before** writing UI code for the production port.

### 1. Decision locked

- [ ] **Chosen path documented:** Option A (incremental React port) or Option B (standalone default + React slices).
- [ ] **Default recommendation:** Option A — port standalone into React page by page.
- [ ] **Standalone HTML role defined:** design spec / reference until parity, then delete.
- [ ] **Demo mode policy defined:** live backend default after auth; demo seed only via explicit toggle.

### 2. Design reference frozen

- [ ] Reference file identified: `apps/web/public/credara-enterprise-ui-v11.html`
- [ ] Page inventory captured (31 workspace views + landing sections) — see `docs/UI_DESIGN_COMPARISON.md`
- [ ] Visual tokens extracted (indigo palette, pills, cards, nav icons)
- [ ] “Exact replica” scope defined: same UX/copy/layout, not same monolithic file structure

### 3. Backend blockers reviewed

Fix or accept these **before** wiring UI to production flows:

| Blocker | Doc reference | Must fix before |
|---------|---------------|-----------------|
| Simulated Polygon relayer (`simulate_tx_hash`) | `docs/CODEBASE_REVIEW.md` | Claiming “on-chain” in UI |
| KYB webhook signature verification | `docs/CODEBASE_REVIEW.md` | KYB gates in UI |
| Tenant scoping on all trade/finance routes | `apps/api/app/api/v1/routes/trade.py` | Multi-tenant demo |
| Real JWT secret in deploy | `.env.example` | Any public deploy |

### 4. Environment & tooling ready

- [ ] `cp .env.example .env` and set `JWT_SECRET`, `DATABASE_URL`
- [ ] `make dev` runs API (:8000) + web (:3000) + Postgres
- [ ] API docs reachable: `http://localhost:8000/docs`
- [ ] Agreed API base: `NEXT_PUBLIC_API_BASE=/api/v1` with Next.js rewrite to API in dev
- [ ] Branch strategy: feature branches `cursor/<name>-9e59` off `main`

### 5. Success criteria defined

A “real working system” means:

- [ ] User can register, create workspace, and see **empty states** (not demo seed) when no data exists
- [ ] SME can create order → invoice through API from UI
- [ ] Payment → escrow → ledger → reconciliation works without demo fallback
- [ ] Role nav matches server (`GET /real/access/navigation/{role}`)
- [ ] No page shows fake Acme/Global Retail data after authentication unless demo mode is on

---

## Build phases (execute in order)

Do **not** skip ahead. Each phase has exit criteria.

### Phase 0 — Foundation

**Start only after:** Pre-build gates above are checked.

- [ ] Typed API layer: `apps/web/lib/api/` (`client`, `auth`, `real`, `trade`)
- [ ] React Query provider in `app/layout.tsx`
- [ ] Design tokens: `apps/web/styles/tokens.css` aligned with standalone
- [ ] Next.js `/api/v1` rewrite in `next.config.ts`
- [ ] Remove duplicate fetch logic from components
- [ ] Delete or wire `apps/web/lib/api.ts` dead enterprise client

**Exit criteria:** Auth works; one authenticated API call via shared client; no new inline `fetch` in components.

---

### Phase 1 — Landing + shell parity

- [ ] Port landing sections (hero, process flow, Polygon, UAE corridor, footer)
- [ ] Auth gate: sign up / sign in (real JWT)
- [ ] Workspace shell: sidebar, tenant card, live status bar, role nav from server
- [ ] Mobile sidebar/backdrop

**Exit criteria:** Landing visually matches standalone; authenticated user enters workspace shell.

---

### Phase 2 — Settlement slice (production-grade)

- [ ] Wallets — `GET/POST /real/wallets`
- [ ] Payment intents — create / submit / confirm
- [ ] Escrows — create / fund / release
- [ ] Ledger — `GET /real/ledger`
- [ ] Reconciliation — `POST /real/reconciliation/{type}/{id}`
- [ ] Settings save — `PUT /real/settings`
- [ ] API keys — `POST /real/api-keys`
- [ ] **No demo fallback** after auth on these pages

**Exit criteria:** Full settlement path works with empty initial state; data persists across refresh.

---

### Phase 3 — Setup & access

- [ ] Onboarding — `/real/onboarding/*`
- [ ] Invitations — `GET/POST /real/invitations`
- [ ] Members — from workspace membership API
- [ ] Business profile — business + KYB read

**Exit criteria:** New user onboarding and invite flow work end-to-end.

---

### Phase 4 — Trade core (solves the real problem)

- [ ] Order list + create — `GET/POST /trade/orders`
- [ ] Invoice list + create — `GET/POST /trade/invoices`
- [ ] Buyer confirm invoice
- [ ] Delivery proof submit
- [ ] Receivable create (gated by invoice status)
- [ ] Replace client `guidedNext()` with server-driven workflow state

**Exit criteria:** README 8-step demo flow completable through React UI + API (chain step may still be simulated until relayer is real).

---

### Phase 5 — Network + financier

- [ ] Directory, opportunities, proposals — `/network/*`
- [ ] Marketplace, deal room — `/enterprise/*` or `/network/*`
- [ ] Repayments, credit score UI

**Exit criteria:** Financier can discover and review receivables from live API data.

---

### Phase 6 — Admin + platform

- [ ] KYB review UI — `/kyb/*`, `/admin/*`
- [ ] Risk rules, permissions matrix
- [ ] API Explorer wired to OpenAPI
- [ ] Launch readiness page

---

### Phase 7 — Production hardening

- [ ] Real Polygon Amoy transaction (replace `simulate_tx_hash`)
- [ ] OIDC/Clerk auth (replace demo JWT form)
- [ ] `next build` + `next start` in Docker (not `npm run dev`)
- [ ] Playwright E2E: auth, order, settlement per role
- [ ] Delete `credara-ui.html` + `credara-enterprise-ui-v11.html` after parity sign-off
- [ ] Wire `packages/shared/domain.json` into API + web types

**Exit criteria:** `security/deployment-readiness-checklist.md` testnet section completable.

---

## Per-page port checklist (copy for each workspace page)

When porting a standalone page to React:

- [ ] Standalone view function identified (e.g. `invoiceDetailView`)
- [ ] React route/component created
- [ ] API endpoint(s) identified and typed
- [ ] Loading, empty, and error states implemented
- [ ] Role access checked via server nav
- [ ] No hardcoded demo rows after auth
- [ ] Visual parity spot-checked against standalone
- [ ] Manual test recorded (role, steps, result)

---

## What not to do

- [ ] Do **not** copy-paste the 10K-line HTML into one React file
- [ ] Do **not** wire money-movement pages before auth + tenant checks verified
- [ ] Do **not** keep demo seed as silent fallback after login
- [ ] Do **not** claim on-chain proof until relayer sends real txs
- [ ] Do **not** delete standalone HTML until Phase 4+ parity sign-off

---

## Current status (update as work progresses)

| Phase | Status | Notes |
|-------|--------|-------|
| Pre-build gates | ⬜ Not started | Checklist created 2026-07-09 |
| Phase 0 | ⬜ Not started | Partial uncommitted files exist — **do not merge until gated** |
| Phase 1 | ⬜ Not started | |
| Phase 2 | 🟡 Partial | Settlement wired in old `credara-live-app.tsx`; needs hardening |
| Phase 3 | ⬜ Not started | |
| Phase 4 | ⬜ Not started | |
| Phase 5–7 | ⬜ Not started | |

---

## Related docs

- `docs/UI_DESIGN_COMPARISON.md` — gap analysis driving this checklist
- `docs/REAL_WORKFLOW_WIRING_V11.md` — `/real/*` endpoint reference
- `docs/PROCESS_FLOW_IMPLEMENTATION_CHECKLIST.md` — backend/flow readiness
- `docs/CODEBASE_REVIEW.md` — P1 security fixes before public demo
