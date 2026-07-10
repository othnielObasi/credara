import { expect } from 'chai';
import { ethers } from 'hardhat';

const DISPUTE_WINDOW = 600;

async function deployFixture(overrides: Partial<{ verifier: string; disputeResolver: string; pauser: string }> = {}) {
  const [admin, buyer, seller, resolver, verifierSigner, pauserSigner] = await ethers.getSigners();
  const Token = await ethers.getContractFactory('MockUSDC');
  const token = await Token.deploy();
  const amount = ethers.parseUnits('1000', 6);
  await token.mint(buyer.address, amount);

  const now = (await ethers.provider.getBlock('latest'))!.timestamp;
  const orderHash = ethers.keccak256(ethers.toUtf8Bytes('order-1'));
  const SmartLC = await ethers.getContractFactory('SmartLC');
  const lc = await SmartLC.deploy(
    admin.address,
    overrides.verifier ?? admin.address,
    overrides.disputeResolver ?? admin.address,
    overrides.pauser ?? admin.address,
    await token.getAddress(),
    buyer.address,
    seller.address,
    amount,
    orderHash,
    now + 3600,
    now + 86400,
    300,
    DISPUTE_WINDOW
  );
  return { admin, buyer, seller, resolver, verifierSigner, pauserSigner, token, amount, orderHash, lc };
}

describe('SmartLC', function () {
  it('funds, verifies delivery, and releases to seller', async function () {
    const { buyer, seller, token, amount, lc } = await deployFixture();
    await token.connect(buyer).approve(await lc.getAddress(), amount);
    await expect(lc.connect(buyer).fund()).to.emit(lc, 'LCFunded');

    const deliveryHash = ethers.keccak256(ethers.toUtf8Bytes('delivery-proof'));
    await expect(lc.connect(seller).submitDelivery(deliveryHash)).to.emit(lc, 'DeliverySubmitted');
    await expect(lc.verifyDelivery(deliveryHash)).to.emit(lc, 'DeliveryVerified');
    await expect(lc.release()).to.emit(lc, 'LCReleased');
    expect(await token.balanceOf(seller.address)).to.equal(amount);
  });

  it('blocks release before delivery verification', async function () {
    const { buyer, token, amount, lc } = await deployFixture();
    await token.connect(buyer).approve(await lc.getAddress(), amount);
    await lc.connect(buyer).fund();
    await expect(lc.release()).to.be.revertedWithCustomError(lc, 'InvalidState');
  });

  it('allows dispute resolver to refund a disputed LC', async function () {
    const { admin, buyer, seller, token, amount, lc } = await deployFixture();
    await token.connect(buyer).approve(await lc.getAddress(), amount);
    await lc.connect(buyer).fund();
    const deliveryHash = ethers.keccak256(ethers.toUtf8Bytes('delivery-proof'));
    await lc.connect(seller).submitDelivery(deliveryHash);
    await lc.connect(buyer).dispute(ethers.keccak256(ethers.toUtf8Bytes('damaged')));
    await expect(lc.connect(admin).resolveDisputeRefund()).to.emit(lc, 'LCRefunded');
    expect(await token.balanceOf(buyer.address)).to.equal(amount);
  });

  it('pauses settlement operations', async function () {
    const { buyer, token, amount, lc } = await deployFixture();
    await lc.pause();
    await token.connect(buyer).approve(await lc.getAddress(), amount);
    await expect(lc.connect(buyer).fund()).to.be.revertedWithCustomError(lc, 'EnforcedPause');
  });

  it('grants verifier, dispute-resolver, and pauser roles to distinct addresses', async function () {
    const signers = await ethers.getSigners();
    const { verifierSigner, resolver, pauserSigner, lc } = await deployFixture({
      verifier: signers[4].address,
      disputeResolver: signers[3].address,
      pauser: signers[5].address,
    });
    expect(await lc.hasRole(await lc.VERIFIER_ROLE(), verifierSigner.address)).to.equal(true);
    expect(await lc.hasRole(await lc.DISPUTE_RESOLVER_ROLE(), resolver.address)).to.equal(true);
    expect(await lc.hasRole(await lc.PAUSER_ROLE(), pauserSigner.address)).to.equal(true);
    // A verifier holding only VERIFIER_ROLE cannot resolve disputes or pause -
    // compromising that one key no longer compromises the other two roles.
    expect(await lc.hasRole(await lc.DISPUTE_RESOLVER_ROLE(), verifierSigner.address)).to.equal(false);
    expect(await lc.hasRole(await lc.PAUSER_ROLE(), verifierSigner.address)).to.equal(false);
  });

  it('lets anyone refund after the dispute window expires with no resolver action', async function () {
    const { buyer, seller, token, amount, lc } = await deployFixture();
    await token.connect(buyer).approve(await lc.getAddress(), amount);
    await lc.connect(buyer).fund();
    const deliveryHash = ethers.keccak256(ethers.toUtf8Bytes('delivery-proof'));
    await lc.connect(seller).submitDelivery(deliveryHash);
    await lc.connect(buyer).dispute(ethers.keccak256(ethers.toUtf8Bytes('damaged')));

    await expect(lc.connect(buyer).resolveDisputeTimeout()).to.be.revertedWithCustomError(lc, 'DisputeWindowOpen');

    await ethers.provider.send('evm_increaseTime', [DISPUTE_WINDOW + 1]);
    await ethers.provider.send('evm_mine', []);

    await expect(lc.connect(buyer).resolveDisputeTimeout()).to.emit(lc, 'LCRefunded');
    expect(await token.balanceOf(buyer.address)).to.equal(amount);
  });
});
