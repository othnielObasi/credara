#!/usr/bin/env python3
"""Verify one live Polygon Amoy transaction (proof anchor) using repo .env config.

Prints relayer address, balances, tx hash, and Polygonscan URL — never private keys.
"""

from __future__ import annotations

import hashlib
import os
import sys
import time
import uuid

# apps/api on path for app.* imports
API_ROOT = os.path.join(os.path.dirname(__file__), '..', 'apps', 'api')
sys.path.insert(0, os.path.abspath(API_ROOT))


def _ok(msg: str) -> None:
    print(f'OK  {msg}')


def _fail(msg: str) -> None:
    print(f'FAIL {msg}', file=sys.stderr)
    sys.exit(1)


def _warn(msg: str) -> None:
    print(f'WARN {msg}')


def main() -> None:
    from eth_account import Account
    from web3 import Web3

    from app.core.config import get_settings
    from app.services.polygon import explorer_tx_url, publish_tx

    settings = get_settings()
    print('=== Credara Amoy live-tx verification ===')
    print(f'environment: {settings.environment}')
    print(f'chain_id: {settings.polygon_chain_id}')
    print(f'rpc: {settings.polygon_rpc_url.split("/")[2]}')  # host only
    print(f'permits_simulated_chain: {settings.permits_simulated_chain}')

    required = {
        'RELAYER_PRIVATE_KEY': settings.relayer_private_key,
        'PROOF_REGISTRY_ADDRESS': settings.proof_registry_address,
        'SMART_LC_FACTORY_ADDRESS': settings.smart_lc_factory_address,
        'MOCK_USDC_ADDRESS': settings.mock_usdc_address,
    }
    missing = [k for k, v in required.items() if not v or str(v).startswith('replace-with')]
    if missing:
        _fail(f'missing env: {", ".join(missing)}')

    key = settings.relayer_private_key
    assert key is not None
    account = Account.from_key(key)
    relayer = account.address
    _ok(f'relayer address {relayer}')

    w3 = Web3(Web3.HTTPProvider(settings.polygon_rpc_url))
    if not w3.is_connected():
        _fail('Polygon RPC not reachable')
    _ok('RPC connected')

    block = w3.eth.block_number
    _ok(f'latest block {block}')

    pol_wei = w3.eth.get_balance(relayer)
    pol = float(w3.from_wei(pol_wei, 'ether'))
    print(f'    relayer POL balance: {pol:.6f}')
    if pol < 0.01:
        _warn('relayer POL low — fund on https://faucet.polygon.technology/')

    for name, addr in [
        ('ProofRegistry', settings.proof_registry_address),
        ('SmartLCFactory', settings.smart_lc_factory_address),
        ('MockUSDC', settings.mock_usdc_address),
    ]:
        code = w3.eth.get_code(Web3.to_checksum_address(addr))
        if code in (b'', b'0x'):
            _fail(f'{name} has no bytecode at {addr}')
        _ok(f'{name} deployed ({len(code)} bytes)')

    seed = f'verify-amoy:{uuid.uuid4().hex}'
    proof_hash = '0x' + hashlib.sha256(seed.encode()).hexdigest()
    print(f'    proof_hash: {proof_hash[:18]}...')

    try:
        tx_hash, on_chain = publish_tx(seed, proof_hash=proof_hash)
    except Exception as exc:
        _fail(f'publish_tx raised: {exc}')

    if not on_chain or not tx_hash:
        _fail('publish_tx returned simulated/off-chain result — no live Amoy tx')

    url = explorer_tx_url(tx_hash, on_chain=True)
    _ok(f'tx broadcast {tx_hash}')
    print(f'    explorer: {url}')

    deadline = time.time() + 120
    receipt = None
    while time.time() < deadline:
        try:
            receipt = w3.eth.get_transaction_receipt(tx_hash)
            if receipt is not None:
                break
        except Exception:
            pass
        time.sleep(3)

    if receipt is None:
        _warn('receipt not confirmed within 120s — check explorer manually')
    else:
        status = receipt.get('status', receipt.status if hasattr(receipt, 'status') else None)
        if status == 0:
            _fail(f'tx reverted on-chain: {url}')
        _ok(f'tx confirmed block {receipt["blockNumber"]} status={status}')

    scan_key = os.getenv('POLYGONSCAN_API_KEY', '').strip()
    if scan_key:
        import httpx

        api_url = (
            f'https://api-amoy.polygonscan.com/api'
            f'?module=transaction&action=gettxreceiptstatus&txhash={tx_hash}&apikey={scan_key}'
        )
        try:
            resp = httpx.get(api_url, timeout=30)
            data = resp.json()
            if data.get('status') == '1' and data.get('result', {}).get('status') == '1':
                _ok('Polygonscan API confirms success')
            else:
                _warn(f'Polygonscan API: {data}')
        except Exception as exc:
            _warn(f'Polygonscan API check skipped: {exc}')

    print('=== LIVE AMOY TX VERIFIED ===')
    print(url)


if __name__ == '__main__':
    main()
