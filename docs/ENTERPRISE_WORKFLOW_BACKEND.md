# Credara Enterprise Workflow Backend Upgrade

This upgrade aligns the backend with the full multi-user enterprise workflow represented in the latest Credara UI.

## Users now supported at backend level

### SME / Supplier
- Create orders and invoices.
- Request buyer confirmation.
- Submit delivery proof.
- Create receivables.
- Generate evidence bundles.
- View finance readiness and trade credit score.

### Buyer
- Has a dedicated buyer action inbox.
- Can approve, reject, dispute, or request more information.
- Buyer decisions update invoice / Smart LC state and write audit records.

### Financier / Lender
- Has deal-room endpoints for receivable review.
- Can generate financing offers.
- Can approve, reject, accept, or cancel offers.
- Can view evidence bundles, repayment schedules, proof receipts, and risk context.

### Admin / Risk / Compliance
- Can configure risk rules.
- Can evaluate policy/risk rules against workflow context.
- Can manage KYB and review audit logs.
- Can manage Smart LC dispute/refund/release workflows.

### Developer / Integration Partner
- Can create API keys.
- Can register webhook endpoints.
- Can run sandbox API simulations.
- Can view endpoint catalogue and webhook delivery logs.

### Logistics Provider / Integration
- Logistics verification records can be created and updated.
- Delivery status, GPS match, timestamp match, handover status, and evidence URI are scored into proof confidence.

### Auditor / Regulator
- Evidence bundles can be generated and read with linked invoice, receivable, Smart LC, KYB, proof, score, and Polygon tx evidence.
- Permission matrix now includes read-only audit concepts.

## New backend modules

### Buyer Inbox
Routes:
- `GET /api/v1/buyer-inbox/actions`
- `POST /api/v1/buyer-inbox/actions`
- `POST /api/v1/buyer-inbox/invoices/{invoice_id}/request-confirmation`
- `POST /api/v1/buyer-inbox/actions/{action_id}/decision`

Model:
- `BuyerAction`

### Logistics Verification
Routes:
- `GET /api/v1/logistics/verifications`
- `POST /api/v1/logistics/verifications`
- `PATCH /api/v1/logistics/verifications/{verification_id}`

Model:
- `LogisticsVerification`

### Financier Deal Room
Routes:
- `GET /api/v1/deal-room/summary`
- `GET /api/v1/deal-room/receivables`
- `POST /api/v1/deal-room/receivables/{receivable_id}/offers`
- `POST /api/v1/deal-room/offers/{offer_id}/{decision}`

Uses:
- `Receivable`
- `Invoice`
- `FinancingOffer`

### Repayments
Routes:
- `GET /api/v1/repayments`
- `POST /api/v1/repayments`
- `PATCH /api/v1/repayments/{repayment_id}`

Model:
- `RepaymentScheduleItem`

### Evidence Bundles
Routes:
- `POST /api/v1/evidence/bundles`
- `GET /api/v1/evidence/bundles/{bundle_id}`

Models:
- `EvidenceBundle`
- `EvidenceBundleItem`

### Risk Rules
Routes:
- `GET /api/v1/risk-rules`
- `POST /api/v1/risk-rules`
- `POST /api/v1/risk-rules/evaluate`

Model:
- `RiskRule`

### Developer Infrastructure
Routes:
- `POST /api/v1/developer/api-keys`
- `GET /api/v1/developer/api-keys`
- `POST /api/v1/developer/webhook-endpoints`
- `GET /api/v1/developer/webhook-deliveries`
- `POST /api/v1/developer/api-simulations`
- `GET /api/v1/developer/endpoints`

Models:
- `ApiKey`
- `WebhookEndpoint`
- `WebhookDelivery`
- `ApiUsageLog`

### Permissions Matrix
Route:
- `GET /api/v1/permissions/matrix`

### Smart LC Lifecycle
Routes:
- `POST /api/v1/smart-lcs/{lc_id}/fund`
- `POST /api/v1/smart-lcs/{lc_id}/release`
- `POST /api/v1/smart-lcs/{lc_id}/dispute`
- `POST /api/v1/smart-lcs/{lc_id}/refund`

These endpoints update Smart LC state, write audit logs, emit webhook delivery records, create proof bundle events, and simulate Polygon transaction hashes for demo/sandbox mode.

### Trade Credit Score Attestation
Route:
- `POST /api/v1/finance/businesses/{business_id}/score/attest`

This endpoint calculates or reuses the latest trade credit score, simulates Polygon attestation, writes blockchain outbox, creates a proof bundle, and records audit/webhook events.

## Important production notes

This implementation is backend-complete for the enterprise workflow shape, but production rollout still requires:

1. Database migrations through Alembic instead of relying only on `create_all`.
2. Real Polygon relayer implementation for mainnet/testnet transactions.
3. Real KYB provider credentials and webhook signature verification.
4. Real logistics provider integrations.
5. Object storage for evidence files.
6. Real API key authentication middleware.
7. Webhook delivery retry worker.
8. Legal review for receivable assignment and Smart LC enforceability.
9. Independent smart contract audit before production value custody.
