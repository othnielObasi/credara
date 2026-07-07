// SPDX-License-Identifier: MIT
pragma solidity ^0.8.28;

import {AccessControl} from "@openzeppelin/contracts/access/AccessControl.sol";
import {Pausable} from "@openzeppelin/contracts/utils/Pausable.sol";

contract ReceivableRegistry is AccessControl, Pausable {
    bytes32 public constant ISSUER_ROLE = keccak256("ISSUER_ROLE");
    bytes32 public constant FINANCIER_ROLE = keccak256("FINANCIER_ROLE");
    bytes32 public constant SETTLER_ROLE = keccak256("SETTLER_ROLE");
    bytes32 public constant PAUSER_ROLE = keccak256("PAUSER_ROLE");

    enum Status { Created, Financed, Settled, Defaulted, Cancelled }

    struct Receivable {
        uint256 id;
        address seller;
        address debtor;
        uint256 faceValue;
        uint256 maturityDate;
        bytes32 proofHash;
        Status status;
        address financier;
    }

    uint256 public nextId = 1;
    mapping(uint256 => Receivable) public receivables;
    mapping(bytes32 => bool) public usedProofHashes;

    event ReceivableCreated(uint256 indexed id, address indexed seller, address indexed debtor, uint256 faceValue, uint256 maturityDate, bytes32 proofHash);
    event ReceivableFinanced(uint256 indexed id, address indexed financier);
    event ReceivableSettled(uint256 indexed id);
    event ReceivableDefaulted(uint256 indexed id);
    event ReceivableCancelled(uint256 indexed id);

    error InvalidAddress();
    error InvalidAmount();
    error InvalidMaturityDate();
    error InvalidProofHash();
    error DuplicateProofHash();
    error ReceivableNotFound();
    error InvalidState(Status current);

    constructor(address admin) {
        require(admin != address(0), "admin required");
        _grantRole(DEFAULT_ADMIN_ROLE, admin);
        _grantRole(ISSUER_ROLE, admin);
        _grantRole(FINANCIER_ROLE, admin);
        _grantRole(SETTLER_ROLE, admin);
        _grantRole(PAUSER_ROLE, admin);
    }

    function createReceivable(address seller, address debtor, uint256 faceValue, uint256 maturityDate, bytes32 proofHash) external onlyRole(ISSUER_ROLE) whenNotPaused returns (uint256) {
        if (seller == address(0) || debtor == address(0)) revert InvalidAddress();
        if (faceValue == 0) revert InvalidAmount();
        if (maturityDate <= block.timestamp) revert InvalidMaturityDate();
        if (proofHash == bytes32(0)) revert InvalidProofHash();
        if (usedProofHashes[proofHash]) revert DuplicateProofHash();

        uint256 id = nextId++;
        usedProofHashes[proofHash] = true;
        receivables[id] = Receivable(id, seller, debtor, faceValue, maturityDate, proofHash, Status.Created, address(0));
        emit ReceivableCreated(id, seller, debtor, faceValue, maturityDate, proofHash);
        return id;
    }

    function markFinanced(uint256 id, address financier) external onlyRole(FINANCIER_ROLE) whenNotPaused {
        Receivable storage r = _get(id);
        if (r.status != Status.Created) revert InvalidState(r.status);
        if (financier == address(0)) revert InvalidAddress();
        r.status = Status.Financed;
        r.financier = financier;
        emit ReceivableFinanced(id, financier);
    }

    function markSettled(uint256 id) external onlyRole(SETTLER_ROLE) whenNotPaused {
        Receivable storage r = _get(id);
        if (r.status != Status.Created && r.status != Status.Financed) revert InvalidState(r.status);
        r.status = Status.Settled;
        emit ReceivableSettled(id);
    }

    function markDefaulted(uint256 id) external onlyRole(SETTLER_ROLE) whenNotPaused {
        Receivable storage r = _get(id);
        if (r.status != Status.Financed) revert InvalidState(r.status);
        r.status = Status.Defaulted;
        emit ReceivableDefaulted(id);
    }

    function cancel(uint256 id) external onlyRole(ISSUER_ROLE) whenNotPaused {
        Receivable storage r = _get(id);
        if (r.status != Status.Created) revert InvalidState(r.status);
        r.status = Status.Cancelled;
        emit ReceivableCancelled(id);
    }

    function pause() external onlyRole(PAUSER_ROLE) { _pause(); }
    function unpause() external onlyRole(PAUSER_ROLE) { _unpause(); }

    function _get(uint256 id) private view returns (Receivable storage r) {
        r = receivables[id];
        if (r.id == 0) revert ReceivableNotFound();
    }
}
