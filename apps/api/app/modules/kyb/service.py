from __future__ import annotations

from datetime import datetime
from typing import Any
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.business import Business, KYBCheck, KYBDocument, KYBProfile, KYBRiskFlag, KYBWebhookEvent
from app.models.enums import BusinessStatus
from app.modules.kyb.provider_factory import get_kyb_provider
from app.modules.kyb.providers.mock_provider import derive_mock_decision
from app.schemas.kyb import KYBDocumentCreate, KYBProfileUpsert
from app.services.audit import record_audit


def get_or_create_profile(db: Session, business_id: str) -> KYBProfile:
    business = db.get(Business, business_id)
    if not business:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Business not found')
    profile = db.query(KYBProfile).filter(KYBProfile.business_id == business_id).first()
    if not profile:
        profile = KYBProfile(business_id=business_id, status='not_started')
        db.add(profile)
        db.flush()
    return profile


def upsert_profile(db: Session, business_id: str, payload: KYBProfileUpsert, actor_user_id: str) -> KYBProfile:
    business = db.get(Business, business_id)
    if not business:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Business not found')
    profile = get_or_create_profile(db, business_id)
    for key, value in payload.model_dump().items():
        setattr(profile, key, value)
    profile.status = 'draft' if profile.status in {'not_started', 'rejected', 'needs_more_info'} else profile.status
    record_audit(db, actor_user_id, 'kyb.profile.upserted', 'business', business_id)
    db.commit(); db.refresh(profile)
    return profile


def add_document(db: Session, business_id: str, payload: KYBDocumentCreate, actor_user_id: str) -> KYBDocument:
    profile = get_or_create_profile(db, business_id)
    doc = KYBDocument(kyb_profile_id=profile.id, **payload.model_dump())
    db.add(doc)
    record_audit(db, actor_user_id, 'kyb.document.uploaded', 'kyb_profile', profile.id)
    db.commit(); db.refresh(doc)
    return doc


async def submit_kyb(db: Session, business_id: str, actor_user_id: str) -> dict[str, Any]:
    business = db.get(Business, business_id)
    if not business:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Business not found')
    profile = get_or_create_profile(db, business_id)
    if not profile.legal_name or not profile.country:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail='KYB profile requires legal_name and country before submission')

    provider = get_kyb_provider()
    business_payload = {
        'business_id': business.id,
        'legal_name': profile.legal_name,
        'trading_name': profile.trading_name,
        'registration_number': profile.registration_number,
        'tax_id': profile.tax_id,
        'country': profile.country,
        'business_type': profile.business_type,
        'industry': profile.industry,
        'website': profile.website,
        'registered_address': profile.registered_address,
        'operating_address': profile.operating_address,
    }
    applicant = await provider.create_applicant(business_payload)
    profile.provider_name = provider.name
    profile.provider_applicant_id = applicant.get('applicant_id')

    documents = db.query(KYBDocument).filter(KYBDocument.kyb_profile_id == profile.id).all()
    for doc in documents:
        upload = await provider.upload_document(profile.provider_applicant_id or profile.id, {
            'document_type': doc.document_type,
            'file_url': doc.file_url,
            'file_hash': doc.file_hash,
        })
        doc.provider_document_id = upload.get('document_id')
        doc.status = upload.get('status', 'submitted')

    check = await provider.start_check(profile.provider_applicant_id or profile.id)
    profile.provider_check_id = check.get('check_id')

    if provider.name == 'mock':
        final_status, risk_level, flags = derive_mock_decision(business_payload)
    else:
        final_status, risk_level, flags = 'pending_review', None, []

    profile.status = final_status
    profile.risk_level = risk_level
    now = datetime.utcnow()
    if final_status == 'approved':
        profile.approved_at = now
        business.status = BusinessStatus.VERIFIED.value
    elif final_status == 'rejected':
        profile.rejected_at = now
        business.status = BusinessStatus.PENDING_KYB.value
    else:
        business.status = BusinessStatus.PENDING_KYB.value

    kyb_check = KYBCheck(
        kyb_profile_id=profile.id,
        provider_name=provider.name,
        provider_check_id=profile.provider_check_id,
        status=final_status,
        risk_level=risk_level,
        raw_response_json={'applicant': applicant, 'check': check},
    )
    db.add(kyb_check)
    for flag in flags:
        db.add(KYBRiskFlag(kyb_profile_id=profile.id, source=provider.name, **flag))

    record_audit(db, actor_user_id, 'kyb.submitted', 'business', business_id)
    db.commit(); db.refresh(profile)
    return {
        'business_id': business.id,
        'profile_id': profile.id,
        'status': profile.status,
        'provider_name': provider.name,
        'provider_applicant_id': profile.provider_applicant_id,
        'provider_check_id': profile.provider_check_id,
        'risk_level': profile.risk_level,
        'provider_response': {'applicant': applicant, 'check': check},
    }


async def process_webhook(db: Session, provider_name: str, payload: dict[str, Any], headers: dict[str, str]) -> dict[str, Any]:
    provider = get_kyb_provider()
    # Allow provider-specific endpoint path to differ from configured provider for future providers.
    parsed = await provider.parse_webhook(payload, headers)
    event = KYBWebhookEvent(
        provider_name=provider_name,
        provider_event_id=parsed.get('provider_event_id'),
        provider_check_id=parsed.get('provider_check_id'),
        event_type=parsed.get('event_type', f'{provider_name}.kyb.updated'),
        normalized_status=parsed.get('normalized_status'),
        payload_json=parsed.get('raw', payload),
        processed=1,
    )
    db.add(event)

    check_id = parsed.get('provider_check_id')
    normalized_status = parsed.get('normalized_status')
    profile = None
    if check_id:
        profile = db.query(KYBProfile).filter(KYBProfile.provider_check_id == check_id).first()
    if profile and normalized_status:
        profile.status = normalized_status
        profile.risk_level = parsed.get('risk_level') or profile.risk_level
        now = datetime.utcnow()
        if normalized_status == 'approved':
            profile.approved_at = now
            business = db.get(Business, profile.business_id)
            if business:
                business.status = BusinessStatus.VERIFIED.value
        elif normalized_status == 'rejected':
            profile.rejected_at = now
    db.commit()
    return {'accepted': True, 'provider': provider_name, 'normalized_status': normalized_status, 'provider_check_id': check_id}


def admin_decision(db: Session, profile_id: str, decision: str, actor_user_id: str, reason: str | None, risk_level: str | None = None) -> KYBProfile:
    profile = db.get(KYBProfile, profile_id)
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='KYB profile not found')
    if decision not in {'approved', 'rejected', 'manual_review', 'needs_more_info'}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Unsupported KYB decision')
    profile.status = decision
    profile.risk_notes = reason
    profile.risk_level = risk_level or profile.risk_level
    profile.reviewed_at = datetime.utcnow()
    business = db.get(Business, profile.business_id)
    if decision == 'approved':
        profile.approved_at = datetime.utcnow()
        if business:
            business.status = BusinessStatus.VERIFIED.value
    elif decision == 'rejected':
        profile.rejected_at = datetime.utcnow()
        if business:
            business.status = BusinessStatus.PENDING_KYB.value
    record_audit(db, actor_user_id, f'kyb.admin.{decision}', 'kyb_profile', profile.id)
    db.commit(); db.refresh(profile)
    return profile
