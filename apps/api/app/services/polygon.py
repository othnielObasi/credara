from app.core.config import get_settings

ANCHOR_ABI = [
    {
        'inputs': [
            {'name': 'proofHash', 'type': 'bytes32'},
            {'name': 'proofType', 'type': 'string'},
            {'name': 'subject', 'type': 'address'},
            {'name': 'metadataURI', 'type': 'string'},
        ],
        'name': 'anchorProof',
        'outputs': [],
        'stateMutability': 'nonpayable',
        'type': 'function',
    }
]


def explorer_tx_url(tx_hash: str | None) -> str | None:
    if not tx_hash:
        return None
    settings = get_settings()
    return f"{settings.polygon_explorer_base.rstrip('/')}/tx/{tx_hash}"


def simulate_tx_hash(seed: str) -> str:
    import hashlib
    return '0x' + hashlib.sha256(seed.encode()).hexdigest()


def publish_tx(seed: str, *, proof_hash: str | None = None) -> tuple[str, bool]:
    """Return (tx_hash, is_on_chain). Falls back to deterministic simulation when relayer is not configured."""
    settings = get_settings()
    key = settings.relayer_private_key
    if not key or key.startswith('replace-with'):
        return simulate_tx_hash(seed), False

    try:
        from eth_account import Account
        from web3 import Web3

        w3 = Web3(Web3.HTTPProvider(settings.polygon_rpc_url))
        if not w3.is_connected():
            return simulate_tx_hash(seed), False

        account = Account.from_key(key)
        chain_id = settings.polygon_chain_id
        nonce = w3.eth.get_transaction_count(account.address)

        if proof_hash and settings.proof_registry_address:
            contract = w3.eth.contract(
                address=Web3.to_checksum_address(settings.proof_registry_address),
                abi=ANCHOR_ABI,
            )
            digest = bytes.fromhex(proof_hash.replace('0x', ''))
            tx = contract.functions.anchorProof(digest, 'PROOF_BUNDLE', account.address, '').build_transaction(
                {
                    'from': account.address,
                    'nonce': nonce,
                    'chainId': chain_id,
                    'gas': 250_000,
                    'maxFeePerGas': w3.to_wei('50', 'gwei'),
                    'maxPriorityFeePerGas': w3.to_wei('2', 'gwei'),
                }
            )
        else:
            tx = {
                'to': account.address,
                'value': 0,
                'gas': 21_000,
                'nonce': nonce,
                'chainId': chain_id,
                'maxFeePerGas': w3.to_wei('50', 'gwei'),
                'maxPriorityFeePerGas': w3.to_wei('2', 'gwei'),
            }

        signed = account.sign_transaction(tx)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
        return tx_hash.hex(), True
    except Exception:
        return simulate_tx_hash(seed), False
