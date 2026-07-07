# Smart Contract Audit Preparation Checklist

- [ ] All functions have intended access control.
- [ ] Settlement token transfers use SafeERC20.
- [ ] ReentrancyGuard protects transfer functions.
- [ ] State transitions are explicit and tested.
- [ ] Pause/unpause behavior is tested.
- [ ] Duplicate proof/receivable prevention is tested.
- [ ] Deadlines and timeout refund paths are tested.
- [ ] Events include enough fields for backend indexing.
- [ ] Deployment scripts use the expected admin/multisig addresses.
- [ ] Slither run completed and findings triaged.
- [ ] Test coverage generated.
- [ ] Legal model for receivable assignment/LC enforceability reviewed.
- [ ] Independent auditor engaged before mainnet.
