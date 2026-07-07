from __future__ import annotations

import hashlib
import hmac
import json
import time
from typing import Any

import httpx
from fastapi import HTTPException, status

from app.core.config import get_settings
from app.modules.kyb.provider_interface import KYBProvider

DIDIT_BASE_URL = 'https://verification.didit.me'
WEBHOOK_TIMESTAMP_TOLERANCE_SECONDS = 300

_STATUS_MAP = {
    'approved': 'approved',
    'declined': 'rejected',
    'in review': 'manual_review',
    'resubmitted': 'needs_more_info',
    'not started': 'pending_review',
    'in progress': 'pending_review',
    'awaiting user': 'pending_review',
    'expired': 'rejected',
    'kyc expired': 'rejected',
    'abandoned': 'rejected',
}


def _normalize_status(raw_status: str | None) -> str:
    if not raw_status:
        return 'pending_review'
    return _STATUS_MAP.get(raw_status.strip().lower(), 'pending_review')


class DiditKYBProvider(KYBProvider):
    """Didit (https://docs.didit.me) session-based KYB provider.

    Didit runs verification as a single hosted session rather than a
    document-by-document upload API: create_applicant() opens the session
    and the business completes it via the returned hosted URL; the decision
    arrives asynchronously via webhook, or can be polled via get_check_status().
    upload_document() has no Didit equivalent - documents are captured inside
    the hosted session itself, so it's recorded locally only.
    """

    name = 'didit'

    def __init__(self) -> None:
        settings = get_settings()
        if not settings.didit_api_key:
            raise ValueError('DIDIT_API_KEY is not configured')
        if not settings.didit_workflow_id:
            raise ValueError('DIDIT_WORKFLOW_ID is not configured')
        self._api_key = settings.didit_api_key
        self._workflow_id = settings.didit_workflow_id
        self._webhook_secret = settings.didit_webhook_secret

    def _client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            base_url=DIDIT_BASE_URL,
            headers={'x-api-key': self._api_key, 'Content-Type': 'application/json'},
            timeout=15.0,
        )

    async def create_applicant(self, business_payload: dict[str, Any]) -> dict[str, Any]:
        body = {
            'workflow_id': self._workflow_id,
            'vendor_data': business_payload.get('business_id'),
            'expected_details': {
                'company_name': business_payload.get('legal_name'),
                'registry_country': business_payload.get('country'),
                'registration_number': business_payload.get('registration_number'),
            },
        }
        async with self._client() as client:
            response = await client.post('/v3/session/', json=body)
        response.raise_for_status()
        data = response.json()
        return {'provider_name': self.name, 'applicant_id': data['session_id'], 'raw': data}

    async def upload_document(self, applicant_id: str, document_payload: dict[str, Any]) -> dict[str, Any]:
        return {'document_id': f'didit_doc_{applicant_id}', 'status': 'pending_hosted_session'}

    async def start_check(self, applicant_id: str) -> dict[str, Any]:
        # Didit's v3 API has no separate "start check" call - the check begins
        # the moment the session is created. Return the session's current status.
        async with self._client() as client:
            response = await client.get(f'/v3/session/{applicant_id}/decision/')
        response.raise_for_status()
        data = response.json()
        return {'check_id': applicant_id, 'status': data.get('status'), 'raw': data}

    async def get_check_status(self, check_id: str) -> dict[str, Any]:
        async with self._client() as client:
            response = await client.get(f'/v3/session/{check_id}/decision/')
        response.raise_for_status()
        data = response.json()
        return {
            'check_id': check_id,
            'status': _normalize_status(data.get('status')),
            'risk_level': None,
            'raw': data,
        }

    async def parse_webhook(self, payload: dict[str, Any], headers: dict[str, str]) -> dict[str, Any]:
        self._verify_signature(payload, headers)
        return {
            'provider_event_id': payload.get('event_id'),
            'provider_check_id': payload.get('session_id'),
            'event_type': payload.get('webhook_type') or 'didit.kyb.updated',
            'normalized_status': _normalize_status(payload.get('status')),
            'risk_level': None,
            'raw': payload,
        }

    def _verify_signature(self, payload: dict[str, Any], headers: dict[str, str]) -> None:
        if not self._webhook_secret:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, 'DIDIT_WEBHOOK_SECRET is not configured')

        lower_headers = {k.lower(): v for k, v in headers.items()}
        signature = lower_headers.get('x-signature-v2')
        timestamp = lower_headers.get('x-timestamp')
        if not signature or not timestamp:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, 'Missing Didit webhook signature headers')

        try:
            timestamp_value = int(timestamp)
        except ValueError:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, 'Invalid Didit webhook timestamp')
        if abs(int(time.time()) - timestamp_value) > WEBHOOK_TIMESTAMP_TOLERANCE_SECONDS:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, 'Didit webhook timestamp outside tolerance window')

        # V2 scheme per Didit docs: HMAC-SHA256 over the recursively key-sorted,
        # Unicode-preserved canonical JSON - re-derivable from the parsed body,
        # so it verifies correctly even though FastAPI has already decoded it.
        canonical = json.dumps(payload, sort_keys=True, separators=(',', ':'), ensure_ascii=False)
        expected = hmac.new(self._webhook_secret.encode(), canonical.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected):
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, 'Didit webhook signature verification failed')
