from functools import lru_cache
from typing import Annotated

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    environment: str = 'local'
    project_name: str = 'Credara Enterprise'
    api_host: str = '0.0.0.0'
    api_port: int = 8000
    # May be empty on Vercel when Neon only injects POSTGRES_URL — resolved in database.py.
    database_url: str = 'sqlite:///./credara.db'
    redis_url: str = 'redis://localhost:6379/0'
    jwt_secret: str = 'change-me-in-production'
    jwt_issuer: str = 'credara.local'
    jwt_audience: str = 'credara.web'
    # NoDecode: this is a plain comma-separated string in .env, not JSON - without
    # NoDecode, pydantic-settings tries to JSON-decode it before parse_cors() ever
    # runs, and raises SettingsError on any non-JSON value (including the default).
    cors_origins: Annotated[list[str], NoDecode] = [
        'http://localhost:3000',
        'https://credara-jet.vercel.app',
        'https://credara-jet-six.vercel.app',
        'https://credara-jet-othnielobasis-projects.vercel.app',
    ]

    polygon_chain_id: int = 80002
    polygon_rpc_url: str = 'https://rpc-amoy.polygon.technology'
    polygon_explorer_base: str = 'https://amoy.polygonscan.com'
    relayer_private_key: str | None = None
    proof_registry_address: str | None = None
    receivable_registry_address: str | None = None
    smart_lc_factory_address: str | None = None
    credit_score_attestation_address: str | None = None
    mock_usdc_address: str | None = None

    # KYB: mock only allowed outside production unless allow_mock_kyb=true.
    kyb_provider: str = 'mock'
    allow_mock_kyb: bool = False
    didit_api_key: str | None = None
    didit_workflow_id: str | None = None
    didit_webhook_secret: str | None = None

    # Auth0 OAuth (Regular Web App) - server-brokered authorization code flow.
    auth0_domain: str | None = None
    auth0_client_id: str | None = None
    auth0_client_secret: str | None = None
    auth0_callback_url: str = 'https://credara-api.vercel.app/api/v1/auth/oauth/callback'
    auth0_frontend_redirect: str = 'https://credara-jet.vercel.app/auth/callback'

    # Shared secret for Vercel Cron / worker drain endpoint.
    cron_secret: str | None = None

    @field_validator('database_url', mode='before')
    @classmethod
    def empty_database_url_as_unset(cls, value):
        if value is None or (isinstance(value, str) and not value.strip()):
            return 'sqlite:///./credara.db'
        return value

    @field_validator('cors_origins', mode='before')
    @classmethod
    def parse_cors(cls, value):
        if isinstance(value, str):
            return [v.strip() for v in value.split(',') if v.strip()]
        return value

    @property
    def is_production(self) -> bool:
        return self.environment.lower() in {'production', 'prod'}


@lru_cache
def get_settings() -> Settings:
    return Settings()
