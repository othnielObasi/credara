# Credara Codebase Review

**Date:** 2026-07-07
**Scope:** `apps/api`, `contracts`, `apps/web` (including both standalone UI files: `credara-ui.html` and `apps/web/public/credara-enterprise-ui-v11.html`), `apps/workers`, `infra`, `packages/shared`
**Method:** four parallel read-only reviews (backend API, smart contracts, web app/UI, workers/infra). No files were modified as part of this review.

## Summary

Credara has real architectural breadth — an outbox-shaped audit trail, a KYB provider abstraction, RBAC, five hardened-looking contracts, four full workspace UIs. But three things a judge or reviewer is likely to test directly are currently simulated rather than real:

- **Money-movement endpoints in the API have no auth at all.**
- **The Polygon relayer never signs or sends a real transaction** — it hashes a string and calls it a tx hash.
- **The standalone UI runs on hardcoded demo data by default**, with live-backend calls wired in for only a handful of actions.

None of this requires a rewrite — the shapes are already there. It's a matter of finishing the wiring on a short, specific list of files.

**Totals:** 27 findings — 3 Critical, 6 High, 11 Medium, 7 Low — across four review areas, plus a solid-practices list per section below.

---

## Backend API (`apps/api`)

### Critical

**Money-movement endpoints have no auth**
`apps/api/app/api/v1/routers/real_workflow.py:218-871`
None of the payment-intent, escrow fund/release, wallet, or API-key routes carry `Depends(get_current_user)` or a role check. Anyone with the URL can create, fund, or release an escrow, or mint an API key, without a token.

**Pervasive IDOR — no tenant scoping**
`apps/api/app/api/v1/routes/finance.py:12-26`, `routes/trade.py` (create_invoice, create_receivable, submit_delivery_proof)
Role checks exist, but nothing ties a path/body `business_id`, `order_id`, or `invoice_id` to the caller's own business. Any SME can read a competitor's credit score or act on another SME's order by simply passing its ID.

### High

**KYB webhook accepts unsigned payloads**
`apps/api/app/api/v1/routes/kyb.py:33-37`, `modules/kyb/service.py:132`, `core/config.py:31`
`kyb_webhook_secret` is defined but never read anywhere. Since the mock provider derives its check ID deterministically from `business_id:legal_name`, a forged webhook call can flip any business straight to VERIFIED.

**KYB "provider abstraction" is fake for every real provider**
`apps/api/app/modules/kyb/providers/sumsub_provider.py`, `persona_provider.py`
These subclass the mock provider with no overrides. Setting `KYB_PROVIDER=sumsub` in production silently runs the same deterministic auto-approve/reject logic — no real identity check ever happens, with no guard to catch the misconfiguration.

**Outbox + Polygon relayer are simulated end to end**
`apps/api/app/services/polygon.py:11-14` (`simulate_tx_hash`), `routes/enterprise.py:1091,1115,1153,1173` — see also Workers & Infra below
`relayer_private_key` is declared in config but read nowhere in the codebase. Outbox rows are written with `status='sent'` at creation time rather than pending+dispatched, so every "on-chain" proof/receivable/tx reference on the Proof Ledger is a SHA-256 of a string, not a real Polygon transaction.

### Medium

**Idempotency doesn't replay the original response**
`apps/api/app/core/idempotency.py:6-12`, `models/audit.py:20`
A legit retry after a dropped response gets a bare 409 instead of the original result, and a genuine concurrent race hits the DB's `UniqueConstraint` as an unhandled `IntegrityError` → 500 rather than the intended 409.

**Unhandled None dereference on an invalid business ID**
`apps/api/app/api/v1/routes/businesses.py:33-38`
`verify_business` calls `db.get()` with no None check, so an unknown ID throws `AttributeError` → 500 instead of a 404.

**Audit log isn't actually immutable**
`apps/api/app/models/audit.py:8-16`
No DB trigger or ORM guard stops an UPDATE/DELETE on `AuditLog` rows — the "immutable audit trail" README claim is a naming convention, not an enforced property.

**"API workflow" test coverage doesn't exist**
`apps/api/tests/` (test_hashing.py, test_scoring.py, test_kyb.py only)
No `TestClient`/endpoint test exists anywhere — no coverage for auth, idempotency, proof-ledger, or outbox behavior, despite the README's "tests for hashing, scoring, and API workflows" claim.

### Low

**JWT secret has a live hardcoded fallback**
`apps/api/app/core/config.py:14`
If `JWT_SECRET` is unset at deploy time, the app boots and signs real tokens with the literal string `change-me-in-production`, silently.

