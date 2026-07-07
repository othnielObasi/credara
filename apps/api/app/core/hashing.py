import hashlib
import json
from decimal import Decimal
from datetime import date, datetime
from uuid import UUID


def _normalise(value):
    if isinstance(value, dict):
        return {k: _normalise(value[k]) for k in sorted(value)}
    if isinstance(value, list):
        return [_normalise(v) for v in value]
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, UUID):
        return str(value)
    return value


def canonical_json(payload: dict) -> str:
    return json.dumps(_normalise(payload), separators=(',', ':'), ensure_ascii=False)


def sha256_hex(payload: dict | bytes | str) -> str:
    if isinstance(payload, dict):
        data = canonical_json(payload).encode('utf-8')
    elif isinstance(payload, str):
        data = payload.encode('utf-8')
    else:
        data = payload
    return '0x' + hashlib.sha256(data).hexdigest()
