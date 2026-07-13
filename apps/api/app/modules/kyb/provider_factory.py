from fastapi import HTTPException, status

from app.core.config import get_settings
from app.modules.kyb.provider_interface import KYBProvider
from app.modules.kyb.providers.didit_provider import DiditKYBProvider
from app.modules.kyb.providers.mock_provider import MockKYBProvider


def get_kyb_provider() -> KYBProvider:
    settings = get_settings()
    provider = (settings.kyb_provider or 'mock').lower().strip()

    if provider == 'mock':
        if settings.is_production and not settings.allow_mock_kyb:
            raise HTTPException(
                status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=(
                    'Mock KYB is disabled in production. '
                    'Set KYB_PROVIDER=didit with credentials, or ALLOW_MOCK_KYB=true for an explicit sandbox.'
                ),
            )
        return MockKYBProvider()

    if provider == 'didit':
        if not settings.didit_api_key or not settings.didit_workflow_id:
            raise HTTPException(
                status.HTTP_503_SERVICE_UNAVAILABLE,
                detail='Didit KYB is selected but DIDIT_API_KEY / DIDIT_WORKFLOW_ID are missing.',
            )
        return DiditKYBProvider()

    raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f'Unsupported KYB provider: {provider}')