**Settings/access router trusts a client-supplied role**
`apps/api/app/api/v1/routers/settings_and_access.py`
No auth dependency, and the route reads `{role}` straight from the path. Low real impact today since the backing data is static, but it sits right next to the unauth'd finding above as a pattern to break.

### Solid

- Canonical JSON hashing (sorted keys, Decimal/UUID/datetime handling) in `core/hashing.py` is clean and genuinely order-independent.
- `core/security.py`: bcrypt with a correct 72-byte guard, proper JWT iss/aud/exp validation, clean role-dependency composition.
- `record_audit` is consistently threaded through nearly every mutating enterprise endpoint with before/after diffs.
- Foreign-key and status columns are sensibly indexed across the model layer.

---

## Smart Contracts (`contracts/contracts`, Solidity 0.8.28, OZ 5.1)

### Critical

**One key holds verifier, resolver, and pauser for every LC**
`SmartLC.sol:92-95`, `SmartLCFactory.sol:41`, `contracts/scripts/deploy.ts:12-24`
The factory grants `msg.sender` — realistically one backend relayer address — `DEFAULT_ADMIN_ROLE`, `VERIFIER_ROLE`, `DISPUTE_RESOLVER_ROLE`, and `PAUSER_ROLE` on every deployed LC. Compromise that one key and an attacker can fabricate a delivery, verify it, and release escrowed funds across every outstanding LC with no counterparty involvement.

### High

**Disputes have no timeout — funds can lock permanently**
`SmartLC.sol:146-171`
Any party can call `dispute()` from Funded/DeliverySubmitted/DeliveryVerified, after which only the (single) resolver role can release or refund. A buyer disputing right after verification — specifically to block the permissionless deadline-refund path — combined with a lost resolver key leaves funds stuck indefinitely.

### Medium

**Receivables can be marked defaulted before maturity**
`ReceivableRegistry.sol:83-88`
`markDefaulted` has no check against `maturityDate`, so `SETTLER_ROLE` can flag a receivable as defaulted before it's even due.

**Contract test coverage is thinner than the audit checklist implies**
`contracts/test/*`
No test files exist at all for `SmartLCFactory`, `CreditScoreAttestation`, or `MockUSDC`. `SmartLC.test.ts` covers only the happy path plus one revert and one dispute-refund — missing role-restriction reverts and most non-happy-path transitions.

### Low

**MockUSDC.mint() is unrestricted**
`MockUSDC.sol:12`
Anyone can mint arbitrary amounts to any address. Expected for a testnet faucet — flagging only so the pattern isn't copied anywhere the token is treated as having real value.

**Non-standard ERC20 as settlement token would brick payouts**
`SmartLC.sol` (settlementToken usage throughout)
A fee-on-transfer or rebasing token would leave the contract unable to pay out its immutable `amount`, reverting `_release`/`_refund` permanently with no rescue function. Fine as long as only approved stablecoins are ever configured.

### Solid

- Correct checks-effects-interactions ordering on every fund/release/refund path, backed by `nonReentrant` and `SafeERC20` as defense in depth.
- `whenNotPaused` consistently applied across all five contracts' state-changing functions.
- No `tx.origin` usage; custom errors throughout instead of string reverts; immutable LC parameters prevent post-construction tampering.
- Proof-hash and duplicate-receivable uniqueness are correctly enforced on-chain.

---

## Web App & Standalone UI (`apps/web`, `credara-ui.html`, `apps/web/public/credara-enterprise-ui-v11.html`)

### High

**The UI runs on hardcoded demo data by default**
`apps/web/public/credara-enterprise-ui-v11.html` (initialState, realApi())
Nearly every workspace view reads and writes an in-memory `state` seeded from a large fake dataset (mock businesses, invoices, wallets, ledger rows). A `realApi()` helper does call the real backend, but only for ~7 specific actions (onboarding start, invite create/decision, settings save, API-key creation, one demo payment flow) and only once a user manually switches out of "local fallback mode." The demo looks live; by default, it isn't.

### Medium

**Next.js app is an iframe wrapper, not a dashboard**
`apps/web/app/page.tsx`, `app/workspace/page.tsx`, `app/layout.tsx`
Both pages render nothing but an `<iframe>` pointed at the static HTML file. There's no App Router data fetching, server logic, or React state anywhere in the Next.js layer — "enterprise dashboard" is currently a file server.

**The better landing page isn't the one being served**
`credara-ui.html` vs `apps/web/public/credara-enterprise-ui-v11.html`
The two files are byte-identical except for one block: the root `credara-ui.html` carries a newer "investor-grade" landing page (Investor Brief / Judge Mode / Evidence Pack sections, UAE/Jebel Ali narrative) that never made it into the file actually served from `public/`. Everything past the landing section — all workspace logic — is identical between the two.

