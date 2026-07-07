// SPDX-License-Identifier: MIT
pragma solidity ^0.8.28;

import {AccessControl} from "@openzeppelin/contracts/access/AccessControl.sol";
import {Pausable} from "@openzeppelin/contracts/utils/Pausable.sol";

contract CreditScoreAttestation is AccessControl, Pausable {
    bytes32 public constant ATTESTER_ROLE = keccak256("ATTESTER_ROLE");
    bytes32 public constant PAUSER_ROLE = keccak256("PAUSER_ROLE");

    struct ScoreSnapshot {
        address subject;
        uint16 score;
        string grade;
        bytes32 factorsHash;
        uint256 attestedAt;
    }

    mapping(address => ScoreSnapshot[]) private snapshots;
    event CreditScoreAttested(address indexed subject, uint16 score, string grade, bytes32 factorsHash, uint256 attestedAt);

    error InvalidSubject();
    error InvalidScore();
    error InvalidFactorsHash();
    error NoScore();

    constructor(address admin) {
        require(admin != address(0), "admin required");
        _grantRole(DEFAULT_ADMIN_ROLE, admin);
        _grantRole(ATTESTER_ROLE, admin);
        _grantRole(PAUSER_ROLE, admin);
    }

    function attest(address subject, uint16 score, string calldata grade, bytes32 factorsHash) external onlyRole(ATTESTER_ROLE) whenNotPaused {
        if (subject == address(0)) revert InvalidSubject();
        if (score > 100) revert InvalidScore();
        if (factorsHash == bytes32(0)) revert InvalidFactorsHash();
        snapshots[subject].push(ScoreSnapshot(subject, score, grade, factorsHash, block.timestamp));
        emit CreditScoreAttested(subject, score, grade, factorsHash, block.timestamp);
    }

    function latest(address subject) external view returns (ScoreSnapshot memory) {
        if (snapshots[subject].length == 0) revert NoScore();
        return snapshots[subject][snapshots[subject].length - 1];
    }

    function snapshotCount(address subject) external view returns (uint256) {
        return snapshots[subject].length;
    }

    function pause() external onlyRole(PAUSER_ROLE) { _pause(); }
    function unpause() external onlyRole(PAUSER_ROLE) { _unpause(); }
}
