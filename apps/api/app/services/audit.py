from sqlalchemy.orm import Session
from app.models.audit import AuditLog


def record_audit(db: Session, actor_user_id: str | None, action: str, resource_type: str, resource_id: str, metadata: dict | None = None) -> None:
    db.add(AuditLog(actor_user_id=actor_user_id, action=action, resource_type=resource_type, resource_id=resource_id, metadata_json=metadata or {}))
