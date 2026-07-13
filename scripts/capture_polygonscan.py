#!/usr/bin/env python3
"""Capture Polygonscan tx page screenshot for pitch deck."""

from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs' / 'screenshots' / 'polygonscan-tx.png'
# Smart LC release tx (demo climax)
URL = 'https://amoy.polygonscan.com/tx/0x5743a885e54063da6c4056d73e4b49113918558fd09d8973c9074de8e57af9de'


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={'width': 1400, 'height': 1100})
        page.goto(URL, wait_until='load', timeout=90000)
        page.wait_for_timeout(6000)
        for label in ('Got it!', 'Accept', 'I Agree'):
            try:
                page.get_by_role('button', name=label).click(timeout=2000)
                page.wait_for_timeout(500)
            except Exception:
                pass
        page.screenshot(path=str(OUT), full_page=False)
        browser.close()
    print(f'saved {OUT} ({OUT.stat().st_size} bytes)')


if __name__ == '__main__':
    main()
