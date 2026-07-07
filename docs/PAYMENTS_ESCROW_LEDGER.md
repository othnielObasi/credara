# Payments, Wallets, Escrow and Settlement Ledger

## Purpose

This implementation upgrades Credara with a production-grade payment layer:

- business wallets
- payment intents
- Smart LC escrow funding
- stablecoin approval/funding lifecycle
- on-chain confirmation state
- internal settlement ledger
- role-specific reporting
- admin aggregate reporting
- reconciliation between expected payment, chain event, internal ledger and Smart LC state

## Wallet Model

Credara supports three wallet modes:

1. Connected wallet for crypto-native/hackathon users.
2. Embedded business wallet for SMEs and non-crypto users.
3. Treasury wallet for platform, fee, refund and settlement operations.

## Escrow Model

Smart LC escrow is funded through stablecoin transfer:

```text
Wallet approves stablecoin
Wallet funds Smart LC escrow
Polygon confirms transaction
Credara indexer validates event
Internal ledger records funding
Smart LC state becomes Funded
```

## New API Endpoints

```text
GET  /api/v1/payments/wallets
GET  /api/v1/payments/intents
POST /api/v1/payments/intents/escrow-funding
POST /api/v1/payments/intents/{payment_intent_id}/confirm

GET  /api/v1/payments/escrows
POST /api/v1/payments/escrows/{smart_lc_id}/release

GET  /api/v1/payments/ledger
GET  /api/v1/payments/ledger/summary

GET  /api/v1/payments/reports/role/{role}
GET  /api/v1/payments/reports/admin/aggregate

GET  /api/v1/payments/reconciliation/{reference_id}
```

## Reporting

The settlement ledger is adapted for each role:

- SME/Seller: payouts, advances, received settlement.
- Buyer: escrow funding, release locks, refund exposure.
- Financier: funded receivables, repayment allocation.
- Admin: aggregate confirmed, pending, fallback and exception receipts.

## Production Next Steps

- Replace deterministic demo repository with persistent SQLAlchemy models.
- Add WalletConnect/MPC provider integration.
- Add token approval and transfer calls to Polygon.
- Add chain indexer/event listener.
- Add settlement ledger table and double-entry accounting.
- Add real reconciliation jobs and exception queue.
- Add PDF/CSV exports for audit packs.
