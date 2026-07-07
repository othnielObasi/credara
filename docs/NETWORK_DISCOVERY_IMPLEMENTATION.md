# Credara Network Discovery Implementation

## Purpose

This implementation adds the missing pre-transaction network layer to Credara. The earlier backend supported the post-relationship trade finance workflow: invoice, buyer confirmation, delivery proof, receivable, Smart LC, evidence, repayment and audit. The new layer answers the business questions:

- How does a buyer find or invite a seller?
- How does a seller discover buyer demand?
- How does a financier discover fundable receivables?
- How can enterprises embed relationship creation through APIs instead of manual UI flows?

Credara is now structured as a verified trade finance network, not only an invoice workflow tool.

## Relationship models supported

### 1. Private invite model

A buyer, seller, financier or logistics partner can invite a known counterparty through a relationship object. This supports normal enterprise trade where counterparties already know one another.

Examples:

- Buyer invites seller by business ID or email.
- Seller invites buyer to confirm a trade contract or invoice.
- SME invites financier to review receivables.
- SME or buyer connects a logistics provider.

Backend models:

- `CounterpartyRelationship`
- `TradeContract`

Key endpoints:

- `POST /api/v1/network/invitations`
- `GET /api/v1/network/invitations`
- `POST /api/v1/network/invitations/{relationship_id}/decision`
- `POST /api/v1/network/trade-contracts`
- `POST /api/v1/network/trade-contracts/{contract_id}/decision`
- `POST /api/v1/network/trade-contracts/{contract_id}/activate`

### 2. Discoverable business network

Verified businesses can publish a directory profile showing role, sector, country, capability, contact email, score snapshot, supported currencies and visibility.

Backend model:

- `BusinessDirectoryProfile`

Key endpoints:

- `GET /api/v1/network/directory`
- `POST /api/v1/network/directory/{business_id}`

Directory users:

- Buyers discover verified sellers.
- Sellers discover reputable buyers.
- Financiers discover SMEs and receivables.
- Logistics providers become selectable proof sources.

### 3. Buyer opportunity / seller proposal flow

Buyers can post opportunities. Verified sellers can submit proposals. Buyers can accept a proposal and automatically create a trade contract.

Backend models:

- `TradeOpportunity`
- `SellerProposal`
- `TradeContract`

Key endpoints:

- `POST /api/v1/network/opportunities`
- `GET /api/v1/network/opportunities`
- `POST /api/v1/network/opportunities/{opportunity_id}/proposals`
- `GET /api/v1/network/opportunities/{opportunity_id}/proposals`
- `POST /api/v1/network/proposals/{proposal_id}/decision`

### 4. Financier marketplace

Financiers can discover fundable receivables without needing manual one-by-one invites. The marketplace aggregates receivables, buyer confirmation status, seller score, proof status, dispute state and recommended advance.

Key endpoints:

- `GET /api/v1/network/financier-marketplace/deals`
- `POST /api/v1/network/financier-marketplace/deals/{receivable_id}/express-interest`

## Main product flows

### Buyer-led private contract

1. Buyer creates trade contract.
2. Buyer selects seller by business ID or invites by email.
3. Seller accepts, rejects or requests changes.
4. Contract is activated.
5. An order is created.
6. Invoice, delivery proof, receivable, Smart LC and financing workflow continue.

### Buyer-led open opportunity

1. Buyer posts trade opportunity.
2. Sellers discover opportunity.
3. Sellers submit proposals.
4. Buyer accepts a proposal.
5. Credara creates a trade contract.
6. Contract is activated into an order.

### Seller-led flow

1. Seller lists profile or creates trade contract/invoice request.
2. Seller invites buyer.
3. Buyer confirms obligation.
4. Delivery proof and financing workflow continue.

### Financier-led flow

1. Financier opens marketplace.
2. Financier filters finance-ready receivables.
3. Financier reviews risk inputs and evidence.
4. Financier expresses interest or creates offer.
5. Offer and repayment workflow continue.

## Audit and webhook behaviour

Every network/discovery action records audit events and webhook events where appropriate:

- directory profile upserted
- counterparty invited
- relationship decided
- trade contract created/decided/activated
- opportunity created
- proposal submitted/decided
- financier interest expressed

## Production notes

Before using this layer in production, add:

- search indexes for sector/country/role fields
- anti-spam controls for invitations and proposals
- business verification gates before public listing
- admin moderation for public opportunities
- fraud controls for fake buyer demand
- notification delivery via email and webhooks
- organisation-scoped RBAC checks beyond role-level checks
- migration scripts for all new tables
