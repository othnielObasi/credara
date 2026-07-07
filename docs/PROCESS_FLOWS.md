# Credara Process Flows

This document defines the end-to-end operating flows for Credara. It is intended for product, engineering, enterprise reviewers, security reviewers, and hackathon judges. Each flow describes the business objective, actors, preconditions, happy path, alternate paths, failure modes, system modules, APIs, database records, and Polygon/on-chain touchpoints.

Credara is built as enterprise-grade SME trade finance infrastructure. The hackathon demo should expose the same flows in a simplified sandbox mode, while the underlying design remains suitable for production pilots with SMEs, buyers, financiers, ports, logistics partners, and fintech platforms.

---

## Flow 1: Enterprise Tenant, User, and Role Onboarding

### Objective
Create a secure multi-tenant operating environment where users belong to organisations and can only access actions permitted by their role.

### Actors
- SME administrator
- Buyer user
- Financier user
- Risk/admin user
- Developer/API user
- Clerk/OIDC identity provider

### Preconditions
- Clerk project is configured.
- Backend has Clerk issuer/JWKS values.
- Roles and organisations are configured in Credara.

### Happy Path
1. User signs in through Clerk.
2. Clerk issues JWT containing subject, email, organisation, and role metadata.
3. Credara API validates JWT signature and issuer.
4. Credara maps the identity to an internal user record.
5. User is attached to a business, buyer, financier, or admin organisation.
6. RBAC middleware checks permissions before every action.
7. Audit log records login-sensitive and permission-sensitive actions.

### Alternate Paths
- User exists in Clerk but not in Credara: create pending internal profile.
- User has no organisation: route to onboarding.
- User role changes in Clerk: refresh permissions on next token validation.

### Failure Modes
- Invalid JWT: reject with 401.
- Role missing: reject with 403.
- Organisation mismatch: reject with 403 and audit the attempt.

### System Modules
- `apps/api/app/modules/auth`
- `apps/api/app/models/identity.py`
- Clerk middleware to be wired in production
- `audit_logs`

### Main APIs
- `GET /api/v1/auth/me`
- Future Clerk webhook: `POST /api/v1/auth/webhooks/clerk`

### Enterprise Controls
- SSO/OIDC-ready
- RBAC
- multi-tenant isolation
- audit logging
- optional API key access for developers

---

## Flow 2: SME Business Profile and KYB Submission

### Objective
Verify that an SME is a legitimate business before allowing finance, high-value transactions, receivable funding, or smart LC settlement.

### Actors
- SME admin
- KYB provider
- Risk admin
- Credara backend

### Preconditions
- SME account exists.
- Business profile exists or is being created.
- KYB provider is configured as `mock`, `sumsub`, `persona`, `trulioo`, or `comply_advantage`.

### Happy Path
1. SME creates or updates business profile.
2. SME provides legal name, trading name, registration number, tax ID, jurisdiction, industry, address, and beneficial ownership details.
3. SME uploads required KYB documents.
4. Credara stores document metadata and file hashes.
5. Credara submits applicant payload to configured KYB provider.
6. KYB provider returns provider applicant/check ID.
7. Credara stores the check as `PENDING_REVIEW`.
8. Provider completes screening and sends webhook.
9. Credara validates webhook signature.
10. Credara maps provider status to internal KYB status.
11. If approved, business becomes finance-eligible according to risk limits.
12. Trust score engine applies KYB status modifier.

### Alternate Paths
- Provider requests more information: status becomes `NEEDS_MORE_INFO`.
- Provider flags sanctions, PEP, adverse media, or registration mismatch: status becomes `MANUAL_REVIEW` or `REJECTED`.
- Admin manually approves/rejects after review.

### Failure Modes
- Provider unavailable: keep profile in `PENDING_REVIEW`, retry with backoff.
- Invalid document: mark document rejected and request replacement.
- Webhook replay: reject by idempotency key/signature/timestamp.

### System Modules
- `apps/api/app/modules/kyb`
- `apps/api/app/models/business.py`
- `KYBProfile`, `KYBDocument`, `KYBCheck`, `KYBWebhookEvent`, `KYBRiskFlag`

