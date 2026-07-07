from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import Role, require_roles
from app.models.business import Business
from app.models.identity import User
from app.schemas.finance import FinanceReadinessRead, TrustScoreRead
from app.services.scoring import build_finance_readiness_report, calculate_trade_credit_score

router = APIRouter()

def _require_business_access(business: Business, user: User) -> None:
    # SMEs may only score/review their own business; financiers and admins
    # legitimately need to review other businesses' credit as part of the
    # financing workflow, so they keep full access.
    if user.role == Role.SME.value and business.owner_user_id != user.id:
        raise HTTPException(403, 'You do not have access to this business')

@router.post('/businesses/{business_id}/score', response_model=TrustScoreRead)
def calculate_score(business_id: str, db: Session = Depends(get_db), user: User = Depends(require_roles(Role.ADMIN, Role.FINANCIER, Role.SME))):
    business = db.get(Business, business_id)
    if not business:
        raise HTTPException(404, 'Business not found')
    _require_business_access(business, user)
    score = calculate_trade_credit_score(db, business_id)
    db.commit(); db.refresh(score)
    return score

@router.post('/businesses/{business_id}/readiness', response_model=FinanceReadinessRead)
def readiness(business_id: str, db: Session = Depends(get_db), user: User = Depends(require_roles(Role.ADMIN, Role.FINANCIER, Role.SME))):
    business = db.get(Business, business_id)
    if not business:
        raise HTTPException(404, 'Business not found')
    _require_business_access(business, user)
    report = build_finance_readiness_report(db, business_id)
    db.commit(); db.refresh(report)
    return report
