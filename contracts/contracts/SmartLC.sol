// SPDX-License-Identifier: MIT
pragma solidity ^0.8.28;

import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {SafeERC20} from "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import {ReentrancyGuard} from "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import {AccessControl} from "@openzeppelin/contracts/access/AccessControl.sol";
import {Pausable} from "@openzeppelin/contracts/utils/Pausable.sol";

/// @title SmartLC
/// @notice Enterprise-grade programmable letter-of-credit escrow for verified SME trade settlement.
/// @dev Sensitive commercial data stays off-chain; only hashes/state are recorded here.
contract SmartLC is AccessControl, Pausable, ReentrancyGuard {
    using SafeERC20 for IERC20;

    bytes32 public constant VERIFIER_ROLE = keccak256("VERIFIER_ROLE");
    bytes32 public constant DISPUTE_RESOLVER_ROLE = keccak256("DISPUTE_RESOLVER_ROLE");
    bytes32 public constant PAUSER_ROLE = keccak256("PAUSER_ROLE");

    enum Status {
        Created,
        Funded,
        DeliverySubmitted,
        DeliveryVerified,
        Released,
        Refunded,
        Disputed,
        Cancelled
    }

    IERC20 public immutable settlementToken;
    address public immutable buyer;
    address public immutable seller;
    uint256 public immutable amount;
    bytes32 public immutable orderProofHash;
    uint256 public immutable fundingDeadline;
    uint256 public immutable deliveryDeadline;
    uint256 public immutable confirmationWindowSeconds;

    Status public status;
    bytes32 public deliveryProofHash;
    bytes32 public disputeReasonHash;
    uint256 public deliverySubmittedAt;
    uint256 public deliveryVerifiedAt;

    event LCFunded(bytes32 indexed orderProofHash, address indexed buyer, uint256 amount);
    event DeliverySubmitted(bytes32 indexed orderProofHash, address indexed seller, bytes32 deliveryProofHash);
    event DeliveryVerified(bytes32 indexed orderProofHash, address indexed verifier, bytes32 deliveryProofHash);
    event LCReleased(bytes32 indexed orderProofHash, address indexed seller, uint256 amount, bytes32 deliveryProofHash);
    event LCDisputed(bytes32 indexed orderProofHash, address indexed reporter, bytes32 reasonHash);
    event LCRefunded(bytes32 indexed orderProofHash, address indexed buyer, uint256 amount);
    event LCCancelled(bytes32 indexed orderProofHash, address indexed buyer);

    error InvalidAddress();
    error InvalidAmount();
    error InvalidProofHash();
    error InvalidDeadline();
    error InvalidState(Status current);
    error OnlyBuyer();
    error OnlySeller();
    error FundingExpired();
    error DeliveryExpired();
    error ConfirmationWindowOpen();

    constructor(
        address admin,
        IERC20 token,
        address buyer_,
        address seller_,
        uint256 amount_,
        bytes32 orderProofHash_,
        uint256 fundingDeadline_,
        uint256 deliveryDeadline_,
        uint256 confirmationWindowSeconds_
    ) {
        if (admin == address(0) || address(token) == address(0) || buyer_ == address(0) || seller_ == address(0)) revert InvalidAddress();
        if (amount_ == 0) revert InvalidAmount();
        if (orderProofHash_ == bytes32(0)) revert InvalidProofHash();
        if (fundingDeadline_ <= block.timestamp || deliveryDeadline_ <= fundingDeadline_) revert InvalidDeadline();
        if (confirmationWindowSeconds_ == 0) revert InvalidDeadline();

        settlementToken = token;
        buyer = buyer_;
        seller = seller_;
        amount = amount_;
        orderProofHash = orderProofHash_;
        fundingDeadline = fundingDeadline_;
        deliveryDeadline = deliveryDeadline_;
        confirmationWindowSeconds = confirmationWindowSeconds_;
        status = Status.Created;

        _grantRole(DEFAULT_ADMIN_ROLE, admin);
        _grantRole(VERIFIER_ROLE, admin);
        _grantRole(DISPUTE_RESOLVER_ROLE, admin);
        _grantRole(PAUSER_ROLE, admin);
    }

    function fund() external nonReentrant whenNotPaused {
        if (msg.sender != buyer) revert OnlyBuyer();
        if (status != Status.Created) revert InvalidState(status);
        if (block.timestamp > fundingDeadline) revert FundingExpired();

        status = Status.Funded;
        settlementToken.safeTransferFrom(msg.sender, address(this), amount);
        emit LCFunded(orderProofHash, msg.sender, amount);
    }

    function cancelUnfunded() external whenNotPaused {
        if (msg.sender != buyer) revert OnlyBuyer();
        if (status != Status.Created) revert InvalidState(status);
        status = Status.Cancelled;
        emit LCCancelled(orderProofHash, msg.sender);
    }

    function submitDelivery(bytes32 proofHash) external whenNotPaused {
        if (msg.sender != seller && !hasRole(VERIFIER_ROLE, msg.sender)) revert OnlySeller();
        if (status != Status.Funded) revert InvalidState(status);
        if (block.timestamp > deliveryDeadline) revert DeliveryExpired();
        if (proofHash == bytes32(0)) revert InvalidProofHash();

        deliveryProofHash = proofHash;
        deliverySubmittedAt = block.timestamp;
        status = Status.DeliverySubmitted;
        emit DeliverySubmitted(orderProofHash, seller, proofHash);
    }

    function verifyDelivery(bytes32 proofHash) external onlyRole(VERIFIER_ROLE) whenNotPaused {
        if (status != Status.DeliverySubmitted) revert InvalidState(status);
        if (proofHash == bytes32(0) || proofHash != deliveryProofHash) revert InvalidProofHash();

        deliveryVerifiedAt = block.timestamp;
        status = Status.DeliveryVerified;
        emit DeliveryVerified(orderProofHash, msg.sender, proofHash);
    }

    function release() external onlyRole(VERIFIER_ROLE) nonReentrant whenNotPaused {
        _release();
    }

    function releaseAfterConfirmationWindow() external nonReentrant whenNotPaused {
        if (status != Status.DeliveryVerified) revert InvalidState(status);
        if (block.timestamp < deliveryVerifiedAt + confirmationWindowSeconds) revert ConfirmationWindowOpen();
        _release();
    }

    function dispute(bytes32 reasonHash) external whenNotPaused {
        if (msg.sender != buyer && msg.sender != seller && !hasRole(VERIFIER_ROLE, msg.sender)) revert InvalidAddress();
        if (status != Status.Funded && status != Status.DeliverySubmitted && status != Status.DeliveryVerified) revert InvalidState(status);
        if (reasonHash == bytes32(0)) revert InvalidProofHash();

        disputeReasonHash = reasonHash;
        status = Status.Disputed;
        emit LCDisputed(orderProofHash, msg.sender, reasonHash);
    }

    function resolveDisputeRelease() external onlyRole(DISPUTE_RESOLVER_ROLE) nonReentrant whenNotPaused {
        if (status != Status.Disputed) revert InvalidState(status);
        _release();
    }

    function resolveDisputeRefund() external onlyRole(DISPUTE_RESOLVER_ROLE) nonReentrant whenNotPaused {
        if (status != Status.Disputed) revert InvalidState(status);
        _refund();
    }

    function refundExpiredDelivery() external nonReentrant whenNotPaused {
        if (msg.sender != buyer) revert OnlyBuyer();
        if (status != Status.Funded) revert InvalidState(status);
        if (block.timestamp <= deliveryDeadline) revert InvalidDeadline();
        _refund();
    }

    function pause() external onlyRole(PAUSER_ROLE) { _pause(); }
    function unpause() external onlyRole(PAUSER_ROLE) { _unpause(); }

    function _release() private {
        if (status != Status.DeliveryVerified && status != Status.Disputed) revert InvalidState(status);
        status = Status.Released;
        settlementToken.safeTransfer(seller, amount);
        emit LCReleased(orderProofHash, seller, amount, deliveryProofHash);
    }

    function _refund() private {
        status = Status.Refunded;
        settlementToken.safeTransfer(buyer, amount);
        emit LCRefunded(orderProofHash, buyer, amount);
    }
}
