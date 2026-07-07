from app.core.config import get_settings


def explorer_tx_url(tx_hash: str | None) -> str | None:
    if not tx_hash:
        return None
    settings = get_settings()
    return f"{settings.polygon_explorer_base.rstrip('/')}/tx/{tx_hash}"


def simulate_tx_hash(seed: str) -> str:
    # Local/demo fallback. Production relayer signs and broadcasts real transactions.
    import hashlib
    return '0x' + hashlib.sha256(seed.encode()).hexdigest()
