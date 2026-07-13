# Credara

**Polygon-native SME trade finance for the UAE corridor.**

Buyer-confirmed invoices and delivery proofs become finance-ready receivables, settled with programmable Smart LC stablecoin escrow — not remittance, POS, or a consumer wallet.

Demo climax: **live Polygon Amoy proof anchor → Polygonscan.** Pitch: MockUSDC today → regulated AED stablecoin for B2B settlement tomorrow ([pitch notes](docs/PITCH_STABLECOIN_CORRIDOR.md)).

---

## Live product

| Surface | URL |
|---------|-----|
| Web workspace | [https://credara-jet.vercel.app](https://credara-jet.vercel.app) |
| API health | [https://credara-api.vercel.app/health](https://credara-api.vercel.app/health) |
| API docs | [https://credara-api.vercel.app/docs](https://credara-api.vercel.app/docs) |

**Judge Mode (≈3 minutes):** open Workspace → enable **Judge demo mode** → walk invoice → buyer confirm → delivery proof → receivable → anchor (Polygonscan when live) → Smart LC fund → release.

Detailed checklist: [docs/JUDGE_READINESS_PLAN.md](docs/JUDGE_READINESS_PLAN.md) · Submission draft: [docs/SUBMISSION.md](docs/SUBMISSION.md)

---

## What Credara does

Four role workspaces on one shared, verified trade record:

| Workspace | Outcomes |
|-----------|----------|
| **SME** | Orders, invoices, delivery proof, receivables, finance readiness, trade credit score |
| **Buyer** | Confirm obligation, confirm delivery, raise disputes |
| **Financier** | Review verified receivables, fund Smart LCs, track settlement |
| **Admin / Risk** | KYB review, proof scrutiny, disputes, audit trail |

**On-chain suite (Polygon Amoy):** `ProofRegistry`, `ReceivableRegistry`, `SmartLCFactory` / `SmartLC`, `CreditScoreAttestation`, `MockUSDC` (demo settlement asset).

---

## Production architecture

```text
apps/web        Next.js 15 workspace + marketing
apps/api        FastAPI (Postgres, JWT + Auth0, Didit KYB, Amoy writes)
apps/workers    Relayer / indexer / scoring (Compose / outbox drain)
contracts       Hardhat + Solidity 0.8.28 (CI: test + Slither)
docs            Specs, judge plan, process flows
infra           Docker Compose
```

| Concern | Approach |
|---------|----------|
| Auth | Password sessions + Auth0 authorization-code (server-brokered) |
| KYB | Provider abstraction (`KYB_PROVIDER=didit` in production) |
| Data | Postgres (Neon on Vercel); role-scoped API access |
| Chain honesty | Fail-closed: no fake explorer links; `on_chain=false` shows **Simulated** |
| Relayer | Outbox + cron drain (`CRON_SECRET`); Smart LC create/fund/release via factory |
| Contracts CI | [`.github/workflows/contracts.yml`](.github/workflows/contracts.yml) |

---

## Production deploy (Vercel)

| App | Project | Root | Production URL |
|-----|---------|------|----------------|
| Web | `credara-jet` | `apps/web` | https://credara-jet.vercel.app |
| API | `credara-api` | `apps/api` | https://credara-api.vercel.app |

GitHub → Vercel auto-deploy with those root directories. CLI deploy from the monorepo root (project Root Directory must match).

### Required environment (API)

Copy from [`.env.example`](.env.example). Production must include:

```text
ENVIRONMENT=production
DATABASE_URL / Neon vars
JWT_SECRET                    # never leave the example default
CORS_ORIGINS                  # include https://credara-jet.vercel.app
RELAYER_PRIVATE_KEY
POLYGON_CHAIN_ID=80002
POLYGON_RPC_URL
PROOF_REGISTRY_ADDRESS
RECEIVABLE_REGISTRY_ADDRESS
SMART_LC_FACTORY_ADDRESS
MOCK_USDC_ADDRESS
CREDIT_SCORE_ATTESTATION_ADDRESS
KYB_PROVIDER=didit            # + Didit secrets
AUTH0_DOMAIN / CLIENT_ID / CLIENT_SECRET
AUTH0_CALLBACK_URL=https://credara-api.vercel.app/api/v1/auth/oauth/callback
AUTH0_FRONTEND_REDIRECT=https://credara-jet.vercel.app/auth/callback
CRON_SECRET
```

Do **not** set `ALLOW_SIMULATED_CHAIN=true` in production unless you intentionally want soft failures without live chain.

### Required environment (Web)

```text
NEXT_PUBLIC_API_BASE=/api/v1
API_PROXY_TARGET=https://credara-api.vercel.app
NEXT_PUBLIC_API_ORIGIN=https://credara-api.vercel.app   # Auth0 must start on API host (state cookie)
```

### Auth0 application URLs

| Setting | Value |
|---------|--------|
| Allowed Callback URLs | `https://credara-api.vercel.app/api/v1/auth/oauth/callback` |
| Allowed Logout URLs | `https://credara-jet.vercel.app`, `…/workspace`, `…/login` |
| Allowed Web Origins | `https://credara-jet.vercel.app` |

OAuth login must hit the **API origin** (`…/api/v1/auth/oauth/login`) so the state cookie and callback share a host.

### Production guardrails

- Demo/in-memory `/payments/*` routers are **off** when `ENVIRONMENT=production`.
- Cron drains the blockchain outbox (`apps/api/vercel.json`); Bearer `CRON_SECRET`.
- Smoke: `python scripts/e2e_production_smoke.py`

---

## Local development

```bash
cp .env.example .env          # or: make setup-env
bash scripts/dev-local.sh api # terminal 1
bash scripts/dev-local.sh web # terminal 2
```

- Web: http://localhost:3000  
- API docs: http://localhost:8000/docs  
- Docker (optional): `make dev`

```bash
cd contracts && npm ci && npm test
```

Relayer must hold factory `CREATOR_ROLE` for live Smart LC deploys. Amoy Polarscan: https://amoy.polygonscan.com

---

## Judge demo flow (business)

1. **SME** — order → invoice → delivery proof  
2. **Buyer** — confirm order / invoice  
3. **SME** — receivable → **anchor proof** (live tx when relayer configured)  
4. **Financier** — fund Smart LC  
5. **Release** — settlement after verified delivery  

Today’s settlement asset is **MockUSDC** on Amoy; rails are ERC-20-token-agnostic for a future CBUAE-aligned AED stablecoin ([corridor pitch](docs/PITCH_STABLECOIN_CORRIDOR.md)).

---

## Documentation map

| Doc | Purpose |
|-----|---------|
| [docs/JUDGE_READINESS_PLAN.md](docs/JUDGE_READINESS_PLAN.md) | Judge criteria & checklist |
| [docs/PITCH_STABLECOIN_CORRIDOR.md](docs/PITCH_STABLECOIN_CORRIDOR.md) | MockUSDC → AED talk track |
| [docs/SUBMISSION.md](docs/SUBMISSION.md) | Hackathon submission draft |
| [docs/PROCESS_FLOWS.md](docs/PROCESS_FLOWS.md) | End-to-end business/technical flows |
| [docs/ENTERPRISE_WORKFLOW_BACKEND.md](docs/ENTERPRISE_WORKFLOW_BACKEND.md) | Enterprise workflow APIs |
| [docs/NETWORK_DISCOVERY_API.md](docs/NETWORK_DISCOVERY_API.md) | Directory / marketplace APIs |

Older feature-series notes (v5–v12, payments/escrow wiring, onboarding) remain under `docs/` for implementers; they are not required for judging.

---

## Production maturity

**In place:** role-aware APIs, Auth0 + password auth, Didit KYB path, audit log, idempotency keys, deterministic proof hashing, fail-closed chain UX, Smart LC factory wiring, outbox + cron, contract tests + Slither CI, Vercel dual-project deploy.

**Before regulated mainnet:** independent Solidity audit, legal review of receivable assignment / LC enforceability, licensed AED (or other) settlement asset, mainnet monitoring and incident runbooks.

---

## License / team

Private monorepo for Credara Enterprise. Fill team bios in [docs/SUBMISSION.md](docs/SUBMISSION.md) before formal submission.
