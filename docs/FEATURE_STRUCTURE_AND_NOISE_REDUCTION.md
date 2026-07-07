# Feature Structure and Noise Reduction

## Product Principle

Credara is not a collection of dashboards. It is a verified trade finance network.

The product is organised around five pillars:

1. Network: find/invite counterparties and discover financeable trades.
2. Trade: create contracts and invoices with clear commercial terms.
3. Trust: verify KYB, delivery proof, and Polygon evidence.
4. Finance: tokenize receivables and let financiers fund them.
5. Settlement: wallet-backed escrow, payment confirmation, ledger and reconciliation.

## Core Features

Core features remain visible in the main product flow:

- Business Directory and Counterparty Network
- Trade Opportunities and Seller Proposals
- Trade Contracts
- Invoices
- Delivery Proof
- Proof Ledger
- Receivables
- Financier Deal Room / Marketplace
- Wallets and Payment Intents
- Smart LC Escrow
- Settlement Ledger
- Reconciliation
- Repayments
- KYB and Compliance
- Risk Rules
- Evidence Bundle
- Admin Audit

## Supporting Features

Supporting features remain available but should not dominate the default user journey:

- API Explorer
- Webhook logs
- Permissions Matrix
- Launch Readiness
- CSV exports
- Role reports
- Mobile polish

## Demo-only Features

Demo actions are intentionally separated from production actions:

- Run next workflow step
- Simulate chain confirmation
- Reset demo

In production, these should be disabled or hidden behind a sandbox/demo environment flag.

## UI Changes

The signed-in app now uses grouped navigation:

- Operate
- Network
- Settlement
- Trust
- Platform

The dashboard now focuses on real operating metrics:

- Active contracts
- Escrow funded
- Advance available
- Confirmations
- Reconciliation variance

Generic charts and noisy metrics have been reduced.

## Backend Endpoint

The backend exposes the feature map and navigation structure:

```text
GET /api/v1/feature-structure/pillars
GET /api/v1/feature-structure/features
GET /api/v1/feature-structure/features/core
GET /api/v1/feature-structure/features/supporting
GET /api/v1/feature-structure/features/demo
GET /api/v1/feature-structure/navigation
```
