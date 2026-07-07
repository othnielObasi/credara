from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any
from app.modules.kyb.provider_interface import KYBProvider

class MockKYBProvider(KYBProvider):
    """Deterministic sandbox provider for local demo and CI.

    Rules:
    - registration_number ending with BLOCK -> rejected / high risk
    - country in sanctioned demo list -> manual_review / critical
    - otherwise approved / low risk
    """
    name = 'mock'
    _manual_countries = {'IR', 'KP', 'SY'}

    async def create_applicant(self, business_payload: dict[str, Any]) -> dict[str, Any]:
        seed = f"{business_payload.get('business_id')}:{business_payload.get('legal_name')}".encode()
        applicant_id = 'mock_app_' + hashlib.sha256(seed).hexdigest()[:16]
        return {'provider_name': self.name, 'applicant_id': applicant_id, 'raw': {'created_at': _now()}}

    async def upload_document(self, applicant_id: str, document_payload: dict[str, Any]) -> dict[str, Any]:
        seed = f"{applicant_id}:{document_payload.get('file_hash')}".encode()
        return {'document_id': 'mock_doc_' + hashlib.sha256(seed).hexdigest()[:16], 'status': 'accepted'}

    async def start_check(self, applicant_id: str) -> dict[str, Any]:
        # status is finalized by service using the profile payload, but we return a stable provider check id.
        return {'check_id': 'mock_chk_' + hashlib.sha256(applicant_id.encode()).hexdigest()[:16], 'status': 'pending'}

    async def get_check_status(self, check_id: str) -> dict[str, Any]:
        return {'check_id': check_id, 'status': 'approved', 'risk_level': 'low'}

    async def parse_webhook(self, payload: dict[str, Any], headers: dict[str, str]) -> dict[str, Any]:
        status = payload.get('status') or payload.get('reviewStatus') or 'pending_review'
        return {
            'provider_event_id': payload.get('event_id') or payload.get('id'),
            'provider_check_id': payload.get('check_id') or payload.get('provider_check_id'),
            'event_type': payload.get('event_type') or 'mock.kyb.updated',
            'normalized_status': _normalize_status(status),
            'risk_level': payload.get('risk_level'),
            'raw': payload,
        }

def derive_mock_decision(profile_payload: dict[str, Any]) -> tuple[str, str, list[dict[str, str]]]:
    registration = (profile_payload.get('registration_number') or '').upper()
    country = (profile_payload.get('country') or '').upper()
    if registration.endswith('BLOCK'):
        return 'rejected', 'high', [{'flag_type': 'REGISTRATION_MISMATCH', 'severity': 'high', 'description': 'Mock KYB rejected registration number ending with BLOCK.'}]
    if country in MockKYBProvider._manual_countries:
        return 'manual_review', 'critical', [{'flag_type': 'HIGH_RISK_JURISDICTION', 'severity': 'critical', 'description': 'Mock KYB routed country to manual review.'}]
    return 'approved', 'low', []

def _normalize_status(status: str) -> str:
    value = status.lower()
    mapping = {
        'approved': 'approved', 'completed': 'approved', 'green': 'approved',
        'rejected': 'rejected', 'declined': 'rejected', 'red': 'rejected',
        'pending': 'pending_review', 'pending_review': 'pending_review', 'review': 'manual_review',
        'manual_review': 'manual_review', 'needs_more_info': 'needs_more_info',
    }
    return mapping.get(value, 'pending_review')

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
