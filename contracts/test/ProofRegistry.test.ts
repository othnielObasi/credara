import { expect } from 'chai';
import { ethers } from 'hardhat';

describe('ProofRegistry', function () {
  it('anchors a unique proof hash and rejects duplicates', async function () {
    const [admin, subject] = await ethers.getSigners();
    const Factory = await ethers.getContractFactory('ProofRegistry');
    const registry = await Factory.deploy(admin.address);
    const hash = ethers.keccak256(ethers.toUtf8Bytes('proof'));

    await expect(registry.anchorProof(hash, 'INVOICE', subject.address, 'ipfs://meta')).to.emit(registry, 'ProofAnchored');
    await expect(registry.anchorProof(hash, 'INVOICE', subject.address, 'ipfs://meta')).to.be.revertedWithCustomError(registry, 'ProofAlreadyExists');
  });

  it('pauses proof anchoring', async function () {
    const [admin, subject] = await ethers.getSigners();
    const Factory = await ethers.getContractFactory('ProofRegistry');
    const registry = await Factory.deploy(admin.address);
    await registry.pause();
    const hash = ethers.keccak256(ethers.toUtf8Bytes('proof'));
    await expect(registry.anchorProof(hash, 'INVOICE', subject.address, 'ipfs://meta')).to.be.revertedWithCustomError(registry, 'EnforcedPause');
  });
});