### Main APIs
- `POST /api/v1/kyb/profiles/{business_id}`
- `GET /api/v1/kyb/profiles/{business_id}`
- `POST /api/v1/kyb/profiles/{business_id}/documents`
- `POST /api/v1/kyb/profiles/{business_id}/submit`
- `GET /api/v1/kyb/profiles/{business_id}/status`
- `POST /api/v1/kyb/webhooks/{provider}`
- `GET /api/v1/kyb/admin/reviews`
- `POST /api/v1/kyb/admin/{profile_id}/approve`
- `POST /api/v1/kyb/admin/{profile_id}/reject`

### Polygon Touchpoints
- None by default. KYB details remain off-chain.
- Future option: anchor a KYB approval attestation hash without exposing private data.

### Business Rules
- SME cannot request receivable finance unless KYB is approved or manually approved.
- High-risk flags can reduce transaction limits.
- Sanctions match blocks finance and settlement activity.

---

## Flow 3: Buyer/Seller Trade Order Creation

### Objective
Create a structured trade event that can later support invoice verification, receivable tokenisation, settlement, and credit scoring.

### Actors
- Buyer
- SME seller
- Credara backend

### Preconditions
- Seller business profile exists.
- Seller KYB status satisfies platform rules for the transaction value.
- Buyer is registered or invited.

### Happy Path
1. Buyer creates purchase order or seller creates order request.
2. Order includes seller, buyer, goods/services, amount, currency, quantity, delivery deadline, payment terms, and dispute terms.
3. Credara validates the parties and value limits.
4. Seller accepts the order.
5. Order state becomes `ACCEPTED`.
6. Credara emits internal audit event.
7. Invoice can now be generated.

### Alternate Paths
- Seller rejects order: order closes.
- Buyer edits order before acceptance.
- Admin review required for high-risk or high-value orders.

### Failure Modes
- Seller KYB not approved: order allowed only in sandbox or low-value mode.
- Buyer identity mismatch: order blocked.
- Duplicate order reference: reject or treat as idempotent retry.

### System Modules
- `orders`
- `businesses`
- `audit`

### Main APIs
- `POST /api/v1/orders`
- `GET /api/v1/orders/{order_id}`
- `POST /api/v1/orders/{order_id}/accept`
- `POST /api/v1/orders/{order_id}/reject`

### Polygon Touchpoints
- No immediate on-chain event required.
- Future option: anchor high-value order hash after both parties confirm.

---

## Flow 4: Invoice Creation and Buyer Confirmation

### Objective
Convert a trade order into a buyer-confirmed invoice that can later become a tokenized receivable.

### Actors
- SME seller
- Buyer
- Credara backend

### Preconditions
- Order is accepted.
- Invoice amount does not exceed order amount unless amended.
- Seller can issue invoice under platform rules.

### Happy Path
1. Seller creates invoice from accepted order.
2. Credara generates invoice reference and normalized invoice payload.
3. Credara hashes invoice data and stores the hash.
4. Buyer receives confirmation request.
5. Buyer confirms invoice as valid.
6. Invoice state becomes `BUYER_CONFIRMED`.
7. Invoice proof becomes eligible for anchoring and receivable creation.

### Alternate Paths
- Buyer disputes invoice: invoice state becomes `DISPUTED`.
- Buyer requests correction: seller amends and resubmits.
- Partial invoice: multiple invoices can map to one order if permitted.

### Failure Modes
- Duplicate invoice number: reject for the same seller/buyer pair.
- Amount mismatch: require correction or admin review.
- Buyer fails to respond: invoice remains unconfirmed and cannot be financed.

### System Modules
- `invoices`
- `proof_bundles`
- `audit`

### Main APIs
- `POST /api/v1/invoices`
- `GET /api/v1/invoices/{invoice_id}`
- `POST /api/v1/invoices/{invoice_id}/confirm`
- `POST /api/v1/invoices/{invoice_id}/dispute`

### Polygon Touchpoints
- Invoice hash can be submitted to `ProofRegistry.sol` after buyer confirmation.
- The on-chain proof does not contain private invoice data.

---

## Flow 5: Delivery Proof Submission and Verification

### Objective
Verify that goods/services were delivered before improving trust score, tokenising receivables, or releasing settlement.

### Actors
- SME seller
- Buyer
- Logistics provider
- Credara backend
- Risk admin

### Preconditions
- Invoice/order exists.
- Seller is allowed to submit delivery proof.
- Optional delivery OTP or QR code has been generated.

