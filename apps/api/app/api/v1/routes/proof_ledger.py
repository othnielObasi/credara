from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.config import get_settings
from app.core.database import get_db
from app.core.security import Role, require_roles
from app.models.identity import User
from app.models.trade import ProofBundle

router = APIRouter()

@router.get('')
def proof_ledger(db: Session = Depends(get_db), user: User = Depends(require_roles(Role.ADMIN, Role.SME, Role.BUYER, Role.FINANCIER))):
    settings = get_settings()
    bundles = db.query(ProofBundle).order_by(ProofBundle.created_at.desc()).limit(100).all()
    return [{
        'id': b.id,
        'business_id': b.business_id,
        'bundle_type': b.bundle_type,
        'proof_hash': b.proof_hash,
        'status': b.status,
        'polygon_tx_hash': b.polygon_tx_hash,
        'explorer_url': f"{settings.polygon_explorer_base}/tx/{b.polygon_tx_hash}" if b.polygon_tx_hash else None,
        'created_at': b.created_at,
    } for b in bundles]
