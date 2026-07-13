# Credara Enterprise

Credara is an enterprise-grade SME trade-finance infrastructure platform for tokenized receivables, smart contract letters of credit, proof-backed settlement, and trade credit scoring on Polygon.

The repository is intentionally structured as a monorepo so the web app, API, workers, smart contracts, shared schemas, and documentation evolve together.

## Product scope

Credara supports four operating workspaces:

- SME workspace: orders, invoices, delivery proof, receivables, finance readiness, trust/credit score.
- Buyer workspace: supplier verification, invoice confirmation, delivery confirmation, dispute handling.
- Financier workspace: verified receivables, credit review, financing offers, smart LC funding, repayment tracking.
- Admin/Risk workspace: KYB review, suspicious proof review, dispute resolution, audit trail.

## Architecture

```text
apps/web             Next.js enterprise dashboard
apps/api             FastAPI backend API
apps/workers         Relayer, indexer, proof, scoring workers
contracts            Solidity contracts for Polygon Amoy/PoS
packages/shared      Shared schemas, API contracts and domain enums
docs                 BRD, technical spec and implementation runbooks
infra                Docker Compose, deployment and local infra
```

## Quick start

```bash
cp .env.example .env   # or: make setup-env
bash scripts/dev-local.sh api   # terminal 1
bash scripts/dev-local.sh web   # terminal 2
```

Or with Docker: `make dev`

### Production deploy (Vercel)

Use these projects (not the legacy stuck `credara` project):

| App | Vercel project | Root directory | URL |
|-----|----------------|----------------|-----|
| Web | `credara-jet` | `apps/web` | https://credara-jet.vercel.app/ |
| API | `credara-api` | `apps/api` | https://credara-api.vercel.app/ |

API health: https://credara-api.vercel.app/health  
API docs: https://credara-api.vercel.app/docs  

**Auth0 (required for OAuth):** Allowed Callback URL  
`https://credara-api.vercel.app/api/v1/auth/oauth/callback`  
Allowed Logout/App URLs: `https://credara-jet.vercel.app`

**Production notes:**
- Demo `/api/v1/payments/*` routers are **disabled** when `ENVIRONMENT=production` (use `/api/v1/real/*`).
- Set `CRON_SECRET` on the API project so Vercel Cron can drain the blockchain outbox (Hobby: once daily at 12:00 UTC; Pro: raise frequency in `apps/api/vercel.json`). External cron may POST/GET `/api/v1/internal/relayer/drain` with `Authorization: Bearer $CRON_SECRET`.
- KYB: set `KYB_PROVIDER=didit` with Didit credentials, or explicitly `ALLOW_MOCK_KYB=true` for sandbox.
- Smoke test: `python scripts/e2e_production_smoke.py`

Local Docker (optional): `make deploy-production`

API docs (local): http://localhost:8000/docs  
Web app (local): http://localhost:3000

## Local development without Docker

```bash
make setup-env          # once: creates .env
bash scripts/dev-local.sh api   # terminal 1
bash scripts/dev-local.sh web   # terminal 2
```

Open **http://localhost:3000/** — sign up to create a live workspace.

```bash
cd contracts
npm install
npm run compile
npm test
```

## Polygon demo flow

1. Deploy `MockUSDC`, `ProofRegistry`, `ReceivableRegistry`, `SmartLCFactory`, `CreditScoreAttestation` to Polygon Amoy.
2. Create an SME, buyer, invoice, delivery proof and proof bundle through the API.
3. Anchor the proof bundle with the relayer worker.
4. Create a receivable from the buyer-confirmed invoice.
5. Create/fund a smart LC using mock USDC.
6. Verify delivery and release settlement.
7. Update and anchor the SME trade credit score.
8. Show transaction references in the Proof Ledger.

## Production controls included

