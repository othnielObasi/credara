# Onboarding and Invitation Flows

## Purpose

Credara users enter through three paths:

1. Self-signup
2. Counterparty invitation
3. Enterprise/API onboarding

The onboarding sequence is:

```text
Identity → Role → Business Profile → KYB → Wallet → First Workflow
```

## Why this matters

Trade finance is relationship-driven. Invitation onboarding is therefore first-class:
- buyer invites seller to a trade contract
- seller invites buyer to confirm an invoice
- seller/platform invites financier to review a receivable
- enterprise partner onboards via API keys and webhooks

## Backend endpoints

```text
GET  /api/v1/onboarding/progress
GET  /api/v1/onboarding/business-profile
POST /api/v1/onboarding/business-profile
GET  /api/v1/onboarding/role-routing

GET  /api/v1/onboarding/invitations
POST /api/v1/onboarding/invitations
GET  /api/v1/onboarding/invitations/{invitation_id}
POST /api/v1/onboarding/invitations/{invitation_id}/decision

GET  /api/v1/onboarding/members
GET  /api/v1/onboarding/setup-checklist
```

## Clerk integration

Clerk handles the person. Credara handles:
- organisation / business profile
- membership
- role
- KYB state
- wallet state
- permissions
- workflow routing