### Happy Path
1. Seller submits delivery proof: document/photo, recipient name, timestamp, GPS/location if available, tracking number if available, and buyer OTP/QR confirmation.
2. Credara creates proof bundle and calculates file hash.
3. Credara checks basic evidence consistency: order ID, invoice ID, amount, recipient, timestamp, duplicate file hash.
4. Logistics provider abstraction checks tracking status if tracking number exists.
5. Buyer confirms delivery or OTP validates handover.
6. Credara calculates delivery proof confidence score.
7. If confidence threshold is met, delivery state becomes `VERIFIED`.
8. Proof bundle hash becomes eligible for anchoring on Polygon.
9. Trust score engine updates fulfilment metrics.

### Alternate Paths
- Buyer marks partial delivery.
- Buyer rejects proof.
- Logistics status conflicts with seller evidence.
- Admin/risk review required.

### Failure Modes
- Duplicate image/document hash: flag suspicious proof.
- OTP mismatch: reject or escalate.
- Tracking says not delivered: hold verification.
- Buyer disputes delivery: settlement blocked.

### System Modules
- `delivery_proofs`
- `proof_bundles`
- `logistics` provider abstraction to be implemented next
- `trust_score`
- `audit`

### Main APIs
- `POST /api/v1/delivery-proofs`
- `GET /api/v1/delivery-proofs/{proof_id}`
- `POST /api/v1/delivery-proofs/{proof_id}/buyer-confirm`
- `POST /api/v1/delivery-proofs/{proof_id}/reject`
- Future: `POST /api/v1/delivery-proofs/{proof_id}/verify-logistics`

### Polygon Touchpoints
- Verified delivery proof bundle hash is anchored using `ProofRegistry.sol`.
- The UI displays the resulting Amoy/Polygon transaction link.

### Proof Confidence Rules
- Low: seller upload only.
- Medium: seller upload + timestamp + metadata consistency.
- High: seller upload + buyer confirmation/OTP.
- Very high: seller upload + buyer confirmation/OTP + logistics verification.

---

## Flow 6: Proof Bundle Creation and Polygon Anchoring

### Objective
Create tamper-evident records for invoices, delivery proofs, settlement events, receivables, and credit score snapshots.

### Actors
- Credara backend
- Polygon relayer worker
- Polygon network
- Admin/risk reviewer

### Preconditions
- Business event has reached anchorable status.
- Off-chain payload has been normalized.
- Proof hash has been generated.

### Happy Path
1. Credara normalizes event payload into deterministic JSON.
2. Credara calculates hash using canonical hashing rules.
3. Proof bundle is stored off-chain.
4. Backend creates blockchain outbox event.
5. Polygon relayer reads pending outbox item.
6. Relayer submits transaction to `ProofRegistry.sol`.
7. Contract emits proof anchored event.
8. Polygon indexer updates local transaction status.
9. UI displays proof status and explorer link.

### Alternate Paths
- Gas/RPC error: relayer retries.
- Duplicate proof hash: mark as already anchored.
- Transaction pending too long: worker rechecks by nonce/hash.

### Failure Modes
- Relayer private key missing: outbox remains pending.
- Contract paused: outbox remains blocked until unpaused.
- Hash mismatch during verification: mark proof invalid and alert admin.

### System Modules
- `proof_bundles`
- `blockchain_outbox`
- `apps/workers/polygon-relayer`
- `apps/workers/polygon-indexer`
- `ProofRegistry.sol`

### Main APIs
- `POST /api/v1/proofs/anchor`
- `GET /api/v1/proofs/{proof_id}`
- `GET /api/v1/proof-ledger`

### Polygon Touchpoints
- `ProofRegistry.anchorProof(proofId, proofHash, proofType, subjectId)`
- On-chain event consumed by indexer.

---

## Flow 7: Tokenized Receivable Creation

### Objective
Convert a buyer-confirmed invoice and verified delivery record into a financeable receivable record on Polygon.

### Actors
- SME seller
- Credara backend
- Polygon relayer
- Financier

### Preconditions
- Seller KYB is approved.
- Invoice is buyer-confirmed.
- Delivery proof is verified or not required under payment terms.
- Invoice is not already tokenized.
- No unresolved dispute exists.

