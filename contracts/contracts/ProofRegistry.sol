// SPDX-License-Identifier: MIT
pragma solidity ^0.8.28;

import {AccessControl} from "@openzeppelin/contracts/access/AccessControl.sol";
import {Pausable} from "@openzeppelin/contracts/utils/Pausable.sol";

contract ProofRegistry is AccessControl, Pausable {
    bytes32 public constant ANCHOR_ROLE = keccak256("ANCHOR_ROLE");
    bytes32 public constant PAUSER_ROLE = keccak256("PAUSER_ROLE");

    struct ProofRecord {
        bytes32 proofHash;
        string proofType;
        address subject;
        uint256 anchoredAt;
        string metadataURI;
        bool exists;
    }

    mapping(bytes32 => ProofRecord) public proofs;

    event ProofAnchored(bytes32 indexed proofHash, string proofType, address indexed subject, string metadataURI, uint256 anchoredAt);

    error InvalidProofHash();
    error EmptyProofType();
    error ProofAlreadyExists();
    error InvalidSubject();

    constructor(address admin) {
        require(admin != address(0), "admin required");
        _grantRole(DEFAULT_ADMIN_ROLE, admin);
        _grantRole(ANCHOR_ROLE, admin);
        _grantRole(PAUSER_ROLE, admin);
    }

    function anchorProof(bytes32 proofHash, string calldata proofType, address subject, string calldata metadataURI) external onlyRole(ANCHOR_ROLE) whenNotPaused {
        if (proofHash == bytes32(0)) revert InvalidProofHash();
        if (bytes(proofType).length == 0) revert EmptyProofType();
        if (subject == address(0)) revert InvalidSubject();
        if (proofs[proofHash].exists) revert ProofAlreadyExists();

        proofs[proofHash] = ProofRecord(proofHash, proofType, subject, block.timestamp, metadataURI, true);
        emit ProofAnchored(proofHash, proofType, subject, metadataURI, block.timestamp);
    }

    function pause() external onlyRole(PAUSER_ROLE) { _pause(); }
    function unpause() external onlyRole(PAUSER_ROLE) { _unpause(); }
}
