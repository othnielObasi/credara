"""On-chain Smart LC helpers for Amoy (factory create, MockUSDC fund, verify, release)."""

from __future__ import annotations

import time
from typing import Any

from app.core.config import get_settings
from app.services.polygon import ChainUnavailableError, explorer_tx_url

FACTORY_ABI = [
    {
        'inputs': [
            {'name': 'verifier', 'type': 'address'},
            {'name': 'disputeResolver', 'type': 'address'},
            {'name': 'pauser', 'type': 'address'},
            {'name': 'token', 'type': 'address'},
            {'name': 'buyer', 'type': 'address'},
            {'name': 'seller', 'type': 'address'},
            {'name': 'amount', 'type': 'uint256'},
            {'name': 'orderProofHash', 'type': 'bytes32'},
            {'name': 'fundingDeadline', 'type': 'uint256'},
            {'name': 'deliveryDeadline', 'type': 'uint256'},
            {'name': 'confirmationWindowSeconds', 'type': 'uint256'},
            {'name': 'disputeResolutionWindowSeconds', 'type': 'uint256'},
        ],
        'name': 'createSmartLC',
        'outputs': [{'name': 'lc', 'type': 'address'}],
        'stateMutability': 'nonpayable',
        'type': 'function',
    },
    {
        'anonymous': False,
        'inputs': [
            {'indexed': True, 'name': 'lc', 'type': 'address'},
            {'indexed': True, 'name': 'buyer', 'type': 'address'},
            {'indexed': True, 'name': 'seller', 'type': 'address'},
            {'indexed': False, 'name': 'amount', 'type': 'uint256'},
            {'indexed': False, 'name': 'orderProofHash', 'type': 'bytes32'},
            {'indexed': False, 'name': 'fundingDeadline', 'type': 'uint256'},
            {'indexed': False, 'name': 'deliveryDeadline', 'type': 'uint256'},
        ],
        'name': 'SmartLCCreated',
        'type': 'event',
    },
]

SMART_LC_ABI = [
    {'inputs': [], 'name': 'fund', 'outputs': [], 'stateMutability': 'nonpayable', 'type': 'function'},
    {
        'inputs': [{'name': 'proofHash', 'type': 'bytes32'}],
        'name': 'submitDelivery',
        'outputs': [],
        'stateMutability': 'nonpayable',
        'type': 'function',
    },
    {
        'inputs': [{'name': 'proofHash', 'type': 'bytes32'}],
        'name': 'verifyDelivery',
        'outputs': [],
        'stateMutability': 'nonpayable',
        'type': 'function',
    },
    {'inputs': [], 'name': 'release', 'outputs': [], 'stateMutability': 'nonpayable', 'type': 'function'},
    {
        'inputs': [{'name': 'reasonHash', 'type': 'bytes32'}],
        'name': 'dispute',
        'outputs': [],
        'stateMutability': 'nonpayable',
        'type': 'function',
    },
    {
        'inputs': [],
        'name': 'resolveDisputeRefund',
        'outputs': [],
        'stateMutability': 'nonpayable',
        'type': 'function',
    },
]

ERC20_ABI = [
    {
        'inputs': [
            {'name': 'spender', 'type': 'address'},
            {'name': 'amount', 'type': 'uint256'},
        ],
        'name': 'approve',
        'outputs': [{'name': '', 'type': 'bool'}],
        'stateMutability': 'nonpayable',
        'type': 'function',
    },
    {
        'inputs': [{'name': 'account', 'type': 'address'}],
        'name': 'balanceOf',
        'outputs': [{'name': '', 'type': 'uint256'}],
        'stateMutability': 'view',
        'type': 'function',
    },
    {
        'inputs': [
            {'name': 'to', 'type': 'address'},
            {'name': 'amount', 'type': 'uint256'},
        ],
        'name': 'mint',
        'outputs': [],
        'stateMutability': 'nonpayable',
        'type': 'function',
    },
]


def _relayer_ready() -> tuple[Any, Any, Any]:
    settings = get_settings()
    key = settings.relayer_private_key
    if not key or key.startswith('replace-with'):
        raise ChainUnavailableError('Relayer private key is not configured for Smart LC chain ops')
    if not settings.smart_lc_factory_address:
        raise ChainUnavailableError('SMART_LC_FACTORY_ADDRESS is not configured')
    if not settings.mock_usdc_address:
        raise ChainUnavailableError('MOCK_USDC_ADDRESS is not configured')

    from eth_account import Account
    from web3 import Web3

    w3 = Web3(Web3.HTTPProvider(settings.polygon_rpc_url))
    if not w3.is_connected():
        raise ChainUnavailableError('Polygon RPC is not reachable')
    account = Account.from_key(key)
    return w3, account, settings


def _send(w3, account, tx: dict) -> str:
    signed = account.sign_transaction(tx)
    raw = getattr(signed, 'raw_transaction', None) or signed.rawTransaction
    tx_hash = w3.eth.send_raw_transaction(raw)
    return tx_hash.hex()


def _to_token_amount(amount: float, decimals: int = 6) -> int:
    return int(round(float(amount) * (10**decimals)))


def _proof_bytes32(proof_hash: str) -> bytes:
    raw = proof_hash.replace('0x', '')
    if len(raw) != 64:
        raise ValueError('proof_hash must be 32 bytes hex')
    return bytes.fromhex(raw)


