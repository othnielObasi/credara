from datetime import datetime
from uuid import uuid4
from sqlalchemy import DateTime, JSON, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base
from app.models.enums import OutboxStatus

class AuditLog(Base):
    __tablename__ = 'audit_logs'
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    actor_user_id: Mapped[str | None] = mapped_column(String, index=True)
    action: Mapped[str] = mapped_column(String(120), index=True)
    resource_type: Mapped[str] = mapped_column(String(120))
    resource_id: Mapped[str] = mapped_column(String, index=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class IdempotencyKey(Base):
    __tablename__ = 'idempotency_keys'
    __table_args__ = (UniqueConstraint('key', 'scope', name='uq_idempotency_key_scope'),)
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    key: Mapped[str] = mapped_column(String(255), index=True)
    scope: Mapped[str] = mapped_column(String(120), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class BlockchainOutbox(Base):
    __tablename__ = 'blockchain_outbox'
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    action: Mapped[str] = mapped_column(String(120), index=True)
    payload_json: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(50), default=OutboxStatus.PENDING.value, index=True)
    attempts: Mapped[int] = mapped_column(default=0)
    last_error: Mapped[str | None] = mapped_column(String(1000))
    tx_hash: Mapped[str | None] = mapped_column(String(120))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
