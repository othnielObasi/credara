from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import Role, require_roles
from app.models.audit import AuditLog, BlockchainOutbox
from app.models.identity import User

router = APIRouter()

@router.get('/audit-logs')
def audit_logs(db: Session = Depends(get_db), user: User = Depends(require_roles(Role.ADMIN))):
    return db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(200).all()

@router.get('/blockchain-outbox')
def blockchain_outbox(db: Session = Depends(get_db), user: User = Depends(require_roles(Role.ADMIN))):
    return db.query(BlockchainOutbox).order_by(BlockchainOutbox.created_at.desc()).limit(200).all()
