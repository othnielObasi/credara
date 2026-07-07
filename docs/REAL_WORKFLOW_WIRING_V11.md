# Credara v11 — Real Workflow Wiring

## Purpose

v11 moves the newest Credara capabilities beyond textified/demo-only behaviour by adding persistent backend workflow objects and endpoints.

## What is now persistent

The backend now has SQLAlchemy models for:

- Workspace
- Membership
- OnboardingProgressRecord
- InvitationRecord
- UserSettingsRecord
- APIKeyRecord
- WebhookEndpointRecord
- WalletAccountRecord
- PaymentIntentRecord
- EscrowAccountRecord
- SettlementLedgerRecord
- ReconciliationRecord

## Key API endpoints

```text
POST /api/v1/real/onboarding/start
GET  /api/v1/real/onboarding/progress/{workspace_id}

GET  /api/v1/real/access/navigation/{role}
GET  /api/v1/real/access/can-access/{role}/{page}

POST /api/v1/real/invitations
GET  /api/v1/real/invitations
GET  /api/v1/real/invitations/token/{token}
POST /api/v1/real/invitations/token/{token}/decision

GET  /api/v1/real/settings
PUT  /api/v1/real/settings

POST /api/v1/real/api-keys
GET  /api/v1/real/api-keys
POST /api/v1/real/api-keys/{api_key_id}/rotate

POST /api/v1/real/webhooks

POST /api/v1/real/wallets
GET  /api/v1/real/wallets

POST /api/v1/real/payment-intents
POST /api/v1/real/payment-intents/{intent_id}/submit
POST /api/v1/real/payment-intents/{intent_id}/confirm
GET  /api/v1/real/payment-intents

POST /api/v1/real/escrows
POST /api/v1/real/escrows/{escrow_id}/fund
POST /api/v1/real/escrows/{escrow_id}/release
GET  /api/v1/real/escrows

GET  /api/v1/real/ledger
GET  /api/v1/real/ledger/summary
GET  /api/v1/real/reports/role/{role}
GET  /api/v1/real/reports/admin/aggregate
POST /api/v1/real/reconciliation/{reference_type}/{reference_id}
GET  /api/v1/real/health
```

## Real behaviour now implemented

### Invitation onboarding

Invitations now create secure tokens, persist invite state, and support accept/reject decisions.

### Settings

Settings are persisted by user/workspace and can be updated instead of only shown as static UI text.

### API keys and webhooks

API keys are generated, hashed, rotated and scoped. Webhook endpoint secrets are generated and hashed.

### Payments and escrow

Payment intents are persisted and move through pending → submitted → confirmed. Confirmed payment intents create ledger evidence and can fund Smart LC escrow accounts.

### Settlement ledger

Ledger entries are generated from real backend events such as payment intent creation, tx submission, tx confirmation, escrow funding and escrow release.

### Reconciliation

Reconciliation computes expected versus confirmed ledger amounts and returns valid/manual-review decisions.

## Still required for mainnet production

- Clerk/OIDC middleware integration
- object-level permission middleware across every legacy route
- real email provider for invitation delivery
- WalletConnect/embedded wallet frontend integration
- real Polygon RPC/indexer event listener
- durable migration framework rather than metadata create_all
- full integration tests and seed scripts
- PDF renderer/storage for legal documents
