# Smart Contract Security Hardening

The contract suite has been hardened for enterprise-grade testnet deployment readiness.

## Implemented controls

- Role-based access control across proof, receivable, LC, factory, and score contracts.
- Pause controls using `PAUSER_ROLE`.
- `SafeERC20` for settlement token transfers.
- `ReentrancyGuard` on all token movement paths.
- Strict LC state transitions.
- Funding, delivery, and confirmation deadlines.
- Dispute lock and resolver-only release/refund.
- Proof hash uniqueness and non-zero validation.
- Receivable proof hash uniqueness and explicit status transitions.
- Credit score attestation validation and pause support.
- Expanded unit tests for proof registry, receivables, and SmartLC settlement/dispute paths.

## SmartLC states

- `Created`
- `Funded`
- `DeliverySubmitted`
- `DeliveryVerified`
- `Released`
- `Refunded`
- `Disputed`
- `Cancelled`

## Production warning

These controls improve audit readiness but do not replace an independent smart contract audit. Do not deploy to mainnet until independent audit, legal review, and multisig admin setup are completed.
