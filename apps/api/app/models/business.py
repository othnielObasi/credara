from datetime import datetime
from uuid import uuid4
from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.enums import BusinessStatus

class Business(Base):
    __tablename__ = 'businesses'
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    owner_user_id: Mapped[str] = mapped_column(ForeignKey('users.id'), nullable=False, index=True)
    legal_name: Mapped[str] = mapped_column(String(255), nullable=False)
    country: Mapped[str] = mapped_column(String(2), nullable=False)
    registration_number: Mapped[str | None] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(50), default=BusinessStatus.PENDING_KYB.value)
    industry: Mapped[str | None] = mapped_column(String(100))
    wallet_address: Mapped[str | None] = mapped_column(String(120))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class KYBProfile(Base):
    __tablename__ = 'business_kyb_profiles'
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    business_id: Mapped[str] = mapped_column(ForeignKey('businesses.id'), nullable=False, index=True)
    legal_name: Mapped[str | None] = mapped_column(String(255))
    trading_name: Mapped[str | None] = mapped_column(String(255))
    registration_number: Mapped[str | None] = mapped_column(String(100))
    tax_id: Mapped[str | None] = mapped_column(String(100))
    country: Mapped[str | None] = mapped_column(String(2))
    business_type: Mapped[str | None] = mapped_column(String(80))
    industry: Mapped[str | None] = mapped_column(String(100))
    website: Mapped[str | None] = mapped_column(String(255))
    registered_address: Mapped[str | None] = mapped_column(Text)
    operating_address: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(50), default='not_started')
    provider_name: Mapped[str | None] = mapped_column(String(80))
    provider_applicant_id: Mapped[str | None] = mapped_column(String(255), index=True)
    provider_check_id: Mapped[str | None] = mapped_column(String(255), index=True)
    risk_level: Mapped[str | None] = mapped_column(String(50))
    risk_notes: Mapped[str | None] = mapped_column(Text)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime)
    rejected_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

from sqlalchemy import JSON, Integer
from app.models.enums import KYBStatus, KYBRiskLevel

class KYBDocument(Base):
    __tablename__ = 'kyb_documents'
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    kyb_profile_id: Mapped[str] = mapped_column(ForeignKey('business_kyb_profiles.id'), nullable=False, index=True)
    document_type: Mapped[str] = mapped_column(String(80), nullable=False)
    file_url: Mapped[str] = mapped_column(Text, nullable=False)
    file_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default='uploaded')
    provider_document_id: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class KYBCheck(Base):
    __tablename__ = 'kyb_checks'
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    kyb_profile_id: Mapped[str] = mapped_column(ForeignKey('business_kyb_profiles.id'), nullable=False, index=True)
    provider_name: Mapped[str] = mapped_column(String(80), nullable=False)
    provider_check_id: Mapped[str | None] = mapped_column(String(255), index=True)
    status: Mapped[str] = mapped_column(String(50), default=KYBStatus.SUBMITTED.value)
    risk_level: Mapped[str | None] = mapped_column(String(50))
    raw_response_json: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class KYBWebhookEvent(Base):
    __tablename__ = 'kyb_webhook_events'
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    provider_name: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    provider_event_id: Mapped[str | None] = mapped_column(String(255), index=True)
    provider_check_id: Mapped[str | None] = mapped_column(String(255), index=True)
    event_type: Mapped[str] = mapped_column(String(120), nullable=False)
    normalized_status: Mapped[str | None] = mapped_column(String(50))
    payload_json: Mapped[dict] = mapped_column(JSON, default=dict)
    processed: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class KYBRiskFlag(Base):
    __tablename__ = 'kyb_risk_flags'
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    kyb_profile_id: Mapped[str] = mapped_column(ForeignKey('business_kyb_profiles.id'), nullable=False, index=True)
    flag_type: Mapped[str] = mapped_column(String(120), nullable=False)
    severity: Mapped[str] = mapped_column(String(50), default=KYBRiskLevel.MEDIUM.value)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str] = mapped_column(String(80), default='kyb_provider')
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
