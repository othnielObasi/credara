# UI Production Build Checklist

**Purpose:** Gate document to complete **before** starting any UI port/build work.  
**Use when:** Planning or executing the move from standalone HTML → production React UI.  
**Status:** Active — do not start UI implementation phases until the relevant section is checked.

---

## What problems Credara solves

Credara targets the **global trade finance gap**: SMEs that deliver real goods to credible buyers still wait 30–90+ days for payment, while banks and alternative lenders struggle to fund them cheaply because trade claims are hard to verify, easy to fake, and expensive to underwrite.

### The core pain (plain language)

A supplier ships £100,000 of goods to a large buyer. The buyer will not pay for 90 days. The supplier still must pay staff, materials, and logistics **now**. Traditional finance is slow, document-heavy, and often unavailable to smaller firms.

Credara does not magically remove the **cost of early funding** (e.g. a financier advancing £98,000 today for a £100,000 invoice). It attacks the reasons that cost is so high and opaque today.

### Problem 1 — Invoice and trade fraud

**Today:** Fake or duplicate invoices, weak buyer confirmation, and inconsistent paperwork let bad actors borrow against the same receivable more than once.

**Credara’s answer:** Multi-party verification (SME, buyer, logistics) compiled into a **proof bundle**; only a cryptographic hash is anchored on Polygon. Documents stay off-chain; tampering is detectable.

**Build implication:** Buyer inbox, delivery proof, and proof anchoring must be real workflow gates — not UI theatre.

---

### Problem 2 — Slow, manual settlement and letters of credit

**Today:** LC and trade settlement involve days of bank coordination, paper checks, and disputed handoffs.

**Credara’s answer:** **Smart Contract Letters of Credit** — escrow releases when agreed conditions (invoice confirmed, delivery verified, no open dispute) are met.

**Build implication:** Settlement UI must reflect Smart LC state from API/contracts; relayer must eventually send real txs, not `simulate_tx_hash`.

---

### Problem 3 — SMEs lack tradable credit history

**Today:** Banks rely on balance sheets and long relationships. Many growing suppliers are “unbankable” despite good buyers and clean delivery track records.

**Credara’s answer:** **Trade credit scoring** from real order, invoice, settlement, and dispute history; optional on-chain attestation.

**Build implication:** Score/readiness pages must consume `/finance/*` and audit data, not static demo numbers.

---

### Problem 4 — High cost and opacity of supply-chain finance

**Today:** Manual KYB, logistics checks, and legal review make small-ticket deals uneconomic. Suppliers often do not know financing cost until late in the process.

**Credara’s answer:** Automated KYB/logistics scoring, **financier deal room** with explicit offers, risk rules, and repayment schedules before acceptance.

**Build implication:** Deal room + offer accept/reject (Phase 5) is a core product promise, not a nice-to-have.

---

### Problem 5 — Enterprise privacy vs blockchain transparency

**Today:** Firms avoid public chains because competitors could see commercial terms.

**Credara’s answer:** Sensitive trade documents in private storage; chain records **hashes and state transitions** only.

**Build implication:** UI shows proof receipts and explorer links, not raw commercial PDFs on-chain.

---

### Problem 6 — Fragmented counterparties (no single operating system)

**Today:** Supplier, buyer, financier, and compliance teams use different tools and email trails.

**Credara’s answer:** Four workspaces on one platform — SME, Buyer, Financier, Admin/Risk — with shared audit trail, invitations, and API/webhook integrations.

**Build implication:** Build the **circular workflow** (upload → verify → fund → settle → repay), not isolated dashboard pages.

---

### Who benefits

| Actor | Problem relieved |
|-------|------------------|
| **SME / supplier** | Cash sooner; clearer path to finance; reputational trade credit score |
| **Buyer** | Controlled confirmation; less fraud exposure; automated settlement when terms met |
| **Financier** | Verifiable collateral; lower underwriting friction; transparent offer terms |
| **Admin / risk** | KYB, disputes, suspicious proof, audit in one console |
| **Developer / integrator** | APIs and webhooks into ERP, logistics, and lender systems |

---

### Geographic focus (go-to-market, not code)

Credara is positioned for **UAE / DIFC trade corridors** (e.g. Jebel Ali supplier financing): high logistics volume, digital-asset regulatory ambition (VARA), and stablecoin settlement readiness. This shapes pilot design and narrative; it does not replace technical delivery.

---

### What Credara is **not** (honest scope)

