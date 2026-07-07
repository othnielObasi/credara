# Network Discovery API Reference

## Summary

The network discovery API lets Credara support private trade workflows, discoverable markets and financier deal discovery.

Base prefix: `/api/v1/network`

## Directory

### List directory profiles

`GET /network/directory`

Query parameters:

- `role_type`: buyer, seller, financier, logistics
- `sector`: sector keyword
- `country`: ISO country code
- `q`: text search over name, headline and description

### Upsert directory profile

`POST /network/directory/{business_id}`

Request:

```json
{
  "display_name": "Acme Textiles Ltd",
  "role_type": "seller",
  "headline": "Verified textile supplier for UAE buyers",
  "description": "Supplier with verified delivery history and receivable financing support.",
  "sectors_json": ["Textiles"],
  "countries_json": ["AE"],
  "capabilities_json": ["Verified delivery", "Smart LC settlement", "Receivable financing"],
  "preferred_currencies_json": ["USDC"],
  "contact_email": "trade@acme.example",
  "visibility": "network",
  "discovery_status": "listed"
}
```

## Counterparty relationships

### Create invitation

`POST /network/invitations`

Request:

```json
{
  "requester_business_id": "buyer-business-id",
  "counterparty_business_id": "seller-business-id",
  "relationship_type": "buyer_seller",
  "invited_email": "seller@example.com",
  "invited_business_name": "Acme Textiles Ltd",
  "invitation_message": "Please review this trade relationship invitation."
}
```

### List invitations

`GET /network/invitations?status=invited&relationship_type=buyer_seller`

### Decide invitation

`POST /network/invitations/{relationship_id}/decision`

```json
{
  "decision": "accepted",
  "reason": "Commercial relationship confirmed"
}
```

## Trade contracts

### Create trade contract

`POST /network/trade-contracts`

```json
{
  "buyer_business_id": "buyer-business-id",
  "seller_business_id": "seller-business-id",
  "buyer_name": "Global Retail Ltd",
  "seller_name": "Acme Textiles Ltd",
  "title": "Textile supply contract",
  "description": "Supply of verified textile units to Dubai warehouse.",
  "amount": 24500,
  "currency": "USDC",
  "delivery_terms": "Delivered duty paid",
  "payment_terms": "45 days",
  "smart_lc_required": true,
  "financing_allowed": true
}
```

### List trade contracts

`GET /network/trade-contracts?status=active&business_id=...`

### Accept/reject/request changes

`POST /network/trade-contracts/{contract_id}/decision`

```json
{
  "decision": "accepted",
  "reason": "Terms accepted"
}
```

### Activate contract into order

`POST /network/trade-contracts/{contract_id}/activate`

Returns an `OrderRead` object. The normal invoice, proof, receivable and settlement workflow can then continue.

## Opportunities and proposals

### Create buyer opportunity

`POST /network/opportunities`

```json
{
  "buyer_business_id": "buyer-business-id",
  "title": "Verified textile supplier needed",
  "description": "Buyer needs 5,000 textile units delivered to Dubai.",
  "sector": "Textiles",
  "country": "AE",
  "delivery_location": "Jebel Ali Free Zone",
  "amount_min": 20000,
  "amount_max": 50000,
  "currency": "USDC",
  "payment_terms": "45 days",
  "smart_lc_required": true,
  "financing_allowed": true,
  "visibility": "network"
}
```

### List opportunities

`GET /network/opportunities?sector=Textiles&country=AE&status=open`

### Submit seller proposal

`POST /network/opportunities/{opportunity_id}/proposals`

```json
{
  "seller_business_id": "seller-business-id",
  "seller_name": "Acme Textiles Ltd",
  "amount": 24500,
  "currency": "USDC",
  "delivery_terms": "14 days after purchase order",
  "message": "We can fulfil the first batch with verified logistics proof."
}
```

### Decide proposal

`POST /network/proposals/{proposal_id}/decision`

```json
{
  "decision": "accepted",
  "reason": "Supplier meets quality, delivery and finance requirements",
  "create_contract": true
}
```

When `create_contract` is true and the proposal is accepted, Credara creates a trade contract.

## Financier marketplace

### List finance-ready deals

`GET /network/financier-marketplace/deals?min_amount=10000&currency=USDC`

Each item includes:

- receivable ID
- seller business ID
- debtor/buyer name
- face value
- maturity date
- recommended advance
- proof hash
- Polygon tx hash
- risk inputs

### Express funding interest

`POST /network/financier-marketplace/deals/{receivable_id}/express-interest`

Creates a financing offer in `interested` state using an indicative 80% advance and 0.5% fee basis.
