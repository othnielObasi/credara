# Judge demo script — 60 seconds to aha

Use this **before** architecture slides. Open on **live Polygonscan release**, then run Judge Mode.

---

## 60-second pitch (say this)

> Jebel Ali suppliers ship goods but wait **45–90 days** to get paid. Banks take **7–10 days** just to process a letter of credit — and reject **~40%** of SME applications.
>
> Credara turns **buyer-confirmed invoices + delivery proof** into **finance-ready receivables**, anchors trust on **Polygon**, and settles through **Smart LC stablecoin escrow**.
>
> This is **B2B trade settlement** for the UAE corridor — not remittance, not POS. **PTSR-ready** when a licensed AED stablecoin partner is live.
>
> Here’s the climax — **real money released on Amoy** after verified delivery.

**Then open:** [Smart LC release tx](https://amoy.polygonscan.com/tx/0x5743a885e54063da6c4056d73e4b49113918558fd09d8973c9074de8e57af9de)

---

## 3-minute live demo

| Step | Role | Action |
|------|------|--------|
| 0 | — | [credara-jet.vercel.app/workspace](https://credara-jet.vercel.app/workspace) |
| 1 | **SME** | Sign up (or sign in) · **Judge demo mode** on (default) |
| 2 | **SME** | New trade → invoice → delivery proof |
| 3 | **Buyer** | Switch role · confirm invoice in Buyer Inbox |
| 4 | **SME** | Receivable → **anchor proof** → confirm **Anchored** + Polygonscan link |
| 5 | **Financier** | Deal room → **fund Smart LC** |
| 6 | **All** | Settlement → **release** → point at explorer link |

**Climax lines in the UI:** Judge banner links to verified release + proof anchor txs.

---

## Verified on-chain proof (backup if live demo hiccups)

| Event | Polygonscan |
|-------|-------------|
| Proof anchor | [0x71b1d6c7…f251](https://amoy.polygonscan.com/tx/0x71b1d6c74b30033b7f3ab1cad174bf75cf2003fce593dd8c7e04aa3964acf251) |
| Smart LC release | [0x5743a885…f9de](https://amoy.polygonscan.com/tx/0x5743a885e54063da6c4056d73e4b49113918558fd09d8973c9074de8e57af9de) |

---

## Demo reliability checklist

- [ ] Sign in with **email/password** (backup if Auth0 slow)
- [ ] OAuth must start on **API host**: `credara-api.vercel.app/api/v1/auth/oauth/login`
- [ ] After anchor/fund/release, status must show **Anchored** — not Simulated
- [ ] Pitch deck slide 2 = **Aha moment** (release tx screenshot)

---

## One trade story (investors)

> **AED 250k** Jebel Ali textile invoice → **80% advance** → financier funds Smart LC **same afternoon** → **MockUSDC released** to seller after delivery verified on Polygon.

---

*Deck: `docs/Credara_Pitch_Deck.pptx` · Submission: `docs/SUBMISSION.md`*