- Not a replacement for courts and lawyers when disputes go off-chain
- Not live mainnet production today — relayer, KYB providers, and much UI wiring are still demo/sandbox
- Not fee-free finance — it aims to make fees **smaller, fairer, and visible earlier**

---

## Strategic considerations (before build)

Filtered from product/architecture reviews and external analysis. Use this to **prioritize**, not to expand scope blindly.

### High priority — adopt as build principles

| Consideration | Why it matters | Repo touchpoint |
|---------------|----------------|-----------------|
| **State in backend, not UI** | Enterprise trust; no “smoke and mirrors” | `docs/ARCHITECTURE.md`, `CODEBASE_REVIEW.md` |
| **Four-workspace loop** | Product is the full trade cycle, not four demos | README workspaces, standalone UI |
| **Proof bundle as trust bridge** | Core differentiation vs generic invoicing | `proofs.py`, `ProofRegistry.sol` |
| **Relayer + indexer** | Without real chain, “Polygon-powered” is marketing only | `simulate_tx_hash`, `apps/workers` |
| **Deal-room pricing transparency** | Supplier must see cost before accepting | `/deal-room/*`, `/risk-rules` |
| **Honest demo vs production** | Credibility with investors and pilots | README production controls list |
| **Dubai/UAE pilot narrative** | One corridor, three parties: SME + buyer + financier | Landing, `docs/PROCESS_FLOWS.md` |

**Pre-build checklist items to add:**
- [ ] One pilot corridor narrative written (e.g. Jebel Ali supplier shipment)
- [ ] One happy-path user story mapped to API routes (order → settle)
- [ ] Explicit “sandbox” labelling anywhere chain/KYB is simulated

---

### Medium priority — plan for, do not block Phase 0–4

| Consideration | When |
|---------------|------|
| **Logistics oracles** (GPS, carrier APIs, OTP handover) | Phase 5+; API shape exists |
| **Legal enforceability** (UCP 600, assignment, disputes) | Before real money custody; legal review |
| **Fiat–crypto abstraction** (AA, paymasters, custodial wallets) | Before mainstream SME onboarding in UAE |
| **Object storage for evidence files** | Before production document upload |
| **Webhook delivery worker + API key auth middleware** | Before developer integrations |
| **Alembic migrations** | Before multi-env deploy |
| **Auditor / regulator read-only views** | Phase 6 |

---

### Low priority — deprioritize for now

| Topic | Reason |
|-------|--------|
| Polygon CDK / AggLayer sovereign chains | Roadmap; not needed for first pilot |
| Zero-knowledge proofs for bundles | Hash anchoring sufficient for pilot |
| Industry comparables (Finastra, Polytrade, etc.) | GTM context only |
| “Backend is production-complete” framing | Overstated — many paths still simulated |
| ERC-1155 / 4337 on landing copy | Marketing; verify against actual contracts before claiming |

---

### Recommended build order (problem-driven)

Align UI and backend work with **solved problems**, not page count:

```text
1. Trade pipeline     → fraud reduction (verify before finance)
2. Settlement slice   → slow LC / payment friction
3. Real chain anchor  → verifiable proof receipts
4. Deal room + fees   → opaque/expensive finance
5. Logistics + KYB live → underwriting automation
6. UAE pilot          → one real corridor, three parties
```

UI port phases in this doc should follow that order. Landing parity (Phase 1) supports GTM but does not solve a user problem by itself.

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

## Hackathon / DIFC submission alignment

**Context:** UAE Polygon + DIFC hackathon — stablecoin payments, remittances, and trade finance. Prize pool rewards **on-chain readiness**, **technical excellence**, and **real-world UAE impact**.

This is not a reason to stop building Credara. It is the **scoring rubric** — use it to focus the MVP and submission narrative.

### Which problem track Credara fits

| Hackathon problem | Credara fit | Recommendation |
|-------------------|-------------|----------------|
| **#1 SME Trade Finance Is Broken** | **Primary fit** — tokenized receivables, Smart LCs, trade credit scoring on Polygon | **Lead with this** in problem statement, demo, and architecture |
| **#2 Merchant Payments / POS / AED retail** | **Weak fit** — Credara is B2B trade finance, not merchant POS or tourist wallets | Do **not** reposition as a POS product; mention stablecoin settlement as **corridor infrastructure** only |

Credara already names the hackathon’s exact asks for Problem #1:
- Tokenized receivables → `ReceivableRegistry`, `/trade/receivables`
- Smart contract LCs → `SmartLC.sol`, settlement/escrow APIs
- On-chain trade credit scoring → `CreditScoreAttestation`, `/finance/*`
- Jebel Ali / UAE corridor → landing, process docs, pilot narrative

