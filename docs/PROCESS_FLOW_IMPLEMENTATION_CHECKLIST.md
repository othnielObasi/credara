# Process Flow Implementation Checklist

This checklist maps Credara's process flows to implementation tasks. It should be used during build reviews, sprint planning, and production readiness assessment.

## Identity and Tenant Access
- [ ] Clerk JWT validation middleware implemented.
- [ ] User-to-organisation mapping implemented.
- [ ] RBAC roles enforced at route level.
- [ ] Admin and developer roles separated.
- [ ] Audit logs capture permission-sensitive actions.

## KYB
- [x] KYB provider interface exists.
- [x] Mock KYB provider exists.
- [x] Provider factory exists.
- [x] KYB status model exists.
- [x] KYB admin review routes exist.
- [ ] Live provider selected.
- [ ] Live provider credentials added.
- [ ] Webhook signature verification implemented for chosen provider.
- [ ] KYB status wired into all financing gates.

## Orders and Invoices
- [x] Core order/invoice models exist.
- [x] Invoice proof hashing exists.
- [ ] Buyer confirmation UI implemented fully.
- [ ] Invoice dispute workflow completed.
- [ ] Invoice status gates wired into receivable creation.

## Delivery Proof
- [x] Delivery proof scoring foundation exists.
- [ ] OTP/QR handover fully implemented.
- [ ] Logistics provider abstraction implemented.
- [ ] Duplicate proof hash detection wired into risk flags.
- [ ] Buyer confirmation UI completed.

## Proof Anchoring
- [x] ProofRegistry contract exists.
- [x] Blockchain outbox pattern exists.
- [ ] Relayer wired to real Amoy RPC.
- [ ] Indexer confirms events from Amoy.
- [ ] UI displays explorer links for every anchored proof.

## Receivables
- [x] ReceivableRegistry contract exists.
- [x] Receivable data model exists.
- [ ] Receivable creation API fully gated by KYB, invoice confirmation, delivery status, and disputes.
- [ ] Financier receivables dashboard completed.

## Smart LC
- [x] SmartLC contract hardened.
- [x] SmartLCFactory exists.
- [x] MockUSDC exists.
- [x] SmartLC tests added.
- [ ] API-to-contract creation/funding/release fully wired.
- [ ] UI settlement timeline completed.
- [ ] Dispute resolver UI completed.

## Trade Credit Score
- [x] CreditScoreAttestation contract exists.
- [ ] Versioned scoring model implemented as worker.
- [ ] Score explanation generated.
- [ ] Score snapshot anchoring wired to outbox.
- [ ] Score impact visible to SME/financier/admin.

## Finance Readiness
- [x] Finance readiness concept/model exists.
- [ ] Report generation endpoint completed.
- [ ] Evidence bundle export/share workflow completed.
- [ ] Financier review workflow completed.

## Admin / Risk Console
- [x] Admin KYB review endpoints exist.
- [ ] Unified risk queue implemented.
- [ ] Four-eyes approval for high-value overrides.
- [ ] Business freeze/unfreeze workflow.
- [ ] Manual override reason enforcement.

## Developer API
- [ ] API key model and scoped permissions implemented.
- [ ] Webhook subscription model implemented.
- [ ] Webhook signing implemented.
- [ ] Integration logs UI implemented.

## Audit and Production Readiness
- [x] Smart contract audit checklist added.
- [x] Deployment readiness checklist added.
- [x] Smart contract threat model added.
- [ ] Slither run included in CI.
- [ ] Contract coverage report generated.
- [ ] Legal review pack completed.
- [ ] External smart contract audit scheduled.