### Happy Path
1. SME requests receivable creation from confirmed invoice.
2. Credara validates invoice, delivery, KYB, and dispute status.
3. Credara creates receivable record in database.
4. Receivable status becomes `PENDING_ANCHOR`.
5. Relayer calls `ReceivableRegistry.createReceivable(...)`.
6. Contract validates uniqueness and emits receivable creation event.
7. Indexer updates receivable with on-chain tx reference.
8. Receivable appears in financier marketplace/dashboard.
9. Finance readiness report is updated.

### Alternate Paths
- Invoice confirmed but delivery pending: receivable can be marked `CONDITIONAL` if product rules allow.
- Admin review required for high-value receivable.
- Receivable is rejected due to dispute or duplicate.

### Failure Modes
- Duplicate invoice proof hash: block creation.
- Invalid seller address: reject on contract or backend.
- Contract paused: keep pending.

### System Modules
- `receivables`
- `invoices`
- `delivery_proofs`
- `blockchain_outbox`
- `ReceivableRegistry.sol`

### Main APIs
- `POST /api/v1/receivables`
- `GET /api/v1/receivables/{receivable_id}`
- `GET /api/v1/receivables?status=verified`

### Polygon Touchpoints
- `ReceivableRegistry.createReceivable(...)`
- Future: ERC-721/ERC-1155 representation if legal model supports transferable claims.

### Legal Note
The token/registry entry should initially represent a verifiable receivable record, not necessarily automatic legal assignment. Legal enforceability must be reviewed before production financing.

---

## Flow 8: Smart Letter of Credit / Escrow Creation

### Objective
Provide programmable trade settlement where funds are locked and released based on verified commerce events.

### Actors
- Buyer
- SME seller
- Financier
- Credara backend
- Polygon smart contracts
- Risk admin

### Preconditions
- Buyer and seller exist.
- Required KYB status is satisfied.
- Trade order and invoice exist.
- Settlement token exists, using `MockUSDC` in demo and stablecoin in production.

### Happy Path
1. Buyer or financier creates a SmartLC request.
2. Credara validates parties, amount, deadlines, and terms.
3. Backend creates LC record.
4. Relayer or user wallet calls `SmartLCFactory.createLC(...)`.
5. Buyer/financier funds LC with mock USDC/stablecoin.
6. `SmartLC` state becomes `FUNDED`.
7. Seller fulfils order and submits delivery proof.
8. Delivery is verified.
9. Contract release function is called by authorized verifier/operator.
10. Funds are released to seller.
11. Settlement event is anchored and reflected in proof ledger.
12. Trust score and finance readiness metrics update.

### Alternate Paths
- Milestone-based release: partial releases occur at dispatch, delivery, acceptance.
- Financier funds order finance instead of buyer.
- Buyer disputes delivery before release.
- Admin resolves dispute.

### Failure Modes
- Funding deadline missed: LC can be cancelled.
- Delivery deadline missed: refund path opens.
- Dispute opened: release blocked.
- Token transfer fails: transaction reverts.
- Contract paused: settlement blocked.

### System Modules
- `smart_lc`
- `settlements`
- `delivery_proofs`
- `disputes`
- `SmartLC.sol`
- `SmartLCFactory.sol`

### Main APIs
- `POST /api/v1/smart-lcs`
- `GET /api/v1/smart-lcs/{lc_id}`
- `POST /api/v1/smart-lcs/{lc_id}/fund`
- `POST /api/v1/smart-lcs/{lc_id}/release`
- `POST /api/v1/smart-lcs/{lc_id}/refund`
- `POST /api/v1/smart-lcs/{lc_id}/dispute`

### Polygon Touchpoints
- `SmartLCFactory.createLC(...)`
- `SmartLC.fund(...)`
- `SmartLC.submitDelivery(...)`
- `SmartLC.verifyDelivery(...)`
- `SmartLC.release(...)`
- `SmartLC.refund(...)`
- `SmartLC.openDispute(...)`
- `SmartLC.resolveDispute(...)`

---

## Flow 9: Financier Review and Invoice Finance Offer

### Objective
Allow financiers to review verified receivables, SME credit profile, and finance readiness evidence before providing capital.

### Actors
- Financier
- SME seller
- Credara backend
- Risk/admin user