### Judging criteria → what judges will test vs what you have

| Criterion | Credara strength today | Gap to close before submit |
|-----------|------------------------|----------------------------|
| **Innovation** | Proof bundles + multi-party verification + Smart LC escrow | Show **one novel flow** live, not 31 static pages |
| **Technical excellence** | Monorepo, contracts (OZ-hardened), bounded contexts, outbox pattern | **One real Amoy tx** on Polygonscan; relayer not `simulate_tx_hash` |
| **User experience** | Standalone UI is pitch-grade; React app is thinner | Runnable demo: sign up → trade → fund → **verifiable chain receipt** |
| **Real-world impact** | $2T gap, SME rejection, Jebel Ali TEU story matches brief | **3-party pilot story**: UAE supplier + buyer + financier with stablecoin settlement |
| **On-chain readiness** (rewards) | Contracts compile; Amoy in `.env.example` | Deployed contracts + live tx hashes in Proof Ledger |

### Submission pack mapping (Step 1 checklist)

| Required item | Credara source material |
|---------------|-------------------------|
| Team background | Your team doc (not in repo) |
| Problem statement | **Problem #1** — SME trade finance; UAE/Jebel Ali corridor |
| Target market | UAE/DIFC B2B suppliers, buyers, trade financiers (not retail merchants) |
| Technical architecture on Polygon | `docs/ARCHITECTURE.md`, contracts, relayer/indexer design |
| Launch roadmap | Phases in this doc + `security/deployment-readiness-checklist.md` |
| Revenue model | Platform/API fees, financier spread, SaaS for corridors (your GTM) |
| MVP / prototype | **Must demonstrate:** order → invoice → confirm → proof anchor → receivable → Smart LC fund/release with **Polygonscan link** |

### Stablecoin angle (connect to hackathon theme without pivoting)

The brief emphasizes AED stablecoins and PTSR-compliant acceptance. Credara’s honest positioning:

- **Today:** MockUSDC on Amoy for demo settlement (`MockUSDC.sol`, payment intents, escrow)
- **Pilot story:** Smart LC escrow settles in **regulated AED stablecoin** when buyer pays — Credara is the **workflow + proof layer**, not the POS
- **Do not claim:** Retail merchant acceptance, tourist wallets, or loyalty tokenization unless you build them

Bridge line for judges: *“Credara uses Polygon stablecoin rails to settle B2B trade once verified receivables and Smart LC conditions are met — the compliance-heavy half of UAE’s payment future.”*

### Minimum viable demo for judges (priority order)

What wins **Technical Excellence** + **On-chain readiness**:

1. **One real Polygon Amoy transaction** — proof anchor OR Smart LC fund (Polygonscan URL in UI)
2. **Live trade path** — create order + invoice in UI hitting real API (not seed data)
3. **Settlement path** — payment intent → escrow → ledger (partially exists; remove demo fallback)
4. **3-minute narrative** — Jebel Ali supplier, buyer confirms, financier advances, stablecoin escrow releases

What does **not** move the score much before submit:

- Full landing page parity
- All 31 workspace pages
- CDK / AggLayer roadmap slides without a live tx

### Honest risks in front of judges

| If judge asks… | Honest answer |
|----------------|---------------|
| “Is it on-chain?” | Contracts deployed on Amoy; relayer must show **real tx**, not SHA-256 simulation |
| “Is it production?” | Pilot-ready architecture; KYB/logistics/legal need partners |
| “Why not merchant POS?” | We solve **B2B trade finance**, not retail checkout — aligned to Problem #1 |
| “AED stablecoin?” | Settlement layer designed for AED stablecoin; demo uses MockUSDC on Amoy |

### Pre-submit gates (add to Phase 7 or hackathon sprint)

- [ ] Problem statement explicitly cites **Hackathon Problem #1** (SME trade finance)
- [ ] Demo video/script follows: invoice → verify → anchor → receivable → LC → stablecoin settlement
- [ ] At least **one Polygonscan transaction** linked from Proof Ledger or settlement UI
- [ ] Contracts deployed to Polygon Amoy with addresses in `.env`
- [ ] Team can explain UAE corridor (Jebel Ali) in under 60 seconds
- [ ] Application does **not** overclaim POS, remittance app, or live AED issuance

---

## Current status (update as work progresses)

| Phase | Status | Notes |
|-------|--------|-------|
| Pre-build gates | ⬜ Not started | Checklist created 2026-07-09 |
| Phase 0 | ⬜ Not started | |
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
