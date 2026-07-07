from fastapi import APIRouter, Depends, Header, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import Role, require_roles
from app.models.business import KYBProfile
from app.models.identity import User
from app.modules.kyb.service import add_document, admin_decision, get_or_create_profile, process_webhook, submit_kyb, upsert_profile
from app.schemas.kyb import AdminKYBDecision, KYBDocumentCreate, KYBDocumentRead, KYBProfileRead, KYBProfileUpsert, KYBSubmitResponse, KYBWebhookResponse

router = APIRouter()

@router.get('/profiles/{business_id}', response_model=KYBProfileRead)
def read_kyb_profile(business_id: str, db: Session = Depends(get_db), user: User = Depends(require_roles(Role.ADMIN, Role.SME, Role.FINANCIER))):
    return get_or_create_profile(db, business_id)

@router.post('/profiles/{business_id}', response_model=KYBProfileRead)
def upsert_kyb_profile(payload: KYBProfileUpsert, business_id: str, db: Session = Depends(get_db), user: User = Depends(require_roles(Role.ADMIN, Role.SME))):
    return upsert_profile(db, business_id, payload, user.id)

@router.post('/profiles/{business_id}/documents', response_model=KYBDocumentRead)
def upload_kyb_document(payload: KYBDocumentCreate, business_id: str, db: Session = Depends(get_db), user: User = Depends(require_roles(Role.ADMIN, Role.SME))):
    return add_document(db, business_id, payload, user.id)

@router.post('/profiles/{business_id}/submit', response_model=KYBSubmitResponse)
async def submit_kyb_profile(business_id: str, db: Session = Depends(get_db), user: User = Depends(require_roles(Role.ADMIN, Role.SME))):
    return await submit_kyb(db, business_id, user.id)

@router.get('/profiles/{business_id}/status', response_model=KYBProfileRead)
def kyb_status(business_id: str, db: Session = Depends(get_db), user: User = Depends(require_roles(Role.ADMIN, Role.SME, Role.FINANCIER, Role.BUYER))):
    return get_or_create_profile(db, business_id)

@router.post('/webhooks/{provider}', response_model=KYBWebhookResponse)
async def kyb_webhook(provider: str, request: Request, db: Session = Depends(get_db)):
    payload = await request.json()
    headers = {k: v for k, v in request.headers.items()}
    return await process_webhook(db, provider, payload, headers)

@router.get('/admin/reviews', response_model=list[KYBProfileRead])
def list_kyb_reviews(db: Session = Depends(get_db), user: User = Depends(require_roles(Role.ADMIN))):
    return db.query(KYBProfile).filter(KYBProfile.status.in_(['pending_review', 'manual_review', 'submitted', 'needs_more_info'])).order_by(KYBProfile.updated_at.desc()).limit(100).all()

@router.post('/admin/{profile_id}/approve', response_model=KYBProfileRead)
def approve_kyb(profile_id: str, payload: AdminKYBDecision, db: Session = Depends(get_db), user: User = Depends(require_roles(Role.ADMIN))):
    return admin_decision(db, profile_id, 'approved', user.id, payload.reason, payload.risk_level)

@router.post('/admin/{profile_id}/reject', response_model=KYBProfileRead)
def reject_kyb(profile_id: str, payload: AdminKYBDecision, db: Session = Depends(get_db), user: User = Depends(require_roles(Role.ADMIN))):
    return admin_decision(db, profile_id, 'rejected', user.id, payload.reason, payload.risk_level)
