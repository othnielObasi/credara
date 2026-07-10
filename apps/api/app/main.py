from app.api.v1.routers import real_workflow
from app.api.v1.routers import settings_and_access
from app.api.v1.routers import onboarding
from app.api.v1.routers import feature_structure
from app.api.v1.routers import payments_escrow_ledger
from app.api.v1.routers import contract_invoice_documents
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.database import Base, engine
from app import models  # noqa: F401

settings = get_settings()
try:
    Base.metadata.create_all(bind=engine)
except Exception as exc:
    import logging
    logging.getLogger('credara').error(
        'Database init failed (%s). For local dev without Docker, run: bash scripts/dev-local.sh api',
        exc,
    )
    raise

app = FastAPI(title=settings.project_name, version='0.1.0', docs_url='/docs')
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
app.include_router(contract_invoice_documents.router, prefix="/api/v1")
app.include_router(payments_escrow_ledger.router, prefix="/api/v1")
app.include_router(feature_structure.router, prefix="/api/v1")
app.include_router(onboarding.router, prefix="/api/v1")
app.include_router(settings_and_access.router, prefix="/api/v1")
app.include_router(real_workflow.router, prefix="/api/v1")
