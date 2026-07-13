#!/usr/bin/env python3
"""Verify production API can produce a live Amoy proof-anchor tx."""

from __future__ import annotations

import os
import sys
import time
import uuid

import httpx

API_BASE = os.getenv('API_BASE', 'https://credara-api.vercel.app').rstrip('/')
API = f'{API_BASE}/api/v1'


def _fail(msg: str) -> None:
    print(f'FAIL {msg}', file=sys.stderr)
    sys.exit(1)


def main() -> None:
    client = httpx.Client(timeout=90.0)
    print('=== Production Amoy verification ===')
    print(f'API={API_BASE}')

    health = client.get(f'{API_BASE}/health')
    if health.status_code != 200:
        _fail(f'health {health.status_code}')
    env = health.json().get('environment')
    print(f'    environment: {env}')
    if env != 'production':
        print('WARN API not marked production')

    suffix = uuid.uuid4().hex[:8]
    email = f'amoy-{suffix}@example.com'
    password = 'AmoyVerify123!'

    reg = client.post(
        f'{API}/auth/register',
        json={'email': email, 'password': password, 'full_name': 'Amoy Verify', 'role': 'sme'},
    )
    if reg.status_code != 200:
        _fail(f'register {reg.status_code}: {reg.text[:300]}')
    headers = {'Authorization': f'Bearer {reg.json()["access_token"]}'}

    biz = client.post(
        f'{API}/businesses',
        headers=headers,
        json={'legal_name': f'Amoy Co {suffix}', 'country': 'AE', 'registration_number': f'AMY-{suffix}'},
    )
    if biz.status_code != 200:
        _fail(f'business {biz.status_code}: {biz.text[:300]}')
    business_id = biz.json()['id']

    order = client.post(
        f'{API}/trade/orders',
        headers=headers,
        json={
            'seller_business_id': business_id,
            'buyer_name': 'Amoy Buyer',
            'description': 'Amoy verify order',
            'total_amount': 5000,
            'currency': 'USDC',
        },
    )
    if order.status_code != 200:
        _fail(f'order {order.status_code}: {order.text[:300]}')
    order_id = order.json()['id']

    from datetime import datetime, timedelta, timezone

    due = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
    inv = client.post(
        f'{API}/trade/invoices',
        headers=headers,
        json={'order_id': order_id, 'invoice_number': f'INV-{suffix}', 'amount': 5000, 'due_date': due},
    )
    if inv.status_code != 200:
        _fail(f'invoice {inv.status_code}: {inv.text[:300]}')
    invoice_id = inv.json()['id']

    proof = client.post(
        f'{API}/trade/delivery-proofs',
        headers=headers,
        json={
            'order_id': order_id,
            'evidence_uri': f'https://example.com/pod/{suffix}.pdf',
            'otp_code': '654321',
            'gps_lat': '25.0657',
            'gps_lng': '55.1713',
        },
    )
    if proof.status_code != 200:
        _fail(f'delivery proof {proof.status_code}: {proof.text[:300]}')

    anchor = client.post(f'{API}/proof-ledger/anchor', headers=headers, json={'invoice_id': invoice_id})
    print(f'    anchor status: {anchor.status_code}')
    if anchor.status_code == 503:
        _fail(f'chain unavailable on production: {anchor.text[:400]}')
    if anchor.status_code != 200:
        _fail(f'anchor {anchor.status_code}: {anchor.text[:400]}')

    body = anchor.json()
    on_chain = body.get('on_chain')
    tx_hash = body.get('polygon_tx_hash')
    explorer = body.get('explorer_url')
    print(f'    on_chain: {on_chain}')
    print(f'    tx_hash: {tx_hash}')
    print(f'    explorer: {explorer}')

    if not on_chain or not tx_hash or not explorer:
        _fail('production anchor returned off-chain / no explorer URL')

    # Poll explorer page exists (light check)
    time.sleep(5)
    page = client.get(explorer)
    if page.status_code != 200:
        print(f'WARN explorer HTTP {page.status_code}')
    elif 'Transaction Hash' in page.text or tx_hash.lower() in page.text.lower():
        print('OK  Polygonscan page reachable')
    else:
        print('WARN Polygonscan page loaded but tx not indexed yet')

    print('=== PRODUCTION LIVE AMOY TX VERIFIED ===')
    print(explorer)


if __name__ == '__main__':
    main()
