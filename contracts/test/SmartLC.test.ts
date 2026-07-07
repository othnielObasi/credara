import { expect } from 'chai';
import { ethers } from 'hardhat';

async function deployFixture() {
  const [admin, buyer, seller, resolver] = await ethers.getSigners();
  const Token = await ethers.getContractFactory('MockUSDC');
  const token = await Token.deploy();
  const amount = ethers.parseUnits('1000', 6);
  await token.mint(buyer.address, amount);

  const now = (await ethers.provider.getBlock('latest'))!.timestamp;
  const orderHash = ethers.keccak256(ethers.toUtf8Bytes('order-1'));
  const SmartLC = await ethers.getContractFactory('SmartLC');
  const lc = await SmartLC.deploy(
    admin.address,
    await token.getAddress(),
    buyer.address,
    seller.address,
    amount,
    orderHash,
    now + 3600,
    now + 86400,
    300
  );
  return { admin, buyer, seller, resolver, token, amount, orderHash, lc };
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
});
