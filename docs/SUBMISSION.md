# Credara — Smart Commerce Infrastructure Challenge Submission

**Positioning (locked):** Credara is Polygon-native SME trade-finance infrastructure for the UAE corridor: buyer-confirmed invoices and delivery proofs become finance-ready receivables, settled via Smart LC stablecoin escrow. This is **B2B trade settlement**, not remittance, POS, or a consumer wallet.

**Live demo:** [credara-jet.vercel.app/workspace](https://credara-jet.vercel.app/workspace) · API: [credara-api.vercel.app/docs](https://credara-api.vercel.app/docs)

---

## 1. Team background and technical credentials

Credara is built by **Othniel Obasi**, founder of NOVTIA Ltd (London), an AI governance and infrastructure company, with a decade of enterprise product leadership spanning:

- **Digital banking** — Creditville MFBank platform turnaround (40K → 100K+ users).
- **Utilities enterprise transformation** — PHED, 5M+ customers, $96M+ revenue growth delivered over a 6-year transformation.
- **AI governance and runtime infrastructure** — architect of AIRG (AI Runtime Governor), a proprietary policy-engine governance control plane with a cryptographic receipt chain (SURGE v2), now applied to Credara's proof-anchoring and evidence model.
- **Trade finance / fintech infra build track record** — Credara sits alongside a portfolio of enterprise-grade hackathon and production builds (NorthBridge FraudOps, Kairos on Arc, ProofSource, Autonix), each shipped as full-stack systems with real test coverage, not prototypes.

This cross-domain background — regulated banking operations, large-scale utilities transformation, and cryptographic governance infrastructure — is the direct technical basis for Credara's evidence-first, fail-closed approach to on-chain settlement.

---

## 2. Problem statement and target market

Over **USD 2 trillion** in global trade finance demand goes unfilled. **~40%** of SME trade-finance applications are rejected, and traditional letters of credit take **7–10 days** of manual processing — friction that falls hardest on SMEs trading through high-volume corridors like **Jebel Ali Port (15M+ TEUs/year)**.

**Target market:** SMEs, buyers, financiers, and logistics partners operating in UAE B2B trade corridors, plus the banks and non-bank financiers who currently reject or slow-walk SME receivables financing because verification is manual and trust is hard to price.

Credara's wedge is deliberately narrow: **not** the full USD 50B UAE remittance/payments market, but the **SME trade-finance slice** of it — verified receivables and stablecoin-settled Smart LCs.

*Related opportunity (footnote only):* remittance apps could later consume the same proof/settlement APIs; Credara does not ship a consumer remittance MVP.

---

## 3. Technical architecture and approach on Polygon

Credara is a monorepo spanning app, backend, workers, and contracts so proof, settlement, and scoring evolve together:

```text
apps/web        Next.js enterprise dashboard (SME / Buyer / Financier / Admin-Risk)
apps/api        FastAPI backend (Postgres, JWT, Auth0, Didit KYB, Amoy writes)
apps/workers    Relayer, indexer, proof, scoring workers
contracts       Solidity 0.8.28 (Polygon Amoy / PoS-ready)
docs            Architecture, process flows, judge plan
```

**On-chain layer (Polygon Amoy today, PoS-ready):**

| Contract | Role |
|----------|------|
| `MockUSDC` | Demo settlement token (`IERC20`; swap for CBUAE PTSR AED stablecoin without changing escrow logic) |
| `ProofRegistry` | Anchors deterministic hashes of invoice/delivery proof bundles |
| `ReceivableRegistry` | Buyer-confirmed invoices as finance-ready receivables |
| `SmartLCFactory` / `SmartLC` | Escrow: create → fund → verify delivery → release / dispute / refund |
| `CreditScoreAttestation` | On-chain SME trade credit score snapshots |

**Design principles (shipped, not aspirational):**

- **Fail-closed chain writes** — if a tx isn't on-chain, the UI shows **Simulated / not Anchored**; no fabricated Polygonscan links (`ALLOW_SIMULATED_CHAIN` off in production).
- **Off-chain evidence, on-chain anchors** — commercial documents stay private; only hashes and settlement state move on-chain.
- **Outbox + relayer/cron drain**, **idempotency keys**, **deterministic proof hashing**, **AccessControl / Pausable / ReentrancyGuard** on contracts; **Slither in CI**.
- **Role-aware multi-tenant access** (SME / Buyer / Financier / Admin-Risk), audit-logged end to end.
- **Auth0 OAuth + password JWT** (server-brokered authorization-code flow); **Didit KYB** via provider abstraction (`mock` gated in production).
- **Smart LC factory wiring** — `smart_lc_chain.py` calls real `createSmartLC`, `fund()`, `submitDelivery` → `verifyDelivery` → `release` when relayer env is set.

**Demo climax:** live Amoy proof anchor on Polygonscan, walked through **Judge Mode** (~3 min): SME order → invoice → delivery proof → buyer confirm → receivable + anchor → financier funds Smart LC → release on verified delivery.

Pitch slide (MockUSDC → AED corridor): [docs/PITCH_STABLECOIN_CORRIDOR.md](PITCH_STABLECOIN_CORRIDOR.md)

---

## 4. Launch roadmap and go-to-market strategy

**Now — Amoy testnet demo (shipped):** full lifecycle on Polygon Amoy with MockUSDC; Judge Mode; contracts tested + Slither in CI; dual Vercel deploy (`credara-jet` / `credara-api`).

**Near-term (production readiness):**

- Harden Auth0 + enterprise SSO policies (Auth0 is live today; expand org/role claims for bank pilots).
- Production KYB on Didit (configured; ensure `KYB_PROVIDER=didit` and mock KYB off in prod).
- Swap MockUSDC for a **CBUAE PTSR-compliant AED stablecoin** from a licensed issuer — same factory, escrow roles, proof conditions.
- Independent Solidity audit; legal review of receivable assignment and Smart LC enforceability under UAE/DIFC law.
- Polygon mainnet + monitoring / incident runbooks.

**Go-to-market:** pilot with a small cohort of UAE SMEs in Jebel Ali-linked supply chains plus 1–2 non-bank financiers; use DIFC / challenge ecosystem access (banks, VCs, mentors) to land financier demand first — financiers pull SME supply. Prove **7–10 day LC friction collapsed to same-day proof-to-funding** in one corridor before expanding.

---

## 5. Revenue model and scalability plan

| Stream | Mechanic |
|--------|----------|
| **Financing origination** | Fee on receivables funded via Smart LC marketplace (financier or SME at draw-down) |
| **Platform / SaaS** | Tiered fees for buyers/financiers using verification, deal room, reporting |
| **Settlement / escrow** | Basis-point fee per Smart LC fund/release vs. multi-day LC handling |
| **Credit scoring as a service** | Trade credit attestations via API for external lenders |

**Scalability:** bounded contexts, outbox relayer, multi-tenant RBAC, and token-agnostic escrow — new corridors or stablecoins are largely **issuer + `IERC20` address** configuration, not a rebuild. API-first design lets third parties integrate without using Credara's UI.

*Tighten unit economics with Othniel before final submission — illustrative ranges in prior drafts are strategic, not committed pricing.*

---

## 6. MVP / Prototype

**Live and testable today:**

- Next.js enterprise dashboard — four workspaces (SME, Buyer, Financier, Admin/Risk) on one shared verified record.
- FastAPI backend — orders, invoices, delivery proof, receivables, Smart LC lifecycle, KYB, deal room, proof ledger, settlement views, admin/audit.
- Contracts on Polygon Amoy (`MockUSDC`, `ProofRegistry`, `ReceivableRegistry`, `SmartLCFactory`, `CreditScoreAttestation`); relayer env on Vercel when configured.
- End-to-end: order → invoice → delivery proof → proof anchor (Polygonscan when live) → receivable → Smart LC fund → verified-delivery release → credit score path.

**Judge script:** [README.md](../README.md#start-here-judges--reviewers) · Checklist: [JUDGE_READINESS_PLAN.md](JUDGE_READINESS_PLAN.md)

**Pre-submit ops (confirm before judging):**

1. Relayer funded on Amoy; one proof anchor + one Smart LC cycle visible on Polygonscan.
2. `ENVIRONMENT=production`, Auth0 callback URLs, `NEXT_PUBLIC_API_ORIGIN` on web, Didit KYB in prod.
3. OAuth starts on **API host** (`credara-api…/auth/oauth/login`) so state cookie matches callback.

**Explicit non-goals:** no consumer remittance MVP, no POS, no claim of issuing AED — only settlement-readiness for a regulated AED stablecoin on the same rails.

---

*Architecture diagrams and flows: [README.md](../README.md) · Full process spec: [PROCESS_FLOWS.md](PROCESS_FLOWS.md)*