### Preconditions
- Financier profile exists and is permitted to fund.
- Receivable is verified and finance-eligible.
- SME KYB is approved.

### Happy Path
1. Financier opens verified receivables dashboard.
2. Financier reviews SME profile, KYB status, trade credit score, invoice proof, delivery proof, buyer confirmation, dispute history, and repayment history.
3. Financier creates finance offer: advance amount, fee/discount, repayment terms, expiry.
4. SME accepts offer.
5. Funding settlement is executed through SmartLC or off-chain settlement rail depending on environment.
6. Receivable status becomes `FINANCED`.
7. Repayment tracking begins.
8. Final repayment outcome updates credit score.

### Alternate Paths
- Financier requests additional documents.
- SME rejects offer.
- Multiple financiers bid; SME selects one.
- Admin approval required for high-value finance.

### Failure Modes
- Receivable becomes disputed after offer: offer is frozen.
- SME KYB status changes: financing blocked.
- Settlement fails: offer remains accepted but unfunded until retry.

### System Modules
- `finance_readiness`
- `receivables`
- `financing_offers`
- `settlements`
- `trust_score`

### Main APIs
- `GET /api/v1/financier/receivables`
- `POST /api/v1/financing-offers`
- `POST /api/v1/financing-offers/{offer_id}/accept`
- `POST /api/v1/financing-offers/{offer_id}/reject`

### Polygon Touchpoints
- Optional funding event through `SmartLC` or settlement contract.
- Receivable status update can be anchored.

---

## Flow 10: Trade Credit Score Calculation and Attestation

### Objective
Generate a transparent SME trade credit score based on verified commerce behaviour and optionally anchor score snapshots on Polygon.

### Actors
- Trust score worker
- SME
- Financier
- Risk admin
- Polygon relayer

### Preconditions
- SME has trade events or KYB data.
- Scoring rules are versioned.
- Data quality checks pass.

### Happy Path
1. Credit score worker collects verified signals:
   - KYB status
   - confirmed invoices
   - verified deliveries
   - dispute rate
   - settlement history
   - repayment history
   - buyer diversity
   - receivable performance
2. Worker calculates score using versioned scoring rules.
3. Score explanation is generated.
4. Score snapshot is stored off-chain.
5. If score is eligible for attestation, hash is created.
6. Relayer submits score attestation to `CreditScoreAttestation.sol`.
7. UI shows score, explanation, confidence, and Polygon proof link.

### Alternate Paths
- Insufficient data: score is provisional.
- High-risk flags: score capped or financing blocked.
- Admin override: override is recorded with reason.

### Failure Modes
- Missing data: skip affected signal and reduce confidence.
- Conflicting data: flag for review.
- Attempted score manipulation: audit and freeze finance eligibility.

### System Modules
- `trust_score`
- `credit_score_worker`
- `CreditScoreAttestation.sol`
- `audit`

### Main APIs
- `GET /api/v1/trust-score/{business_id}`
- `POST /api/v1/trust-score/{business_id}/recalculate`
- `GET /api/v1/trust-score/{business_id}/snapshots`

### Polygon Touchpoints
- `CreditScoreAttestation.attestScore(businessIdHash, score, scoreHash, modelVersion)`

### Scoring Principles
- Score must be explainable.
- Score must be versioned.
- Score should distinguish data volume from behavioural quality.
- Score should not expose private buyer/seller details on-chain.

---

## Flow 11: Finance Readiness Report Generation

### Objective
Produce lender-readable evidence from verified trade activity.

### Actors
- SME
- Financier
- Credara backend

### Preconditions
- SME has business profile.
- At least one invoice or order exists.

### Happy Path
1. SME requests finance readiness report.
2. Credara aggregates business profile, KYB status, receivables, invoices, delivery proofs, settlement history, disputes, and trust score.
3. Report is generated with risk summary, eligible receivables, evidence bundle, and recommended financing band.
4. SME can share report with financier through platform or export.
5. Report hash may be anchored for tamper evidence.

### Alternate Paths
- Report shows insufficient evidence.
- Report requires admin review due to high-risk flags.
- Financier requests refreshed report.

### Failure Modes
- Missing KYB: report generated but marked not finance-eligible.
- Disputed receivables: excluded or flagged.

### System Modules
- `finance_readiness`
- `trust_score`
- `receivables`
- `proof_ledger`

