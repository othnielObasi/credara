# Judge readiness plan — push Credara toward 9–10/10

Target: win a Polygon/UAE payments-style panel as **SME trade-finance infrastructure**, not as a remittance app.

Overall today: **~6.5/10**. After this plan: **~8.5–9/10** (Impact tops out unless judges accept B2B trade payments as the pitch).

## Positioning (lock this)

> Credara is Polygon-native SME trade finance for the UAE corridor: buyer-confirmed invoices and delivery proofs become finance-ready receivables, settled via Smart LC stablecoin escrow — not remittance, POS, or a consumer wallet.

Demo climax: **live Amoy proof anchor → Polygonscan**.

## P0 — must ship for judging

| # | Fix | Owner surface | Status |
|---|-----|---------------|--------|
| 1 | Fail-closed chain writes: no fake Polygonscan links; `on_chain=false` → Simulated / not Anchored | API `polygon.py`, `proofs.py`, `proof_ledger.py`, enterprise LC actions; web Proof Ledger UI | Done |
| 2 | Judge Mode: 3-minute nav (invoice → confirm → proof → receivable → Smart LC) | `credara-live-app.tsx` | Done |
| 3 | Pitch lock + this doc | `docs/JUDGE_READINESS_PLAN.md` | Done |
| 4 | One real Amoy tx (deploy contracts, set env, fund relayer) | Ops / Vercel env | Manual — blocked on keys |
| 5 | Prod honesty: `ENVIRONMENT=production`, Didit or no mock KYB, Auth0 callbacks | Vercel + Auth0 | Manual |

### Judge Mode path (script)

1. **SME** — create order → invoice → delivery proof  
2. **Buyer** — confirm order/invoice  
3. **SME** — create receivable → anchor proof (show Polygonscan if live)  
4. **Financier** — review receivable / deal room → fund Smart LC  
5. **Release** — settlement when conditions met  

### Amoy checklist (ops)

1. Deploy `ProofRegistry`, `ReceivableRegistry`, `SmartLCFactory`, `MockUSDC`, `CreditScoreAttestation` to Amoy  
2. Set on API: `RELAYER_PRIVATE_KEY`, `PROOF_REGISTRY_ADDRESS`, `SMART_LC_FACTORY_ADDRESS`, `MOCK_USDC_ADDRESS`, `POLYGON_RPC_URL`, `POLYGON_CHAIN_ID=80002` (grant factory `CREATOR_ROLE` to the relayer)  
3. Fund relayer with Amoy POL  
4. Anchor once from UI → confirm tx on https://amoy.polygonscan.com  
5. Create → fund → release a Smart LC and confirm factory / LC txs on Polygonscan  

## P1 — same week

| # | Fix | Status |
|---|-----|--------|
| 6 | AED / Mock USDC currency consistency (drop £ in landing/demo) | Done (landing) |
| 7 | Wire Smart LC fund/release to real factory calls | Done — `smart_lc_chain.py` + trade/enterprise routes |
| 8 | One slide: MockUSDC today → regulated AED stablecoin for B2B settlement | Done — `docs/PITCH_STABLECOIN_CORRIDOR.md` |
| 9 | Hide Advanced nav behind Judge Mode off | Covered by #2 |

## P2 — if time

| # | Fix | Status |
|---|-----|--------|
| 10 | Slither + contract coverage in CI | Done — `.github/workflows/contracts.yml` |
| 11 | A11y/mobile pass on judge path | Pending |
| 12 | Related-opportunity footnote only (no fake remittance MVP) | Done — pitch + submission footnote |

## Score impact

| Criterion | Now | After P0–P1 |
|-----------|-----|-------------|
| Innovation | 6.5 | ~8.5 |
| Technical Excellence | 7.0 | ~9 |
| User Experience | 6.5 | ~8.5–9 |
| Real-World Impact | 5.5 | ~7.5–8 |
| **Overall** | **6.5** | **~8.5–9** |

## Explicit non-goals

- Do **not** build consumer remittance or POS to chase the $50B remittance wording.  
- Do **not** claim AED issuance — claim **settlement readiness** only.  
- Do **not** show explorer links for simulated hashes.
