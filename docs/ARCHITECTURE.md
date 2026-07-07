# Credara Architecture

Credara is an enterprise trade-finance operating system with a demo-ready hackathon surface.

## Bounded contexts

- Identity and RBAC
- Business onboarding and KYB
- Orders and invoices
- Delivery proof verification
- Proof bundle generation
- Receivable tokenization
- Smart LC settlement
- Trade credit scoring
- Finance readiness reporting
- Polygon relayer and indexer
- Audit and risk console

## Enterprise principle

The UI may demonstrate seeded flows, but the backend, contracts and data model are structured for production pilots. Critical business state is not hidden in UI state; it is persisted, audited and anchored through explicit services.

## Polygon use

- Amoy testnet for hackathon demo.
- Polygon PoS for pilot/mainnet.
- Proof hashes and state transitions are anchored on-chain.
- Sensitive trade documents remain off-chain.
- Account abstraction/paymaster support is planned for production onboarding.
- CDK/AggLayer are roadmap options for bank/port/regulatory corridors.