### Main APIs
- `POST /api/v1/finance-readiness/{business_id}/generate`
- `GET /api/v1/finance-readiness/{business_id}/latest`

### Polygon Touchpoints
- Optional report hash anchored using `ProofRegistry.sol`.

---

## Flow 12: Dispute Handling and Settlement Freeze

### Objective
Prevent unsafe settlement when buyer, seller, logistics data, or proof evidence conflicts.

### Actors
- Buyer
- SME seller
- Risk admin/dispute resolver
- Credara backend
- SmartLC contract

### Preconditions
- Order, invoice, delivery proof, receivable, or LC exists.
- User has permission to open dispute.

### Happy Path
1. Buyer or seller opens dispute with reason code.
2. Credara freezes related settlement or finance actions.
3. If SmartLC exists, dispute state is set on-chain or release is blocked by backend and contract state.
4. Admin reviews evidence.
5. Admin resolves dispute as release, refund, partial release, correction, or cancellation.
6. Contract action is executed where applicable.
7. Dispute outcome updates trust score and proof ledger.

### Alternate Paths
- Automated resolution for low-value disputes.
- External arbitration/legal review for high-value disputes.
- Partial delivery leads to partial settlement.

### Failure Modes
- Frivolous repeated disputes: flag buyer/seller.
- Admin conflict of interest: require second approver for high value.
- Evidence tampering detected: freeze account and escalate.

### System Modules
- `disputes`
- `smart_lc`
- `settlements`
- `audit`
- `trust_score`

### Main APIs
- `POST /api/v1/disputes`
- `GET /api/v1/disputes/{dispute_id}`
- `POST /api/v1/disputes/{dispute_id}/resolve`

### Polygon Touchpoints
- `SmartLC.openDispute(...)`
- `SmartLC.resolveDispute(...)`
- `ProofRegistry.anchorProof(...)` for dispute outcome proof hash.

---

## Flow 13: Backend Outbox, Relayer, and Indexer

### Objective
Ensure reliable, auditable blockchain writes without making user-facing API requests depend directly on chain finality.

### Actors
- Credara API
- Blockchain outbox
- Polygon relayer
- Polygon indexer
- Polygon network

### Preconditions
- Contract addresses configured.
- Relayer wallet funded with Amoy POL in testnet.
- RPC URL configured.

### Happy Path
1. API action creates database transaction and writes outbox event atomically.
2. API responds with pending chain status.
3. Relayer picks up outbox event.
4. Relayer submits Polygon transaction.
5. Transaction hash is stored.
6. Indexer confirms transaction and reads emitted events.
7. Local domain record is updated as anchored/confirmed.
8. UI reflects confirmed proof and explorer link.

### Alternate Paths
- Relayer retries failed transaction.
- Idempotency prevents duplicate on-chain writes.
- Manual admin replay for stuck events.

### Failure Modes
- RPC outage: retry with backoff and secondary RPC.
- Nonce conflict: relayer recovers nonce.
- Contract revert: mark event failed and expose reason.
- Chain reorg: indexer waits for confirmation threshold.

### System Modules
- `blockchain_outbox`
- `polygon_relayer.py`
- `polygon_indexer.py`
- `polygon_transactions`

### Main APIs
- `GET /api/v1/blockchain/outbox`
- `POST /api/v1/blockchain/outbox/{event_id}/retry`
- `GET /api/v1/polygon/transactions/{tx_hash}`

### Polygon Touchpoints
- All contract write interactions.

---

## Flow 14: Developer API and Webhook Integration

### Objective
Allow fintechs, marketplaces, logistics platforms, and enterprise systems to integrate Credara as commerce trust and trade finance infrastructure.

### Actors
- Developer/API user
- External platform
- Credara API

### Preconditions
- Developer organisation exists.
- API key has been issued.
- Webhook endpoint configured.

### Happy Path
1. Developer creates API key.
2. External platform creates business/order/invoice/proof records through API.
3. Credara processes verification and proof anchoring.
4. Credara sends webhook events to external platform:
   - KYB approved/rejected
   - invoice confirmed
   - delivery verified
   - receivable created
   - LC funded/released/refunded
   - credit score updated
5. Developer can inspect integration logs.

### Alternate Paths
- Webhook delivery fails and retries.
- API key rotated.
- Sandbox mode used before production.

