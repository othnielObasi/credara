from app.core.hashing import sha256_hex

def test_canonical_hash_order_independent():
    a = sha256_hex({'b': 2, 'a': 1})
    b = sha256_hex({'a': 1, 'b': 2})
    assert a == b
    assert a.startswith('0x')
