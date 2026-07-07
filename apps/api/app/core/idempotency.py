from fastapi import Header, HTTPException, status
from sqlalchemy.orm import Session
from app.models.audit import IdempotencyKey


def assert_idempotent(db: Session, key: str | None, scope: str) -> None:
    if not key:
        return
    existing = db.query(IdempotencyKey).filter_by(key=key, scope=scope).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='Duplicate idempotency key')
    db.add(IdempotencyKey(key=key, scope=scope))
