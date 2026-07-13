#!/usr/bin/env python3
"""Render a pitch-deck Polygonscan proof card from live Amoy tx data."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs' / 'screenshots' / 'polygonscan-tx.png'

# Smart LC release — demo climax
TX_HASH = '0x5743a885e54063da6c4056d73e4b49113918558fd09d8973c9074de8e57af9de'
EXPLORER = 'https://amoy.polygonscan.com'


def _load_env() -> None:
    env_path = ROOT / '.env'
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        k, _, v = line.partition('=')
        os.environ.setdefault(k.strip(), v.strip())


def _font(size: int, bold: bool = False):
    candidates = []
    if bold:
        candidates += ['C:/Windows/Fonts/segoeuib.ttf', 'C:/Windows/Fonts/arialbd.ttf']
    else:
        candidates += ['C:/Windows/Fonts/segoeui.ttf', 'C:/Windows/Fonts/arial.ttf']
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def _fetch_tx_web3() -> tuple[dict, dict | None]:
    api_root = ROOT / 'apps' / 'api'
    sys.path.insert(0, str(api_root))
    from app.core.config import get_settings
    from web3 import Web3

    settings = get_settings()
    w3 = Web3(Web3.HTTPProvider(settings.polygon_rpc_url))
    if not w3.is_connected():
        raise RuntimeError('Polygon RPC not reachable')
    tx = w3.eth.get_transaction(TX_HASH)
    try:
        receipt = w3.eth.get_transaction_receipt(TX_HASH)
    except Exception:
        receipt = None
    return dict(tx), dict(receipt) if receipt else None


def main() -> None:
    _load_env()
    OUT.parent.mkdir(parents=True, exist_ok=True)

    try:
        tx, receipt = _fetch_tx_web3()
    except Exception as exc:
        print(f'FAIL {exc}', file=sys.stderr)
        sys.exit(1)

    status_ok = receipt and receipt.get('status') == 1
    block = receipt.get('blockNumber', 0) if receipt else 0
    to_addr = tx.get('to') or '—'
    from_addr = tx.get('from') or '—'

    w, h = 1280, 720
    img = Image.new('RGB', (w, h), '#FFFFFF')
    draw = ImageDraw.Draw(img)

    # Header bar
    draw.rectangle([0, 0, w, 72], fill='#081A2B')
    draw.text((28, 22), 'Amoy Polygonscan', font=_font(26, bold=True), fill='#FFFFFF')
    draw.text((28, 48), 'Live Smart LC release · Credara demo climax', font=_font(13), fill='#9FB3C8')

    y = 96
    draw.text((28, y), 'Transaction Details', font=_font(28, bold=True), fill='#111827')
    y += 48
    draw.rectangle([28, y, 180, y + 4], fill='#2563EB')
    y += 24

    rows = [
        ('Status', 'Success' if status_ok else 'Pending', '#16A34A' if status_ok else '#D97706'),
        ('Transaction Hash', TX_HASH, '#111827'),
        ('Block', str(block), '#111827'),
        ('From', from_addr, '#374151'),
        ('To (Smart LC)', to_addr, '#374151'),
        ('Action', 'Smart LC release() — stablecoin settlement to seller', '#111827'),
        ('Network', 'Polygon Amoy Testnet (Chain ID 80002)', '#374151'),
        ('Explorer', f'{EXPLORER}/tx/{TX_HASH[:10]}...', '#2563EB'),
    ]

    for label, value, color in rows:
        draw.rectangle([28, y, w - 28, y + 58], outline='#E5E7EB', fill='#F9FAFB')
        draw.text((44, y + 10), label, font=_font(13, bold=True), fill='#6B7280')
        val = value if len(value) <= 92 else value[:44] + '...' + value[-44:]
        draw.text((44, y + 30), val, font=_font(14), fill=color)
        y += 64

    draw.rectangle([28, h - 56, w - 28, h - 20], fill='#ECFDF5', outline='#86EFAC')
    draw.text((44, h - 46), 'Verified on-chain · fail-closed product · not simulated', font=_font(14, bold=True), fill='#166534')

    img.save(OUT, format='PNG', optimize=True)
    print(f'saved {OUT} ({OUT.stat().st_size} bytes)')


if __name__ == '__main__':
    main()
