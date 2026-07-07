import { expect } from 'chai';
import { ethers } from 'hardhat';

describe('ReceivableRegistry', function () {
  it('creates, finances, and settles receivables with strict transitions', async function () {
    const [admin, seller, debtor, financier] = await ethers.getSigners();
    const Registry = await ethers.getContractFactory('ReceivableRegistry');
    const registry = await Registry.deploy(admin.address);
    const proofHash = ethers.keccak256(ethers.toUtf8Bytes('invoice-1'));
    const now = (await ethers.provider.getBlock('latest'))!.timestamp;
    await expect(registry.createReceivable(seller.address, debtor.address, 1000, now + 86400, proofHash)).to.emit(registry, 'ReceivableCreated');
    await expect(registry.createReceivable(seller.address, debtor.address, 1000, now + 86400, proofHash)).to.be.revertedWithCustomError(registry, 'DuplicateProofHash');
    await expect(registry.markFinanced(1, financier.address)).to.emit(registry, 'ReceivableFinanced');
    await expect(registry.markSettled(1)).to.emit(registry, 'ReceivableSettled');
    await expect(registry.markDefaulted(1)).to.be.revertedWithCustomError(registry, 'InvalidState');
  });
});
