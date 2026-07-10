import { ethers } from 'hardhat';

// Redeploy after hardening SmartLC/SmartLCFactory: separated verifier/dispute-resolver/
// pauser roles instead of collapsing them onto one admin address, and added a
// permissionless dispute-timeout fallback. The previously deployed factory still
// runs the old bytecode, so it needs a fresh instance.
async function main() {
  const [deployer] = await ethers.getSigners();
  console.log('Deploying with:', deployer.address);

  const SmartLCFactory = await ethers.getContractFactory('SmartLCFactory');
  const smartLCFactory = await SmartLCFactory.deploy(deployer.address);
  await smartLCFactory.waitForDeployment();

  console.log({ smartLCFactory: await smartLCFactory.getAddress() });
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
