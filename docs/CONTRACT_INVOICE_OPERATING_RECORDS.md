# Contract and Invoice Operating Records

This upgrade makes Credara contracts and invoices clear, stateful enterprise records.

## Trade Contract

A contract now answers:
- who is trading with whom
- what is being supplied
- delivery deadline and payment terms
- proof requirements
- financing and receivable tokenization terms
- Smart LC release/refund rules
- linked invoice, proof bundle, receivable, Smart LC and evidence bundle
- audit and Polygon state

## Invoice

An invoice now answers:
- whether the buyer has confirmed the obligation
- what line items make up the amount
- whether delivery proof is verified
- whether the invoice is receivable-eligible
- finance offer status
- Smart LC settlement state
- Polygon proof receipts
- evidence package availability

## New API Endpoints

```text
GET /api/v1/contract-invoice/contracts/{contract_id}
GET /api/v1/contract-invoice/contracts/{contract_id}/download
GET /api/v1/contract-invoice/contracts/{contract_id}/status-map

GET /api/v1/contract-invoice/invoices/{invoice_id}
GET /api/v1/contract-invoice/invoices/{invoice_id}/download
GET /api/v1/contract-invoice/invoices/{invoice_id}/status-map
```

## Downloadable Documents

Contracts and invoices are downloadable as HTML documents. Users can open or print them to PDF. Production can add PDF rendering using Playwright, WeasyPrint, wkhtmltopdf or a document-rendering service.

## Production Wiring

The router is self-contained for safe integration. Production should connect these schemas to persistent SQLAlchemy models, evidence storage and object-level access control.
