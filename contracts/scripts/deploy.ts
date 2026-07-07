import { ethers } from 'hardhat';

async function main() {
  const [deployer] = await ethers.getSigners();
  console.log('Deploying with:', deployer.address);

  const MockUSDC = await ethers.getContractFactory('MockUSDC');
  const mockUSDC = await MockUSDC.deploy();
  await mockUSDC.waitForDeployment();

  const ProofRegistry = await ethers.getContractFactory('ProofRegistry');
  const proofRegistry = await ProofRegistry.deploy(deployer.address);
  await proofRegistry.waitForDeployment();

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
    mockUSDC: await mockUSDC.getAddress(),
    proofRegistry: await proofRegistry.getAddress(),
    receivableRegistry: await receivableRegistry.getAddress(),
    smartLCFactory: await smartLCFactory.getAddress(),
    creditScoreAttestation: await creditScoreAttestation.getAddress()
  });
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
