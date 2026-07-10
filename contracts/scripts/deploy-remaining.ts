import { ethers } from 'hardhat';

// Recovery script: MockUSDC and ProofRegistry were already deployed in an earlier
// run that ran out of gas partway through. This deploys only the remaining 3.
async function main() {
  const [deployer] = await ethers.getSigners();
  console.log('Deploying with:', deployer.address);

  const ReceivableRegistry = await ethers.getContractFactory('ReceivableRegistry');
  const receivableRegistry = await ReceivableRegistry.deploy(deployer.address);
  await receivableRegistry.waitForDeployment();

  const SmartLCFactory = await ethers.getContractFactory('SmartLCFactory');
  const smartLCFactory = await SmartLCFactory.deploy(deployer.address);
  await smartLCFactory.waitForDeployment();

  const CreditScoreAttestation = await ethers.getContractFactory('CreditScoreAttestation');
  const creditScoreAttestation = await CreditScoreAttestation.deploy(deployer.address);
  await creditScoreAttestation.waitForDeployment();

  console.log({
    receivableRegistry: await receivableRegistry.getAddress(),
    smartLCFactory: await smartLCFactory.getAddress(),
    creditScoreAttestation: await creditScoreAttestation.getAddress()
  });
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
