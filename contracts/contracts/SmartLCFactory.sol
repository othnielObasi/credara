// SPDX-License-Identifier: MIT
pragma solidity ^0.8.28;

import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {AccessControl} from "@openzeppelin/contracts/access/AccessControl.sol";
import {Pausable} from "@openzeppelin/contracts/utils/Pausable.sol";
import {SmartLC} from "./SmartLC.sol";

contract SmartLCFactory is AccessControl, Pausable {
    bytes32 public constant CREATOR_ROLE = keccak256("CREATOR_ROLE");
    bytes32 public constant PAUSER_ROLE = keccak256("PAUSER_ROLE");

    event SmartLCCreated(
        address indexed lc,
        address indexed buyer,
        address indexed seller,
        uint256 amount,
        bytes32 orderProofHash,
        uint256 fundingDeadline,
        uint256 deliveryDeadline
    );

    constructor(address admin) {
        require(admin != address(0), "admin required");
        _grantRole(DEFAULT_ADMIN_ROLE, admin);
        _grantRole(CREATOR_ROLE, admin);
        _grantRole(PAUSER_ROLE, admin);
    }

    function createSmartLC(
        address verifier,
        address disputeResolver,
        address pauser,
        IERC20 token,
        address buyer,
        address seller,
        uint256 amount,
        bytes32 orderProofHash,
        uint256 fundingDeadline,
        uint256 deliveryDeadline,
        uint256 confirmationWindowSeconds,
        uint256 disputeResolutionWindowSeconds
    ) external onlyRole(CREATOR_ROLE) whenNotPaused returns (address) {
        SmartLC lc = new SmartLC(
            msg.sender,
            verifier,
            disputeResolver,
            pauser,
            token,
            buyer,
            seller,
            amount,
            orderProofHash,
            fundingDeadline,
            deliveryDeadline,
            confirmationWindowSeconds,
            disputeResolutionWindowSeconds
        );
        emit SmartLCCreated(address(lc), buyer, seller, amount, orderProofHash, fundingDeadline, deliveryDeadline);
        return address(lc);
    }

    function pause() external onlyRole(PAUSER_ROLE) { _pause(); }
    function unpause() external onlyRole(PAUSER_ROLE) { _unpause(); }
}
