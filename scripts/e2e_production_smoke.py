#!/usr/bin/env python3
"""Production happy-path smoke: SME register → business → order → invoice → proof → receivable.

Usage:
  python scripts/e2e_production_smoke.py
  API_BASE=https://credara-api.vercel.app python scripts/e2e_production_smoke.py
"""

from __future__ import annotations

import os
import sys
import time
import uuid

import httpx

API_BASE = os.getenv('API_BASE', 'https://credara-api.vercel.app').rstrip('/')
API = f'{API_BASE}/api/v1'


def _fail(msg: str) -> None:
    print(f'FAIL: {msg}', file=sys.stderr)
    sys.exit(1)


def main() -> None:
    suffix = uuid.uuid4().hex[:8]
    email = f'smoke-{suffix}@example.com'
    password = 'SmokeTest123!'
    client = httpx.Client(timeout=60.0)

    print(f'API={API_BASE}')
    health = client.get(f'{API_BASE}/health')
    if health.status_code != 200:
        _fail(f'health {health.status_code}: {health.text}')
    print('OK health', health.json())

    # Demo payments must be gone in production
    demo = client.get(f'{API}/payments/intents')
    if demo.status_code == 200:
        _fail('demo /payments/intents still mounted in this environment')
    print('OK demo payments gated', demo.status_code)

    reg = client.post(
        f'{API}/auth/register',
        json={'email': email, 'password': password, 'full_name': 'Smoke SME', 'role': 'sme'},
    )
    if reg.status_code != 200:
        _fail(f'register {reg.status_code}: {reg.text}')
    token = reg.json()['access_token']
    headers = {'Authorization': f'Bearer {token}'}
    print('OK register', email)

    biz = client.post(
        f'{API}/businesses',
        headers=headers,
        json={'legal_name': f'Smoke Co {suffix}', 'country': 'AE', 'registration_number': f'SMK-{suffix}'},
    )
    if biz.status_code != 200:
        _fail(f'business {biz.status_code}: {biz.text}')
    business_id = biz.json()['id']
    print('OK business', business_id)

    order = client.post(
        f'{API}/trade/orders',
        headers=headers,
        json={
            'seller_business_id': business_id,
            'buyer_name': 'Smoke Buyer',
            'description': 'E2E smoke order',
            'total_amount': 12500,
            'currency': 'USDC',
        },
    )
    if order.status_code != 200:
        _fail(f'order {order.status_code}: {order.text}')
    order_id = order.json()['id']
    print('OK order', order_id)

    # Buyer confirm requires buyer role / business — create buyer and confirm if API allows
    buyer_email = f'buyer-{suffix}@example.com'
    buyer_reg = client.post(
        f'{API}/auth/register',
        json={'email': buyer_email, 'password': password, 'full_name': 'Smoke Buyer', 'role': 'buyer'},
    )
    if buyer_reg.status_code != 200:
        _fail(f'buyer register {buyer_reg.status_code}: {buyer_reg.text}')
    buyer_headers = {'Authorization': f'Bearer {buyer_reg.json()["access_token"]}'}
    buyer_biz = client.post(
        f'{API}/businesses',
        headers=buyer_headers,
        json={'legal_name': f'Buyer Co {suffix}', 'country': 'AE', 'registration_number': f'BUY-{suffix}'},
    )
    if buyer_biz.status_code != 200:
        _fail(f'buyer business {buyer_biz.status_code}: {buyer_biz.text}')
    buyer_business_id = buyer_biz.json()['id']

    confirmed = client.post(
        f'{API}/trade/orders/{order_id}/confirm',
        headers=buyer_headers,
        json={'buyer_business_id': buyer_business_id},
    )
    if confirmed.status_code != 200:
        print('WARN order confirm', confirmed.status_code, confirmed.text[:200])
    else:
        print('OK order confirm')

    from datetime import datetime, timedelta, timezone

    due = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
    inv = client.post(
        f'{API}/trade/invoices',
        headers=headers,
        json={
            'order_id': order_id,
            'invoice_number': f'INV-{suffix}',
            'amount': 12500,
            'due_date': due,
        },
    )
    if inv.status_code != 200:
        _fail(f'invoice {inv.status_code}: {inv.text}')
    invoice_id = inv.json()['id']
    print('OK invoice', invoice_id)

    inv_confirm = client.post(
        f'{API}/trade/invoices/{invoice_id}/buyer-confirm',
        headers=buyer_headers,
        json={'buyer_business_id': buyer_business_id},
    )
    if inv_confirm.status_code != 200:
        print('WARN invoice confirm', inv_confirm.status_code, inv_confirm.text[:200])
    else:
        print('OK invoice confirm')

    proof = client.post(
        f'{API}/trade/delivery-proofs',
        headers=headers,
        json={
            'order_id': order_id,
            'evidence_uri': f'https://example.com/pod/{suffix}.pdf',
            'otp_code': '123456',
            'gps_lat': '25.0657',
            'gps_lng': '55.1713',
        },
    )
    if proof.status_code != 200:
        _fail(f'delivery proof {proof.status_code}: {proof.text}')
    print('OK delivery proof', proof.json().get('id'))

    recv = client.post(
        f'{API}/trade/receivables',
        headers=headers,
        json={'invoice_id': invoice_id},
    )
    if recv.status_code != 200:
        print('WARN receivable', recv.status_code, recv.text[:240])
    else:
        print('OK receivable', recv.json().get('id'))

    score = client.post(f'{API}/finance/businesses/{business_id}/score', headers=headers)
    if score.status_code != 200:
        _fail(f'score {score.status_code}: {score.text}')
    print('OK score', score.json().get('score'), score.json().get('grade'))

    ledger = client.get(f'{API}/proof-ledger', headers=headers)
    if ledger.status_code != 200:
        _fail(f'proof ledger {ledger.status_code}: {ledger.text}')
    print('OK proof-ledger rows', len(ledger.json()))

    print('SMOKE PASS', time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()))


if __name__ == '__main__':
    main()