def create_smart_lc_on_chain(*, order_proof_hash: str, amount: float, seller_address: str | None = None) -> dict:
    """Deploy a SmartLC via factory. Relayer is buyer + verifier + disputeResolver + pauser for Amoy demo."""
    w3, account, settings = _relayer_ready()
    from web3 import Web3

    buyer = account.address
    seller = Web3.to_checksum_address(seller_address or settings.smart_lc_demo_seller_address or account.address)
    factory = w3.eth.contract(
        address=Web3.to_checksum_address(settings.smart_lc_factory_address),
        abi=FACTORY_ABI,
    )
    now = int(time.time())
    token_amount = _to_token_amount(amount)
    proof = _proof_bytes32(order_proof_hash)

    nonce = w3.eth.get_transaction_count(account.address)
    tx = factory.functions.createSmartLC(
        account.address,  # verifier
        account.address,  # disputeResolver
        account.address,  # pauser
        Web3.to_checksum_address(settings.mock_usdc_address),
        buyer,
        seller,
        token_amount,
        proof,
        now + 7 * 24 * 3600,
        now + 14 * 24 * 3600,
        3600,
        86400,
    ).build_transaction(
        {
            'from': account.address,
            'nonce': nonce,
            'chainId': settings.polygon_chain_id,
            'gas': 3_500_000,
            'maxFeePerGas': w3.to_wei('50', 'gwei'),
            'maxPriorityFeePerGas': w3.to_wei('2', 'gwei'),
        }
    )
    tx_hash = _send(w3, account, tx)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=180)
    if receipt.status != 1:
        raise ChainUnavailableError('SmartLC factory create transaction reverted')

    events = factory.events.SmartLCCreated().process_receipt(receipt)
    if not events:
        raise ChainUnavailableError('Could not resolve deployed SmartLC address from factory receipt')
    lc_address = Web3.to_checksum_address(events[0]['args']['lc'])

    return {
        'contract_address': lc_address,
        'tx_hash': tx_hash,
        'on_chain': True,
        'explorer_url': explorer_tx_url(tx_hash, on_chain=True),
        'buyer': buyer,
        'seller': seller,
    }


def fund_smart_lc_on_chain(*, contract_address: str, amount: float) -> dict:
    """Mint MockUSDC to relayer if needed, approve, and fund() as buyer."""
    w3, account, settings = _relayer_ready()
    from web3 import Web3

    lc = w3.eth.contract(address=Web3.to_checksum_address(contract_address), abi=SMART_LC_ABI)
    token = w3.eth.contract(address=Web3.to_checksum_address(settings.mock_usdc_address), abi=ERC20_ABI)
    token_amount = _to_token_amount(amount)

    balance = token.functions.balanceOf(account.address).call()
    nonce = w3.eth.get_transaction_count(account.address)
    if balance < token_amount:
        mint_tx = token.functions.mint(account.address, token_amount).build_transaction(
            {
                'from': account.address,
                'nonce': nonce,
                'chainId': settings.polygon_chain_id,
                'gas': 120_000,
                'maxFeePerGas': w3.to_wei('50', 'gwei'),
                'maxPriorityFeePerGas': w3.to_wei('2', 'gwei'),
            }
        )
        mint_hash = _send(w3, account, mint_tx)
        w3.eth.wait_for_transaction_receipt(mint_hash, timeout=120)
        nonce += 1

    approve_tx = token.functions.approve(Web3.to_checksum_address(contract_address), token_amount).build_transaction(
        {
            'from': account.address,
            'nonce': nonce,
            'chainId': settings.polygon_chain_id,
            'gas': 80_000,
            'maxFeePerGas': w3.to_wei('50', 'gwei'),
            'maxPriorityFeePerGas': w3.to_wei('2', 'gwei'),
        }
    )
    approve_hash = _send(w3, account, approve_tx)
    w3.eth.wait_for_transaction_receipt(approve_hash, timeout=120)
    nonce += 1

    fund_tx = lc.functions.fund().build_transaction(
        {
            'from': account.address,
            'nonce': nonce,
            'chainId': settings.polygon_chain_id,
            'gas': 250_000,
            'maxFeePerGas': w3.to_wei('50', 'gwei'),
            'maxPriorityFeePerGas': w3.to_wei('2', 'gwei'),
        }
    )
    fund_hash = _send(w3, account, fund_tx)
    receipt = w3.eth.wait_for_transaction_receipt(fund_hash, timeout=180)
    if receipt.status != 1:
        raise ChainUnavailableError('SmartLC fund transaction reverted')
    return {
        'tx_hash': fund_hash,
        'on_chain': True,
        'explorer_url': explorer_tx_url(fund_hash, on_chain=True),
    }


def release_smart_lc_on_chain(*, contract_address: str, delivery_proof_hash: str) -> dict:
    """submitDelivery → verifyDelivery → release as the relayer verifier."""
    w3, account, settings = _relayer_ready()
    from web3 import Web3

    lc = w3.eth.contract(address=Web3.to_checksum_address(contract_address), abi=SMART_LC_ABI)
    proof = _proof_bytes32(delivery_proof_hash)
    nonce = w3.eth.get_transaction_count(account.address)

    def _build(fn, gas: int):
        nonlocal nonce
        tx = fn.build_transaction(
            {
                'from': account.address,
                'nonce': nonce,
                'chainId': settings.polygon_chain_id,
                'gas': gas,
                'maxFeePerGas': w3.to_wei('50', 'gwei'),
                'maxPriorityFeePerGas': w3.to_wei('2', 'gwei'),
            }
        )
        h = _send(w3, account, tx)
        receipt = w3.eth.wait_for_transaction_receipt(h, timeout=180)
        if receipt.status != 1:
            raise ChainUnavailableError(f'SmartLC step reverted: {fn.fn_name}')
        nonce += 1
        return h

    _build(lc.functions.submitDelivery(proof), 180_000)
    _build(lc.functions.verifyDelivery(proof), 180_000)
    release_hash = _build(lc.functions.release(), 250_000)
    return {
        'tx_hash': release_hash,
        'on_chain': True,
        'explorer_url': explorer_tx_url(release_hash, on_chain=True),
    }
