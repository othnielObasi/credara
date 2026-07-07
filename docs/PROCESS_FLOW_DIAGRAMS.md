# Credara Process Flow Diagrams

These Mermaid diagrams can be rendered in GitHub, many documentation portals, and engineering tools that support Mermaid.

---

## 1. Overall Credara Trade Finance Loop

```mermaid
flowchart TD
    A[SME Onboards] --> B[KYB Verification]
    B -->|Approved| C[Buyer Creates Order]
    C --> D[Seller Accepts Order]
    D --> E[Invoice Created]
    E --> F[Buyer Confirms Invoice]
    F --> G[Delivery Proof Submitted]
    G --> H[Buyer OTP / Logistics Verification]
    H --> I[Proof Bundle Hashed]
    I --> J[Polygon Proof Anchored]
    J --> K[Receivable Created]
    K --> L[Trade Credit Score Updated]
    L --> M[Financier Reviews]
    M --> N[Smart LC / Invoice Finance Funded]
    N --> O[Settlement Released]
    O --> P[Proof Ledger + Score Updated]
```

---

## 2. KYB Flow

```mermaid
sequenceDiagram
    participant SME
    participant API as Credara API
    participant KYB as KYB Provider
    participant Admin as Risk Admin
    SME->>API: Submit business profile + documents
    API->>API: Store file hashes and KYB profile
    API->>KYB: Create applicant / start check
    KYB-->>API: Provider applicant/check ID
    API-->>SME: KYB pending
    KYB-->>API: Webhook status update
    API->>API: Verify webhook + map status
    alt Approved
        API-->>SME: KYB approved
    else Needs review
        API-->>Admin: Queue manual review
        Admin->>API: Approve or reject with reason
        API-->>SME: Final KYB status
    else Rejected
        API-->>SME: KYB rejected / finance blocked
    end
```

---

## 3. Invoice to Tokenized Receivable

```mermaid
flowchart TD
    A[Accepted Order] --> B[Seller Creates Invoice]
    B --> C[Invoice Hash Generated]
    C --> D[Buyer Confirmation Request]
    D -->|Confirmed| E[Invoice Buyer Confirmed]
    D -->|Disputed| X[Invoice Dispute]
    E --> F[Delivery Proof Verified?]
    F -->|Yes| G[Receivable Eligibility Check]
    F -->|No| Y[Conditional / Not Eligible]
    G --> H[Create Receivable DB Record]
    H --> I[Outbox Event]
    I --> J[ReceivableRegistry.createReceivable]
    J --> K[On-chain Receivable Event]
    K --> L[Indexer Updates Local Status]
    L --> M[Financier Dashboard]
```

---

## 4. Delivery Proof Verification

```mermaid
flowchart TD
    A[Seller Uploads Proof] --> B[Hash Evidence Bundle]
    B --> C[Check Duplicate Hash]
    C --> D[Validate Order/Invoice Match]
    D --> E[Check Timestamp/GPS Metadata]
    E --> F[OTP or QR Confirmation]
    F --> G[Buyer Confirmation]
    G --> H[Optional Logistics Verification]
    H --> I[Calculate Proof Confidence]
    I -->|High/Very High| J[Mark Delivery Verified]
    I -->|Medium| K[Require Buyer/Admin Review]
    I -->|Low| L[Reject or Manual Review]
    J --> M[Anchor Proof Hash on Polygon]
    M --> N[Enable Settlement / Receivable]
```

---

## 5. Smart LC Settlement

```mermaid
stateDiagram-v2
    [*] --> CREATED
    CREATED --> FUNDED: buyer/financier funds LC
    FUNDED --> DELIVERY_SUBMITTED: seller submits proof
    DELIVERY_SUBMITTED --> DELIVERY_VERIFIED: verifier confirms proof
    DELIVERY_VERIFIED --> RELEASED: release funds to seller
    DELIVERY_SUBMITTED --> DISPUTED: buyer/admin disputes
    FUNDED --> CANCELLED: deadline missed/cancelled
    DISPUTED --> RELEASED: resolver approves seller
    DISPUTED --> REFUNDED: resolver approves buyer
    CANCELLED --> REFUNDED
    RELEASED --> [*]
    REFUNDED --> [*]
```

---

## 6. Blockchain Outbox and Relayer

```mermaid
sequenceDiagram
    participant UI
    participant API as Credara API
    participant DB as Database + Outbox
    participant Relayer
    participant Chain as Polygon Amoy/PoS
    participant Indexer
    UI->>API: Request proof anchor / receivable / LC action
    API->>DB: Save domain record + outbox event atomically
    API-->>UI: Pending chain status
    Relayer->>DB: Poll pending outbox
    Relayer->>Chain: Submit contract transaction
    Chain-->>Relayer: Transaction hash
    Relayer->>DB: Store tx hash and submitted status
    Indexer->>Chain: Read transaction/events
    Indexer->>DB: Mark confirmed and update domain record
    UI->>API: Fetch proof ledger
    API-->>UI: Confirmed tx link and status
```

---

## 7. Credit Score Attestation

```mermaid
flowchart TD
    A[Verified Trade Events] --> B[Score Worker]
    C[KYB Status] --> B
    D[Dispute History] --> B
    E[Settlement / Repayment History] --> B
    F[Buyer Diversity] --> B
    B --> G[Calculate Versioned Score]
    G --> H[Generate Explanation]
    H --> I[Store Score Snapshot]
    I --> J[Hash Snapshot]
    J --> K[CreditScoreAttestation Contract]
    K --> L[On-chain Score Attestation]
    L --> M[Financier / SME Dashboard]
```

---

## 8. Dispute and Settlement Freeze

```mermaid
flowchart TD
    A[Buyer/Seller Opens Dispute] --> B[Freeze Settlement Actions]
    B --> C[Freeze Receivable Financing]
    C --> D[Queue Admin Review]
    D --> E[Review Invoice, Delivery, OTP, Logistics, Messages]
    E --> F{Decision}
    F -->|Seller wins| G[Release Settlement]
    F -->|Buyer wins| H[Refund Buyer]
    F -->|Partial| I[Partial Release / Partial Refund]
    F -->|Correction| J[Request Document Correction]
    G --> K[Anchor Dispute Outcome]
    H --> K
    I --> K
    J --> K
    K --> L[Update Trust Score]
```

