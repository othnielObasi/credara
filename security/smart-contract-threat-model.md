# Smart Contract Threat Model

## Scope
Contracts: ProofRegistry, ReceivableRegistry, SmartLC, SmartLCFactory, CreditScoreAttestation, MockUSDC.

## Primary assets
- Escrowed settlement tokens in SmartLC.
- Integrity of proof hashes and receivable status.
- Integrity of credit score attestations.
- Administrative roles and relayer keys.

## Key threats and controls
- Unauthorized settlement release: AccessControl verifier/resolver roles and strict state transitions.
- Reentrancy on token transfer: ReentrancyGuard and SafeERC20 on all transfer paths.
- Stuck funds: funding and delivery deadlines, refund path, dispute resolution path.
- Duplicate receivables: proof hash uniqueness in ReceivableRegistry.
- Fake proof anchoring: ANCHOR_ROLE and off-chain approval workflow before on-chain anchoring.
- Emergency defect response: PAUSER_ROLE on settlement, proof, receivable, factory, and attestation contracts.
- Key compromise: separate roles, hardware-backed keys recommended, admin multisig before mainnet.

## Mainnet gate
Do not deploy to mainnet until test coverage, Slither review, deployment rehearsal, legal review, and independent audit are complete.
