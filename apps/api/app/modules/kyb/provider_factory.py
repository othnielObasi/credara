from app.core.config import get_settings
from app.modules.kyb.provider_interface import KYBProvider
from app.modules.kyb.providers.mock_provider import MockKYBProvider
from app.modules.kyb.providers.didit_provider import DiditKYBProvider


def get_kyb_provider() -> KYBProvider:
    settings = get_settings()
    provider = settings.kyb_provider.lower()
    if provider == 'mock':
        return MockKYBProvider()
    if provider == 'didit':
        return DiditKYBProvider()
    raise ValueError(f'Unsupported KYB provider: {provider}')
