"""Internal ops endpoints: Vercel Cron drains blockchain outbox without a long-running worker."""

from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException, status

from app.core.config import get_settings
from app.services.outbox_drain import process_once

router = APIRouter(prefix='/internal', tags=['internal'])


def _authorize_cron(
    authorization: str | None,
    x_cron_secret: str | None,
) -> None:
    settings = get_settings()
    expected = settings.cron_secret
    if not expected:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, detail='CRON_SECRET is not configured')

    provided = None
    if authorization and authorization.lower().startswith('bearer '):
        provided = authorization[7:].strip()
    elif x_cron_secret:
        provided = x_cron_secret.strip()

    if not provided or provided != expected:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail='Invalid cron secret')


@router.api_route('/relayer/drain', methods=['GET', 'POST'])
def drain_blockchain_outbox(
    authorization: str | None = Header(default=None),
    x_cron_secret: str | None = Header(default=None, alias='X-Cron-Secret'),
):
    """Process pending BlockchainOutbox rows (same logic as apps/workers relayer).

    Vercel Cron invokes this path with GET + Authorization: Bearer <CRON_SECRET>.
    """
    _authorize_cron(authorization, x_cron_secret)
    processed = process_once()
    return {'ok': True, 'processed': processed}
