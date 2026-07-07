# Deployment Readiness Checklist

## Testnet
- [ ] POLYGON_RPC_URL configured for Amoy.
- [ ] RELAYER_PRIVATE_KEY uses a dedicated test wallet.
- [ ] Contracts compile and tests pass.
- [ ] Deployment script produces contract addresses.
- [ ] Contract addresses are copied into API/Web env files.
- [ ] Proof anchor, receivable creation, and SmartLC flow are executed end-to-end.

## Mainnet/Pilot
- [ ] Admin is multisig, not EOA.
- [ ] Relayer role is least-privilege.
- [ ] Production monitoring and alerting enabled.
- [ ] Incident pause procedure tested.
- [ ] Independent audit complete.
- [ ] Legal review complete.