**The real API client is dead code**
`apps/web/lib/api.ts`
Defines a full `apiGet`/`apiPost` client against `WEB_PUBLIC_API_BASE` with an endpoint map mirroring the real FastAPI routes — but it's never imported anywhere in `apps/web`.

### Low

**No semantic landmarks in the SPA shell**
`credara-enterprise-ui-v11.html`
Relies on `<section>`/`aria-label` throughout with no `<nav>`/`<header>`/`<main>` — minor, but worth a pass for screen-reader navigation.

**Auth form ships pre-filled with fake credentials**
`credara-enterprise-ui-v11.html` (login form)
Convenient for a demo, but worth removing or gating before anything resembling a public link goes out.

### Solid

- Broad, coherent workspace coverage — SME, Buyer, Financier, Admin, and Developer views share one consistent visual system.
- Fully self-contained: no external CDN scripts, no secrets embedded in client JS (the visible "API key" is masked demo data).
- The `realApi()` layer and live-status bar show a genuine, if partial, attempt at real backend integration rather than a pure mockup.
- Role-filtered navigation logic actually works client-side, matching the behavior described in `docs/ROLE_FILTERED_SETTINGS.md`.

---

## Workers & Infra (`apps/workers`, `infra`, `packages/shared`)

### High

**The relayer never touches the chain**
`apps/workers/src/relayer.py:16`, `apps/api/app/services/polygon.py:11-14`
`web3==7.6.1` is in requirements but never imported in `relayer.py`. There's no signing, no nonce tracking, and no RPC-failure handling — the only "transaction" produced is a SHA-256 hash of a string. The outbox polling loop and retry bookkeeping around it are legitimately well-built; they're just pointed at a fake sender.

### Medium

**No restart policy or healthchecks on api/worker/web**
`infra/docker-compose.yml`
Only Postgres has a healthcheck; a crash in the API, worker, or web container won't recover without a manual `docker compose up`, and Redis has no health-gated dependency either.

**Shared schema file is unused**
`packages/shared/domain.json`
No reference to this file or its contents appears anywhere in apps/api, apps/web, apps/workers, or contracts — the FastAPI enums duplicate similar concepts independently in Python instead. Reads as a planned artifact that never got wired in.

### Low

**`make zip` points at a path that doesn't exist**
`Makefile:16-17`
References `/mnt/data/credara-enterprise` — a Linux-only path and a directory name that doesn't match this repo (`credara`). Stale, copy-pasted tooling that will fail as written.

### Solid

- The outbox DB schema (AuditLog, IdempotencyKey, BlockchainOutbox) is a clean, sensible shape — it just needs a real sender behind it.
- `.env.example` and `core/config.py` are well-aligned in naming and defaults.
- Postgres persistence and healthcheck in compose are done correctly.
- `make dev` / `make test` / `make lint` (everything but `make zip`) match the actual repo layout.

---

## Before you submit

Ranked by what a judge is likely to actually test — a live transaction, a real login, a second business's data staying private — against how much work each fix is.

| Priority | Fix | Why it matters here | Effort |
|---|---|---|---|
| P1 | Add auth + business-ID ownership checks to `real_workflow.py`, `finance.py`, and `trade.py` | Closes the unauthenticated-escrow and cross-tenant IDOR findings — the two most exploitable issues in the review | Medium |
| P1 | Make one real signed Polygon Amoy transaction work end to end (proof anchor or LC fund), replacing `simulate_tx_hash` | Highest-leverage fix for "technical excellence" — judges can verify a real tx on PolygonScan; a hashed string can't survive that check | Medium–High |
| P1 | Point the standalone UI's core demo flow at the real API by default instead of local-fallback mode | The README's 8-step Polygon demo flow needs to actually hit the backend live, not just look like it does | Medium |
| P2 | Separate the SmartLC verifier/resolver/pauser roles, or document the multisig plan explicitly in submission materials | Directly addresses the single-key blast-radius finding without redesigning the contracts | Low–Medium |
| P2 | Add a dispute-resolution timeout / fallback path | Removes the permanent-fund-lock scenario | Medium |
| P2 | Verify KYB webhook signatures; label unimplemented providers honestly instead of silently mocking | Closes a real forgeable-verification path and an honesty gap in the KYB story | Low–Medium |
| P3 | Pick one landing page (root file has the better pitch content) and delete the other; wire up or delete `apps/web/lib/api.ts` | Cleanup — avoids judges finding an abandoned, better version of the pitch sitting unused in the repo | Low |
| P3 | Add compose healthchecks/restart policies; fix or remove `make zip`; wire or delete `domain.json` | Polish — none of these block a demo, but they're quick to fix during a cleanup pass | Low |
