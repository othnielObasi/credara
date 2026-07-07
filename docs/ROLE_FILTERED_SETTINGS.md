# Role-Filtered Navigation and Settings

## Purpose

v10 makes the signed-in workspace role-aware and moves platform/API controls into user profile/settings.

## UI Behaviour

Pages are automatically filtered based on the selected workspace role:

- SME sees trade, proof, receivables, settlement and trust tools.
- Buyer sees confirmations, obligations, escrow, settlement and evidence.
- Financier sees marketplace, underwriting, evidence, funding and repayment.
- Admin sees risk, KYB, audit, settlement exceptions and platform controls.
- Developer sees setup and API/webhook settings under Settings.

## Settings

Settings now includes:

- Profile
- Workspace
- Notifications
- Security
- API & Webhooks
- Billing / Limits
- Admin Preferences

API Explorer and Permissions are no longer primary workflow nav items. They are surfaced through Settings where appropriate.

## Backend Endpoints

```text
GET /api/v1/settings/navigation/{role}
GET /api/v1/settings/me/{role}
PUT /api/v1/settings/me/{role}
GET /api/v1/settings/settings-tabs/{role}
GET /api/v1/settings/api-access/{role}
```

## Design Rationale

The main app nav should focus on real trade finance actions. Platform configuration belongs under the user's profile/settings area.
