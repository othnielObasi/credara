from contextlib import asynccontextmanager
import asyncio
import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.api.v1.routers import onboarding
from app.api.v1.routers import real_workflow
from app.api.v1.routers import settings_and_access
from app.core.config import get_settings
from app.core.database import Base, engine
from app import models  # noqa: F401

settings = get_settings()
logger = logging.getLogger('credara')


def _is_production() -> bool:
    return settings.environment.lower() in {'production', 'prod'}


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Vercel cold starts cannot afford the long Docker-style DB wait loop.
    retries = 2 if os.getenv('VERCEL') else 30
    delay = 0.5 if os.getenv('VERCEL') else 2
    for attempt in range(retries):
        try:
            Base.metadata.create_all(bind=engine)
            break
        except Exception as exc:
            if attempt >= retries - 1:
                logger.error('Database init failed after retries: %s', exc)
            else:
                await asyncio.sleep(delay)
    yield


app = FastAPI(title=settings.project_name, version='0.1.0', docs_url='/docs', lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


@app.get('/health')
def health():
    return {'status': 'ok', 'service': 'credara-api', 'environment': settings.environment}


app.include_router(api_router, prefix='/api/v1')
app.include_router(onboarding.router, prefix='/api/v1')
app.include_router(settings_and_access.router, prefix='/api/v1')
app.include_router(real_workflow.router, prefix='/api/v1')

# Demo/in-memory routers stay local/sandbox only — never mount in production.
if not _is_production():
    from app.api.v1.routers import contract_invoice_documents
    from app.api.v1.routers import feature_structure
    from app.api.v1.routers import payments_escrow_ledger

    app.include_router(contract_invoice_documents.router, prefix='/api/v1')
    app.include_router(payments_escrow_ledger.router, prefix='/api/v1')
    app.include_router(feature_structure.router, prefix='/api/v1')
    logger.info('Demo routers mounted (environment=%s)', settings.environment)
else:
    logger.info('Demo routers disabled in production')
