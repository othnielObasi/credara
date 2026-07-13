# Pitch notes — MockUSDC → AED B2B settlement corridor

**One slide.** Use this verbatim on judging day.

---

## Headline

**Today: MockUSDC on Amoy. Tomorrow: regulated AED stablecoin for B2B settlement — same Smart LC rails.**

## Body (talk track, ~45 seconds)

Credara settles verified SME trades through programmable Smart LC escrow on Polygon.

- **What you see in the demo** — escrow is funded and released in MockUSDC on Polygon Amoy. That is intentional: it proves the contract path (create → fund → delivery verify → release) without claiming we issue AED.
- **What does not change in production** — buyer-confirmed invoice + delivery proof hashes stay off-chain evidence; only settlement state and anchors move on-chain. The Smart LC interface is token-agnostic (`IERC20`).
- **What changes for UAE** — swap MockUSDC for a CBUAE Payment Token Services Regulation (PTSR)–compliant AED stablecoin issued by a licensed partner. Same factory, same escrow roles, same proof conditions.
- **Why this is remittance-adjacent impact without being remittance** — this is **B2B trade settlement** along UAE corridors (e.g. Jebel Ali suppliers paid in days, not 30–90). It addresses the same corridor liquidity and FX friction judges care about, as **enterprise payment infrastructure**, not consumer wallets or POS remittance.

## Do / Don’t

| Do say | Don’t say |
|--------|-----------|
| Settlement-ready for regulated AED stablecoin | “We issue AED” / “We are a remittance app” |
| MockUSDC proves the escrow lifecycle today | “Live AED mainnet settlement” (unless true) |
| Smart LC releases only after verified delivery | Fake Polygonscan links for simulated txs |

## Backup line if asked about the $50B figure

> That figure frames UAE corridor payment volume. Credara’s wedge is the SME trade-finance slice of that corridor — verified receivables and stablecoin LC settlement — not retail remittance.

## Related opportunity (footnote only — not the product)

Retail remittance and POS are adjacent corridor themes in the hackathon brief. Credara deliberately does **not** ship a remittance MVP. If asked: those flows can consume the same proof / settlement APIs later; today the product is **verified B2B trade finance + Smart LC escrow**.
