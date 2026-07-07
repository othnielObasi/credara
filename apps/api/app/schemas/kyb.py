from datetime import datetime
from typing import Any, Literal
from pydantic import BaseModel, Field, HttpUrl

KYBStatusLiteral = Literal[
    'not_started', 'draft', 'submitted', 'pending_review', 'approved', 'rejected',
    'needs_more_info', 'manual_review', 'expired', 'suspended'
]

class KYBProfileUpsert(BaseModel):
    legal_name: str = Field(min_length=2, max_length=255)
    trading_name: str | None = None
    registration_number: str | None = None
    tax_id: str | None = None
    country: str = Field(min_length=2, max_length=2)
    business_type: str | None = None
    industry: str | None = None
    website: str | None = None
    registered_address: str | None = None
    operating_address: str | None = None

class KYBProfileRead(BaseModel):
    id: str
    business_id: str
    legal_name: str | None = None
    trading_name: str | None = None
    registration_number: str | None = None
    tax_id: str | None = None
    country: str | None = None
    business_type: str | None = None
    industry: str | None = None
    website: str | None = None
    registered_address: str | None = None
    operating_address: str | None = None
    status: str
    provider_name: str | None = None
    provider_applicant_id: str | None = None
    provider_check_id: str | None = None
    risk_level: str | None = None
    risk_notes: str | None = None
    reviewed_at: datetime | None = None
    approved_at: datetime | None = None
    rejected_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    class Config:
        from_attributes = True

class KYBDocumentCreate(BaseModel):
    document_type: str = Field(min_length=2, max_length=80)
    file_url: str = Field(min_length=3)
    file_hash: str = Field(min_length=16, max_length=128)

class KYBDocumentRead(BaseModel):
    id: str
    kyb_profile_id: str
    document_type: str
    file_url: str
    file_hash: str
    status: str
    provider_document_id: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True

class KYBSubmitResponse(BaseModel):
    business_id: str
    profile_id: str
    status: str
    provider_name: str
    provider_applicant_id: str | None = None
    provider_check_id: str | None = None
    risk_level: str | None = None
    provider_response: dict[str, Any]

class KYBWebhookResponse(BaseModel):
    accepted: bool
    provider: str
    normalized_status: str | None = None
    provider_check_id: str | None = None

class AdminKYBDecision(BaseModel):
    reason: str | None = None
    risk_level: str | None = None