- Modular bounded contexts.
- Role-aware access checks.
- Immutable audit log model.
- Outbox pattern for blockchain relayer safety.
- Idempotency-key support for write endpoints.
- Deterministic proof hashing.
- Trade credit scoring service separated from API handlers.
- Contract pause/role/reentrancy controls.
- Dockerized API, web, worker, Postgres and Redis.
- Tests for hashing, scoring, and API workflows.

## Production controls to complete before real deployment

- Replace demo auth with production IdP/OIDC.
- Complete KYB provider integration.
- Replace mock USDC with approved production stablecoin flow.
- Independent Solidity audit.
- Legal review for receivable assignment and LC enforceability.
- Mainnet deployment, monitoring, alerting and incident runbooks.

## Process Flow Documentation

Credara includes full enterprise process-flow documentation for implementation and review:

- `docs/PROCESS_FLOWS.md` — detailed end-to-end business and technical flows.
- `docs/PROCESS_FLOW_DIAGRAMS.md` — Mermaid diagrams for key flows.
- `docs/PROCESS_FLOW_IMPLEMENTATION_CHECKLIST.md` — build and readiness checklist.

These flows cover identity, KYB, orders, invoices, delivery proof, proof anchoring, receivables, smart LCs, financier review, credit scoring, disputes, blockchain relayer/indexer, developer APIs, admin risk review, and the hackathon demo flow.


## Enterprise Workflow Backend Upgrade

The backend now includes the expanded multi-user workflow needed to match the enterprise UI: Buyer Inbox, Logistics Verification, Financier Deal Room, Repayments, Evidence Bundles, API Explorer support, Risk Rules, Permissions Matrix, Smart LC lifecycle actions, and Credit Score Attestation. See `docs/ENTERPRISE_WORKFLOW_BACKEND.md` for endpoint details and production notes.

## v5 Network Discovery and Trade Market Layer

This version adds the pre-transaction network layer required for a complete enterprise trade finance product:

- Business Directory for verified buyers, sellers, financiers and logistics providers.
- Counterparty Invitations for private, relationship-based trade workflows.
- Trade Contracts that can be created directly, by invite, or from accepted seller proposals.
- Trade Opportunities for buyer-posted demand discoverable by verified sellers.
- Seller Proposals for quotes, terms and contract conversion.
- Financier Marketplace for discovering finance-ready receivables.

Implementation docs:

- `docs/NETWORK_DISCOVERY_IMPLEMENTATION.md`
- `docs/NETWORK_DISCOVERY_API.md`
- `docs/UI_NETWORK_DISCOVERY_UPDATE.md`


## Contract and Invoice Operating Records

v6 adds rich contract/invoice detail APIs and downloadable contract/invoice HTML documents. See `docs/CONTRACT_INVOICE_OPERATING_RECORDS.md`.


## Payments, Wallets, Escrow and Settlement Ledger

v7 adds wallet/payment intent, Smart LC escrow, settlement ledger reporting, role reports, admin aggregate reporting and reconciliation APIs. See `docs/PAYMENTS_ESCROW_LEDGER.md`.


## Feature Structure and Noise Reduction

v8 separates core product features from supporting tools and demo controls. See `docs/FEATURE_STRUCTURE_AND_NOISE_REDUCTION.md`.


## Onboarding and Invitation Flows

v9 adds business onboarding, invitations, role routing, members, and setup checklist APIs. See `docs/ONBOARDING_AND_INVITATIONS.md`.


## Role-Filtered Navigation and Settings

v10 filters pages by selected role and moves API/platform controls into Settings. See `docs/ROLE_FILTERED_SETTINGS.md`.


## v12 Enterprise UI

The runnable app is the **Credara Next.js workspace** at `http://localhost:3000/` (`apps/web`).

The old standalone HTML demo has been archived to `docs/archive/` for reference only — it is **not** the product UI. Do not open `credara-ui.html` directly; use the Next.js app.


## Real Workflow Wiring

v11 adds persistent onboarding, invitations, settings, API keys, webhooks, wallets, payment intents, escrow, settlement ledger and reconciliation APIs. See `docs/REAL_WORKFLOW_WIRING_V11.md`.
