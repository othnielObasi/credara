from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.core.config import get_settings
from app.core.database import get_db
from app.core.security import Role, require_roles
from app.models.identity import User
from app.models.enums import ProofStatus
from app.models.trade import ProofBundle
from app.services.polygon import explorer_tx_url, publish_tx

router = APIRouter()


class AnchorProofRequest(BaseModel):
    bundle_id: str | None = None
    invoice_id: str | None = None
    business_id: str | None = None


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


@router.post('/anchor')
def anchor_proof(
    payload: AnchorProofRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.ADMIN, Role.SME, Role.BUYER, Role.FINANCIER)),
):
    bundle: ProofBundle | None = None
    if payload.bundle_id:
        bundle = db.get(ProofBundle, payload.bundle_id)
    elif payload.invoice_id:
        bundle = (
            db.query(ProofBundle)
            .filter(ProofBundle.invoice_id == payload.invoice_id)
            .order_by(ProofBundle.created_at.desc())
            .first()
        )
    elif payload.business_id:
        bundle = (
            db.query(ProofBundle)
            .filter(ProofBundle.business_id == payload.business_id)
            .order_by(ProofBundle.created_at.desc())
            .first()
        )
    else:
        raise HTTPException(400, 'bundle_id, invoice_id, or business_id is required')
    if not bundle:
        raise HTTPException(404, 'Proof bundle not found')

    tx_hash, on_chain = publish_tx(f'anchor:{bundle.id}:{bundle.proof_hash}', proof_hash=bundle.proof_hash)
    bundle.polygon_tx_hash = tx_hash
    bundle.status = ProofStatus.ANCHORED.value
    db.commit()
    db.refresh(bundle)
    return {
        'bundle_id': bundle.id,
        'proof_hash': bundle.proof_hash,
        'polygon_tx_hash': tx_hash,
        'on_chain': on_chain,
        'explorer_url': explorer_tx_url(tx_hash),
    }
