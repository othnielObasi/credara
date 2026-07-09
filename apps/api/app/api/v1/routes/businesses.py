from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.idempotency import assert_idempotent
from app.core.security import Role, require_roles
from app.models.business import Business, KYBProfile
from app.models.identity import User
from app.schemas.business import BusinessCreate, BusinessRead
from app.services.audit import record_audit

router = APIRouter()

@router.post('', response_model=BusinessRead)
def create_business(payload: BusinessCreate, idempotency_key: str | None = Header(None), db: Session = Depends(get_db), user: User = Depends(require_roles(Role.SME, Role.ADMIN))):
    assert_idempotent(db, idempotency_key, 'create_business')
    business = Business(owner_user_id=user.id, **payload.model_dump())
    db.add(business)
    db.flush()
    db.add(KYBProfile(business_id=business.id))
    record_audit(db, user.id, 'business.created', 'business', business.id)
    db.commit()
    db.refresh(business)
    return business

@router.get('', response_model=list[BusinessRead])
def list_businesses(db: Session = Depends(get_db), user: User = Depends(require_roles(Role.ADMIN, Role.SME, Role.BUYER, Role.FINANCIER))):
    q = db.query(Business)
    if user.role == Role.SME.value:
        q = q.filter(Business.owner_user_id == user.id)
    return q.order_by(Business.created_at.desc()).limit(100).all()

@router.post('/{business_id}/verify', response_model=BusinessRead)
def verify_business(business_id: str, db: Session = Depends(get_db), user: User = Depends(require_roles(Role.ADMIN))):
    business = db.get(Business, business_id)
    if not business:
        raise HTTPException(404, 'Business not found')
    business.status = 'verified'
    record_audit(db, user.id, 'business.verified', 'business', business.id)
    db.commit(); db.refresh(business)
    return business
