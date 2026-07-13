#!/usr/bin/env python3
"""Verify full Smart LC lifecycle on Polygon Amoy: create → fund → verify → release."""

from __future__ import annotations

import hashlib
import os
import sys
import uuid

API_ROOT = os.path.join(os.path.dirname(__file__), '..', 'apps', 'api')
sys.path.insert(0, os.path.abspath(API_ROOT))


def _ok(msg: str) -> None:
    print(f'OK  {msg}')


def _fail(msg: str) -> None:
    print(f'FAIL {msg}', file=sys.stderr)
    sys.exit(1)


def main() -> None:
    from app.services.polygon import ChainUnavailableError
    from app.services.smart_lc_chain import (
        create_smart_lc_on_chain,
        fund_smart_lc_on_chain,
        release_smart_lc_on_chain,
    )

    print('=== Credara Smart LC full-cycle verification (Amoy) ===')
    seed = f'smart-lc-verify:{uuid.uuid4().hex}'
    order_proof = '0x' + hashlib.sha256(f'order:{seed}'.encode()).hexdigest()
    delivery_proof = '0x' + hashlib.sha256(f'delivery:{seed}'.encode()).hexdigest()
    amount = 1000.0  # 1000 MockUSDC

    try:
        print('Step 1/4: create Smart LC via factory...')
        created = create_smart_lc_on_chain(order_proof_hash=order_proof, amount=amount)
        lc = created['contract_address']
        _ok(f'created LC {lc}')
        print(f'    tx: {created["explorer_url"]}')

        print('Step 2/4: fund escrow (mint MockUSDC if needed + approve + fund)...')
        funded = fund_smart_lc_on_chain(contract_address=lc, amount=amount)
        _ok('funded escrow')
        print(f'    tx: {funded["explorer_url"]}')

        print('Step 3/4: submitDelivery + verifyDelivery...')
        print('Step 4/4: release to seller...')
        released = release_smart_lc_on_chain(contract_address=lc, delivery_proof_hash=delivery_proof)
        _ok('released settlement')
        print(f'    tx: {released["explorer_url"]}')
    except ChainUnavailableError as exc:
        _fail(str(exc))
    except Exception as exc:
        _fail(f'unexpected error: {exc}')

    print('=== SMART LC CYCLE VERIFIED ===')
    print(f'contract: {lc}')
    print(f'create:   {created["explorer_url"]}')
    print(f'fund:     {funded["explorer_url"]}')
    print(f'release:  {released["explorer_url"]}')


if __name__ == '__main__':
    main()
