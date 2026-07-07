# KYB Provider Abstraction

Credara supports a provider-agnostic KYB architecture. The app can run with `KYB_PROVIDER=mock` for local/demo mode and switch to `KYB_PROVIDER=didit` for real verification via [Didit](https://docs.didit.me) without rewriting the business workflow.

## Internal KYB flow

1. SME creates a business profile.
2. SME creates/updates KYB profile at `/api/v1/kyb/profiles/{business_id}`.
3. SME uploads document metadata at `/api/v1/kyb/profiles/{business_id}/documents`.
4. SME submits KYB at `/api/v1/kyb/profiles/{business_id}/submit`.
5. Provider abstraction creates applicant, uploads documents, starts check.
6. Provider webhook updates profile status at `/api/v1/kyb/webhooks/{provider}`.
7. KYB status controls financing eligibility and transaction limits.

## Provider contract

All providers implement:

- `create_applicant`
- `upload_document`
- `start_check`
- `get_check_status`
- `parse_webhook`

## Supported provider keys

```env
KYB_PROVIDER=mock
DIDIT_API_KEY=
DIDIT_WORKFLOW_ID=
DIDIT_WEBHOOK_SECRET=
```

## Didit integration notes

Didit runs verification as a single hosted session rather than a document-by-document
upload API (base URL `https://verification.didit.me`, `x-api-key` auth):

- `create_applicant` calls `POST /v3/session/` with the configured `DIDIT_WORKFLOW_ID`
  and returns a hosted `url` (inside the raw response) that the business must complete.
- `upload_document` is a local no-op - documents are captured inside Didit's hosted
  session, not via a separate API call.
- `start_check` / `get_check_status` call `GET /v3/session/{id}/decision/`.
- The decision normally arrives asynchronously via webhook at
  `POST /api/v1/kyb/webhooks/didit`, verified using the `X-Signature-V2` +
  `X-Timestamp` headers (HMAC-SHA256 over canonical sorted JSON, 5-minute replay
  tolerance) against `DIDIT_WEBHOOK_SECRET`.

## Internal normalized statuses

- `not_started`
- `draft`
- `submitted`
- `pending_review`
- `approved`
- `rejected`
- `needs_more_info`
- `manual_review`
- `expired`
- `suspended`

## Demo behavior

The mock provider is deterministic:

- normal registrations are approved with low risk
- registration number ending in `BLOCK` is rejected
- country in the sandbox high-risk list is routed to manual review

This allows demos without live KYB credentials while preserving the production integration contract.