### Failure Modes
- Invalid API key: reject with 401.
- Rate limit exceeded: return 429.
- Webhook signature invalid: external receiver should reject.

### System Modules
- `api_keys`
- `webhook_events`
- `developer_portal`
- `audit`

### Main APIs
- `POST /api/v1/developers/api-keys`
- `POST /api/v1/developers/webhooks`
- `GET /api/v1/developers/integration-logs`

### Enterprise Controls
- Scoped API keys
- rate limits
- webhook signing
- idempotency keys
- sandbox/prod separation

---

## Flow 15: Admin, Risk Review, and Manual Override

### Objective
Give internal risk and operations teams controlled ability to review KYB, disputes, suspicious proofs, financing exceptions, and stuck blockchain actions.

### Actors
- Risk admin
- Super admin
- Compliance reviewer

### Preconditions
- Admin user has required role.
- Action requires review or override.

### Happy Path
1. Admin opens risk console.
2. Admin reviews queued items:
   - KYB manual review
   - suspicious delivery proof
   - disputed invoice
   - failed relayer event
   - high-value receivable
   - credit score override request
3. Admin records decision and reason.
4. Credara applies state transition.
5. Audit log captures who, what, when, and why.
6. If required, Polygon proof or settlement state is updated.

### Alternate Paths
- Four-eyes approval for high-value actions.
- Escalation to legal/compliance.
- Freeze business account.

### Failure Modes
- Unauthorized override attempt: reject and alert.
- Missing reason code: reject.
- Conflicting admin actions: use optimistic locking.

### System Modules
- `admin`
- `audit`
- `kyb`
- `disputes`
- `blockchain_outbox`

### Main APIs
- `GET /api/v1/admin/reviews`
- `POST /api/v1/admin/actions/{action_id}/approve`
- `POST /api/v1/admin/actions/{action_id}/reject`
- `POST /api/v1/admin/businesses/{business_id}/freeze`

### Enterprise Controls
- reason-required manual override
- audit log immutability
- role separation
- optional four-eyes approval

---

## Flow 16: Hackathon Demo Flow

### Objective
Show judges a complete end-to-end trade finance loop without requiring live KYB, real logistics, mainnet funds, or legal settlement.

### Demo Setup
- `KYB_PROVIDER=mock`
- `LOGISTICS_PROVIDER=mock` or OTP-only
- Polygon Amoy RPC configured
- MockUSDC deployed
- contracts deployed on Amoy
- demo SME, buyer, and financier accounts seeded

### Judge-Facing Flow
1. SME completes mock KYB and is approved.
2. Buyer creates order.
3. SME accepts order and generates invoice.
4. Buyer confirms invoice.
5. SME submits delivery proof with OTP.
6. Delivery proof confidence score is calculated.
7. Proof hash is anchored on Polygon Amoy.
8. Receivable is created/tokenized.
9. Trade credit score updates.
10. Financier reviews finance readiness and funds SmartLC/invoice finance.
11. SmartLC releases settlement after verified delivery.
12. Proof ledger shows all events and Polygon transaction links.

### What This Demonstrates
- Tokenized receivables
- Smart contract-based LC/escrow
- On-chain trade credit score attestation
- Delivery proof verification
- KYB-gated finance access
- Polygon proof anchoring
- Enterprise workflow readiness

---

## Flow Status Matrix

| Flow | MVP/demo | Enterprise pilot | Production hardening required |
|---|---:|---:|---:|
| Identity/OIDC | Clerk sandbox | Clerk production/OIDC | SSO policies, SCIM optional |
| KYB | Mock provider | Live provider sandbox | Legal/compliance policy |
| Orders/invoices | Yes | Yes | Accounting integrations optional |
| Delivery proof | OTP/mock | Logistics API sandbox | Provider contracts, fraud tuning |
| Proof anchoring | Amoy | Polygon PoS/test pilot | Relayer HA, monitoring |
| Receivables | Registry record | Pilot with financier | Legal enforceability |
| Smart LC | MockUSDC Amoy | Stablecoin test/pilot | Audit, legal review |
| Credit score | Rules-based | Tuned scoring model | Model governance |
| Admin review | Basic | Full risk queue | Four-eyes controls |
| Developer API | Basic | Partner sandbox | Rate limits, API SLAs |

