
from __future__ import annotations

from datetime import datetime
from hashlib import sha256
import secrets
from uuid import uuid4
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import or_, select, func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import Role, get_current_user
from app.models.identity import User
from app.models.business import Business
from app.models.real_workflow import (
    APIKeyRecord, EscrowAccountRecord, InvitationRecord, Membership,
    OnboardingProgressRecord, PaymentIntentRecord, ReconciliationRecord,
    SettlementLedgerRecord, UserSettingsRecord, WalletAccountRecord,
    WebhookEndpointRecord, Workspace,
)

router = APIRouter(prefix="/real", tags=["real-workflow-wiring"])


# ---------- Schemas ----------
class StartOnboardingRequest(BaseModel):
    role: str
    business_name: str
    country: str = "AE"
    registration_number: Optional[str] = None
    sector: Optional[str] = None
    wallet_address: Optional[str] = None


class InviteCreateRequest(BaseModel):
    from_workspace_id: str
    from_business_name: str
    to_email: str
    invite_type: str
    invited_role: str
    target_type: str
    target_id: str
    target_route: str
    message: Optional[str] = None


class InviteDecisionRequest(BaseModel):
    email: str
    full_name: str
    decision: str = Field(pattern="^(accept|reject)$")
    reason: Optional[str] = None


class SettingsUpsertRequest(BaseModel):
    workspace_id: Optional[str] = None
    profile: Dict[str, Any] = Field(default_factory=dict)
    workspace: Dict[str, Any] = Field(default_factory=dict)
    notifications: Dict[str, Any] = Field(default_factory=dict)
    security: Dict[str, Any] = Field(default_factory=dict)
    developer: Dict[str, Any] = Field(default_factory=dict)
    admin: Dict[str, Any] = Field(default_factory=dict)


class WalletCreateRequest(BaseModel):
    workspace_id: str
    business_id: Optional[str] = None
    owner_name: str
    wallet_type: str = "connected"
    address: str
    network: str = "Polygon Amoy"
    stablecoin_asset: str = "MockUSDC"
    stablecoin_balance: float = 0
    gas_balance: float = 0


class PaymentIntentCreateRequest(BaseModel):
    workspace_id: str
    intent_type: str
    payer_wallet_id: Optional[str] = None
    payee_reference: str
    reference_type: str
    reference_id: str
    amount: float
    asset: str = "MockUSDC"
    idempotency_key: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SubmitTxRequest(BaseModel):
    tx_hash: str
    confirmations: int = 0


class ConfirmTxRequest(BaseModel):
    confirmations: int = 3
    on_chain_amount: Optional[float] = None


class EscrowCreateRequest(BaseModel):
    workspace_id: str
    smart_lc_id: str
    contract_address: Optional[str] = None
    required_amount: float
    funding_party: str
    seller: str
    asset: str = "MockUSDC"
    release_condition: str = "Invoice confirmed + delivery verified + proof anchored + no dispute"
    refund_condition: str = "Deadline missed or dispute upheld"


class EscrowFundRequest(BaseModel):
    payment_intent_id: str


class EscrowReleaseRequest(BaseModel):
    reason: str = "Release conditions satisfied"


class APIKeyCreateRequest(BaseModel):
    workspace_id: str
    name: str
    scopes: List[str] = Field(default_factory=lambda: ["proof:read", "receivables:write"])


class WebhookCreateRequest(BaseModel):
    workspace_id: str
    url: str
    events: List[str] = Field(default_factory=lambda: ["proof.anchored", "payment.confirmed"])


# ---------- Helpers ----------
def hash_value(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


def public_user(user: User) -> Dict[str, Any]:
    return {"id": user.id, "email": user.email, "full_name": user.full_name, "role": user.role}


def public_business(b: Business) -> Dict[str, Any]:
    return {"id": b.id, "legal_name": b.legal_name, "country": b.country, "registration_number": b.registration_number, "status": b.status, "industry": b.industry, "wallet_address": b.wallet_address}


def public_workspace(w: Workspace) -> Dict[str, Any]:
    return {"id": w.id, "business_id": w.business_id, "name": w.name, "primary_role": w.primary_role, "environment": w.environment, "region": w.region, "status": w.status}


def _member_workspace_ids(db: Session, user: User) -> List[str]:
    rows = db.scalars(
        select(Membership.workspace_id).where(Membership.user_id == user.id, Membership.status == "active")
    ).all()
    return list(rows)


def _require_workspace_access(db: Session, user: User, workspace_id: Optional[str]) -> None:
    """Raise 403 unless the caller is an admin or an active member of workspace_id."""
    if user.role == Role.ADMIN.value:
        return
    if not workspace_id:
        raise HTTPException(403, "workspace_id is required")
    member = db.scalar(
        select(Membership).where(
            Membership.workspace_id == workspace_id,
            Membership.user_id == user.id,
            Membership.status == "active",
        )
    )
    if not member:
        raise HTTPException(403, "You do not have access to this workspace")


def _require_admin(user: User) -> None:
    if user.role != Role.ADMIN.value:
        raise HTTPException(403, "Admin role required")


def ledger_entry(
    db: Session,
    *,
    workspace_id: Optional[str],
    track: str,
    role: str,
    event: str,
    source: str,
    description: str,
    amount: float,
    status: str,
    verifier: Optional[str],
    reference_type: str,
    reference_id: str,
    docs: Optional[List[str]] = None,
) -> SettlementLedgerRecord:
    row = SettlementLedgerRecord(
        workspace_id=workspace_id,
        track=track,
        role=role,
        event=event,
        source=source,
        description=description,
        amount=amount,
        status=status,
        verifier=verifier,
        reference_type=reference_type,
        reference_id=reference_id,
        docs_json=docs or [],
    )
    db.add(row)
    db.flush()
    return row


def serialize_ledger(row: SettlementLedgerRecord) -> Dict[str, Any]:
    return {
        "id": row.id,
        "timestamp": row.created_at.isoformat(),
        "track": row.track,
        "role": row.role,
        "event": row.event,
        "source": row.source,
        "description": row.description,
        "amount": float(row.amount or 0),
        "asset": row.asset,
        "status": row.status,
        "verifier": row.verifier,
        "reference_type": row.reference_type,
        "reference_id": row.reference_id,
        "docs": row.docs_json or [],
    }


ROLE_ALLOWED = {
    "sme": ["dashboard","contractDetail","invoiceDetail","delivery","receivables","directory","opportunities","proposals","marketplace","wallets","settlement","settlementLedger","reconciliation","repayments","proof","evidence","credit","kyb","onboarding","businessProfile","invitations","members","settings"],
    "buyer": ["dashboard","buyerInbox","contractDetail","invoiceDetail","delivery","directory","opportunities","wallets","settlement","settlementLedger","reconciliation","repayments","proof","evidence","credit","kyb","onboarding","businessProfile","invitations","members","settings"],
    "financier": ["dashboard","marketplace","dealRoom","receivables","evidence","credit","kyb","wallets","settlementLedger","reconciliation","repayments","proof","directory","onboarding","businessProfile","invitations","members","settings"],
    "admin": ["dashboard","admin","riskRules","permissions","kyb","proof","evidence","settlementLedger","reconciliation","wallets","onboarding","businessProfile","invitations","members","settings","launch","apiExplorer"],
    "developer": ["dashboard","settings","apiExplorer","onboarding","businessProfile","members","proof","wallets","settlementLedger"],
}


# ---------- Workspaces ----------
@router.get("/workspaces/me")
def my_workspaces(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if user.role == Role.ADMIN.value:
        memberships = db.scalars(select(Membership).where(Membership.status == "active")).all()
    else:
        memberships = db.scalars(
            select(Membership).where(Membership.user_id == user.id, Membership.status == "active")
        ).all()

    rows = []
    for membership in memberships:
        workspace = db.get(Workspace, membership.workspace_id)
        if not workspace:
            continue
        business = db.get(Business, workspace.business_id)
        progress = db.scalar(
            select(OnboardingProgressRecord).where(OnboardingProgressRecord.workspace_id == workspace.id)
        )
        rows.append(
            {
                "workspace": public_workspace(workspace),
                "business": public_business(business) if business else None,
                "membership": {
                    "id": membership.id,
                    "role": membership.role,
                    "status": membership.status,
                    "permissions": membership.permissions_json,
                },
                "progress": {
                    "workspace_id": progress.workspace_id,
                    "percent": progress.percent_complete,
                    "kyb_status": progress.kyb_status,
                    "wallet_status": progress.wallet_status,
                    "first_workflow": progress.first_workflow,
                }
                if progress
                else None,
            }
        )
    return {"user": public_user(user), "workspaces": rows}


# ---------- Onboarding ----------
@router.post("/onboarding/start")
def start_onboarding(
    request: StartOnboardingRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # Provisions a business + workspace for the already-authenticated user (via
    # /auth/register + /auth/login). Identity comes from the JWT, never from the
    # request body, so this can't be used to attach resources to someone else's account.
    business = Business(
        owner_user_id=user.id,
        legal_name=request.business_name,
        country=request.country[:2].upper(),
        registration_number=request.registration_number,
        industry=request.sector,
        wallet_address=request.wallet_address,
        status="pending_kyb",
    )
    db.add(business)
    db.flush()

    workspace = Workspace(
        business_id=business.id,
        name=request.business_name,
        primary_role=request.role,
        environment="sandbox",
        region=request.country,
    )
    db.add(workspace)
    db.flush()

    membership = Membership(
        workspace_id=workspace.id,
        user_id=user.id,
        role=request.role,
        permissions_json={"pages": ROLE_ALLOWED.get(request.role, [])},
    )
    db.add(membership)
    db.flush()

    progress = OnboardingProgressRecord(
        workspace_id=workspace.id,
        account_created=True,
        email_verified=True,
        role_selected=True,
        business_profile_created=True,
        kyb_status="pending_review",
        wallet_status="connected" if request.wallet_address else "not_connected",
        first_workflow=None,
        percent_complete=70 if request.wallet_address else 58,
    )
    db.add(progress)
    db.commit()

    return {
        "user": public_user(user),
        "business": public_business(business),
        "workspace": public_workspace(workspace),
        "membership_id": membership.id,
        "progress": {
            "workspace_id": progress.workspace_id,
            "percent": progress.percent_complete,
            "kyb_status": progress.kyb_status,
            "wallet_status": progress.wallet_status,
        },
    }


@router.get("/onboarding/progress/{workspace_id}")
def onboarding_progress(
    workspace_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _require_workspace_access(db, user, workspace_id)
    progress = db.scalar(select(OnboardingProgressRecord).where(OnboardingProgressRecord.workspace_id == workspace_id))
    if not progress:
        raise HTTPException(404, "Onboarding progress not found")
    return {
        "workspace_id": progress.workspace_id,
        "percent": progress.percent_complete,
        "account_created": progress.account_created,
        "email_verified": progress.email_verified,
        "role_selected": progress.role_selected,
        "business_profile_created": progress.business_profile_created,
        "kyb_status": progress.kyb_status,
        "wallet_status": progress.wallet_status,
        "first_workflow": progress.first_workflow,
        "updated_at": progress.updated_at.isoformat(),
    }


# ---------- Role navigation / permissions ----------
# Static role -> page maps; not per-tenant data, so authentication (any role) is
# enough here - no workspace ownership to check.
@router.get("/access/navigation/{role}")
def navigation_for_role(role: str, user: User = Depends(get_current_user)):
    return {"role": role, "allowed_pages": ROLE_ALLOWED.get(role, ROLE_ALLOWED["sme"])}


@router.get("/access/can-access/{role}/{page}")
def can_access(role: str, page: str, user: User = Depends(get_current_user)):
    allowed = ROLE_ALLOWED.get(role, [])
    return {"role": role, "page": page, "allowed": page in allowed}


# ---------- Invitations ----------
@router.post("/invitations")
def create_invitation(
    request: InviteCreateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _require_workspace_access(db, user, request.from_workspace_id)
    token = secrets.token_urlsafe(32)
    invite = InvitationRecord(
        token=token,
        from_workspace_id=request.from_workspace_id,
        from_business_name=request.from_business_name,
        to_email=request.to_email,
        invite_type=request.invite_type,
        invited_role=request.invited_role,
        target_type=request.target_type,
        target_id=request.target_id,
        target_route=request.target_route,
        message=request.message,
        status="pending",
    )
    db.add(invite)
    db.commit()
    return {
        "id": invite.id,
        "token": invite.token,
        "invite_url": f"/accept-invite?token={invite.token}",
        "status": invite.status,
        "target_route": invite.target_route,
        "email_delivery": "queued_for_provider",
    }


@router.get("/invitations")
def list_invitations(
    status: Optional[str] = None,
    to_email: Optional[str] = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    stmt = select(InvitationRecord).order_by(InvitationRecord.created_at.desc())
    if status:
        stmt = stmt.where(InvitationRecord.status == status)

    if user.role == Role.ADMIN.value:
        if to_email:
            stmt = stmt.where(InvitationRecord.to_email == to_email)
    else:
        workspace_ids = list(
            db.scalars(
                select(Membership.workspace_id).where(
                    Membership.user_id == user.id,
                    Membership.status == "active",
                )
            ).all()
        )
        filters = [InvitationRecord.to_email == user.email]
        if workspace_ids:
            filters.append(InvitationRecord.from_workspace_id.in_(workspace_ids))
        stmt = stmt.where(or_(*filters))

    rows = db.scalars(stmt).all()
    return [
        {
            "id": r.id,
            "token": r.token,
            "from_business_name": r.from_business_name,
            "to_email": r.to_email,
            "invite_type": r.invite_type,
            "invited_role": r.invited_role,
            "target_type": r.target_type,
            "target_id": r.target_id,
            "target_route": r.target_route,
            "status": r.status,
            "message": r.message,
            "created_at": r.created_at.isoformat(),
        }
        for r in rows
    ]


@router.get("/invitations/token/{token}")
def get_invitation_by_token(token: str, db: Session = Depends(get_db)):
    # Intentionally unauthenticated: the token itself is the credential, since the
    # recipient may not have an account yet at the time they open the invite link.
    invite = db.scalar(select(InvitationRecord).where(InvitationRecord.token == token))
    if not invite:
        raise HTTPException(404, "Invitation not found")
    return {
        "id": invite.id,
        "from_business_name": invite.from_business_name,
        "to_email": invite.to_email,
        "invite_type": invite.invite_type,
        "invited_role": invite.invited_role,
        "target_type": invite.target_type,
        "target_id": invite.target_id,
        "target_route": invite.target_route,
        "status": invite.status,
        "message": invite.message,
    }


@router.post("/invitations/token/{token}/decision")
def decide_invitation(token: str, request: InviteDecisionRequest, db: Session = Depends(get_db)):
    # Same token-as-credential model as get_invitation_by_token above.
    invite = db.scalar(select(InvitationRecord).where(InvitationRecord.token == token))
    if not invite:
        raise HTTPException(404, "Invitation not found")
    if invite.status not in ("pending", "open"):
        raise HTTPException(409, f"Invitation already {invite.status}")
    if request.decision == "accept" and request.email.lower() != invite.to_email.lower():
        raise HTTPException(403, "This invitation was not addressed to this email")

    user = db.scalar(select(User).where(User.email == request.email))
    if not user:
        user = User(email=request.email, full_name=request.full_name, role=invite.invited_role, password_hash="managed-by-clerk-or-oidc")
        db.add(user)
        db.flush()

    invite.status = "accepted" if request.decision == "accept" else "rejected"
    invite.accepted_by_user_id = user.id if request.decision == "accept" else None
    invite.decision_reason = request.reason
    invite.decided_at = datetime.utcnow()

    db.commit()
    return {
        "status": invite.status,
        "target_route": invite.target_route if invite.status == "accepted" else None,
        "user": public_user(user),
    }


# ---------- Settings ----------
@router.get("/settings")
def get_settings(
    workspace_id: Optional[str] = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if workspace_id:
        _require_workspace_access(db, user, workspace_id)
    stmt = select(UserSettingsRecord).where(UserSettingsRecord.user_id == user.id)
    if workspace_id:
        stmt = stmt.where(UserSettingsRecord.workspace_id == workspace_id)
    settings = db.scalar(stmt.order_by(UserSettingsRecord.updated_at.desc()))
    if not settings:
        return {
            "profile": {},
            "workspace": {},
            "notifications": {"payment": True, "proof": True, "kyb": True, "invites": True},
            "security": {"mfa": True, "role_filtering": True},
            "developer": {},
            "admin": {},
        }
    return {
        "id": settings.id,
        "profile": settings.profile_json,
        "workspace": settings.workspace_json,
        "notifications": settings.notifications_json,
        "security": settings.security_json,
        "developer": settings.developer_json,
        "admin": settings.admin_json,
        "updated_at": settings.updated_at.isoformat(),
    }


@router.put("/settings")
def upsert_settings(
    request: SettingsUpsertRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if request.workspace_id:
        _require_workspace_access(db, user, request.workspace_id)
    stmt = select(UserSettingsRecord).where(UserSettingsRecord.user_id == user.id)
    if request.workspace_id:
        stmt = stmt.where(UserSettingsRecord.workspace_id == request.workspace_id)
    settings = db.scalar(stmt.order_by(UserSettingsRecord.updated_at.desc()))
    if not settings:
        settings = UserSettingsRecord(user_id=user.id, workspace_id=request.workspace_id)
        db.add(settings)
    settings.profile_json = request.profile
    settings.workspace_json = request.workspace
    settings.notifications_json = request.notifications
    settings.security_json = request.security
    settings.developer_json = request.developer
    settings.admin_json = request.admin
    settings.updated_at = datetime.utcnow()
    db.commit()
    return {"id": settings.id, "saved": True, "updated_at": settings.updated_at.isoformat()}


# ---------- API keys / webhooks ----------
@router.post("/api-keys")
def create_api_key(
    request: APIKeyCreateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _require_workspace_access(db, user, request.workspace_id)
    raw_key = "ck_live_" + secrets.token_urlsafe(28)
    record = APIKeyRecord(
        workspace_id=request.workspace_id,
        name=request.name,
        key_prefix=raw_key[:14],
        key_hash=hash_value(raw_key),
        scopes_json=request.scopes,
        status="active",
    )
    db.add(record)
    db.commit()
    return {"id": record.id, "api_key": raw_key, "key_prefix": record.key_prefix, "scopes": record.scopes_json, "status": record.status}


@router.get("/api-keys")
def list_api_keys(
    workspace_id: Optional[str] = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    stmt = select(APIKeyRecord).order_by(APIKeyRecord.created_at.desc())
    if workspace_id:
        _require_workspace_access(db, user, workspace_id)
        stmt = stmt.where(APIKeyRecord.workspace_id == workspace_id)
    elif user.role != Role.ADMIN.value:
        stmt = stmt.where(APIKeyRecord.workspace_id.in_(_member_workspace_ids(db, user)))
    rows = db.scalars(stmt).all()
    return [{"id": r.id, "name": r.name, "key_prefix": r.key_prefix, "scopes": r.scopes_json, "status": r.status, "created_at": r.created_at.isoformat()} for r in rows]


@router.post("/api-keys/{api_key_id}/rotate")
def rotate_api_key(
    api_key_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    record = db.get(APIKeyRecord, api_key_id)
    if not record:
        raise HTTPException(404, "API key not found")
    _require_workspace_access(db, user, record.workspace_id)
    raw_key = "ck_live_" + secrets.token_urlsafe(28)
    record.key_prefix = raw_key[:14]
    record.key_hash = hash_value(raw_key)
    record.rotated_at = datetime.utcnow()
    db.commit()
    return {"id": record.id, "api_key": raw_key, "rotated": True}


@router.post("/webhooks")
def create_webhook(
    request: WebhookCreateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _require_workspace_access(db, user, request.workspace_id)
    raw_secret = "whsec_" + secrets.token_urlsafe(24)
    hook = WebhookEndpointRecord(
        workspace_id=request.workspace_id,
        url=request.url,
        secret_hash=hash_value(raw_secret),
        events_json=request.events,
        status="active",
    )
    db.add(hook)
    db.commit()
    return {"id": hook.id, "url": hook.url, "secret": raw_secret, "events": hook.events_json, "status": hook.status}


# ---------- Wallets / payment intents / escrow ----------
@router.post("/wallets")
def create_wallet(
    request: WalletCreateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _require_workspace_access(db, user, request.workspace_id)
    existing = db.scalar(select(WalletAccountRecord).where(WalletAccountRecord.address == request.address))
    if existing:
        _require_workspace_access(db, user, existing.workspace_id)
        return {"id": existing.id, "existing": True, "address": existing.address, "status": existing.status}
    wallet = WalletAccountRecord(**request.model_dump())
    db.add(wallet)
    db.commit()
    return {"id": wallet.id, "address": wallet.address, "status": wallet.status, "network": wallet.network}


@router.get("/wallets")
def list_wallets(
    workspace_id: Optional[str] = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    stmt = select(WalletAccountRecord).order_by(WalletAccountRecord.created_at.desc())
    if workspace_id:
        _require_workspace_access(db, user, workspace_id)
        stmt = stmt.where(WalletAccountRecord.workspace_id == workspace_id)
    elif user.role != Role.ADMIN.value:
        stmt = stmt.where(WalletAccountRecord.workspace_id.in_(_member_workspace_ids(db, user)))
    rows = db.scalars(stmt).all()
    return [
        {
            "id": w.id,
            "workspace_id": w.workspace_id,
            "owner_name": w.owner_name,
            "wallet_type": w.wallet_type,
            "address": w.address,
            "network": w.network,
            "stablecoin_asset": w.stablecoin_asset,
            "stablecoin_balance": float(w.stablecoin_balance or 0),
            "gas_balance": float(w.gas_balance or 0),
            "status": w.status,
        }
        for w in rows
    ]


@router.post("/payment-intents")
def create_payment_intent(
    request: PaymentIntentCreateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _require_workspace_access(db, user, request.workspace_id)
    if request.idempotency_key:
        existing = db.scalar(select(PaymentIntentRecord).where(PaymentIntentRecord.idempotency_key == request.idempotency_key))
        if existing:
            return {"id": existing.id, "status": existing.status, "idempotent": True}
    intent = PaymentIntentRecord(
        workspace_id=request.workspace_id,
        intent_type=request.intent_type,
        payer_wallet_id=request.payer_wallet_id,
        payee_reference=request.payee_reference,
        reference_type=request.reference_type,
        reference_id=request.reference_id,
        amount=request.amount,
        asset=request.asset,
        idempotency_key=request.idempotency_key,
        metadata_json=request.metadata,
        status="pending",
    )
    db.add(intent)
    db.flush()
    ledger_entry(
        db,
        workspace_id=intent.workspace_id,
        track="Payment",
        role="system",
        event="payment-intent-created",
        source="Credara API",
        description=f"Payment intent created for {intent.reference_type} {intent.reference_id}",
        amount=float(intent.amount),
        status="pending",
        verifier=None,
        reference_type="payment_intent",
        reference_id=intent.id,
        docs=["Intent"],
    )
    db.commit()
    return {"id": intent.id, "status": intent.status, "amount": float(intent.amount), "asset": intent.asset}


@router.post("/payment-intents/{intent_id}/submit")
def submit_payment_intent(
    intent_id: str,
    request: SubmitTxRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    intent = db.get(PaymentIntentRecord, intent_id)
    if not intent:
        raise HTTPException(404, "Payment intent not found")
    _require_workspace_access(db, user, intent.workspace_id)
    intent.status = "submitted"
    intent.tx_hash = request.tx_hash
    intent.confirmations = request.confirmations
    intent.submitted_at = datetime.utcnow()
    ledger_entry(
        db,
        workspace_id=intent.workspace_id,
        track="Chain",
        role="system",
        event="tx-submitted",
        source="Wallet",
        description=f"Transaction submitted for {intent.intent_type}",
        amount=float(intent.amount),
        status="submitted",
        verifier=intent.tx_hash,
        reference_type="payment_intent",
        reference_id=intent.id,
        docs=["Transaction"],
    )
    db.commit()
    return {"id": intent.id, "status": intent.status, "tx_hash": intent.tx_hash, "confirmations": intent.confirmations}


@router.post("/payment-intents/{intent_id}/confirm")
def confirm_payment_intent(
    intent_id: str,
    request: ConfirmTxRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    intent = db.get(PaymentIntentRecord, intent_id)
    if not intent:
        raise HTTPException(404, "Payment intent not found")
    _require_workspace_access(db, user, intent.workspace_id)
    intent.confirmations = max(intent.confirmations, request.confirmations)
    if intent.confirmations >= intent.required_confirmations:
        intent.status = "confirmed"
        intent.confirmed_at = datetime.utcnow()
    ledger_entry(
        db,
        workspace_id=intent.workspace_id,
        track="Indexer",
        role="system",
        event="tx-confirmed" if intent.status == "confirmed" else "tx-confirmation-updated",
        source="Polygon indexer",
        description=f"{intent.confirmations}/{intent.required_confirmations} confirmations for {intent.intent_type}",
        amount=float(request.on_chain_amount if request.on_chain_amount is not None else intent.amount),
        status=intent.status,
        verifier=intent.tx_hash,
        reference_type="payment_intent",
        reference_id=intent.id,
        docs=["Receipt", "Proof"],
    )
    db.commit()
    return {"id": intent.id, "status": intent.status, "confirmations": intent.confirmations, "required_confirmations": intent.required_confirmations}


@router.get("/payment-intents")
def list_payment_intents(
    workspace_id: Optional[str] = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    stmt = select(PaymentIntentRecord).order_by(PaymentIntentRecord.created_at.desc())
    if workspace_id:
        _require_workspace_access(db, user, workspace_id)
        stmt = stmt.where(PaymentIntentRecord.workspace_id == workspace_id)
    elif user.role != Role.ADMIN.value:
        stmt = stmt.where(PaymentIntentRecord.workspace_id.in_(_member_workspace_ids(db, user)))
    rows = db.scalars(stmt).all()
    return [
        {
            "id": p.id,
            "intent_type": p.intent_type,
            "reference_type": p.reference_type,
            "reference_id": p.reference_id,
            "amount": float(p.amount),
            "asset": p.asset,
            "status": p.status,
            "tx_hash": p.tx_hash,
            "confirmations": p.confirmations,
            "required_confirmations": p.required_confirmations,
            "created_at": p.created_at.isoformat(),
        }
        for p in rows
    ]


@router.post("/escrows")
def create_escrow(
    request: EscrowCreateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _require_workspace_access(db, user, request.workspace_id)
    escrow = EscrowAccountRecord(**request.model_dump(), status="created", funded_amount=0)
    db.add(escrow)
    db.commit()
    return {"id": escrow.id, "smart_lc_id": escrow.smart_lc_id, "status": escrow.status, "required_amount": float(escrow.required_amount)}


@router.post("/escrows/{escrow_id}/fund")
def fund_escrow(
    escrow_id: str,
    request: EscrowFundRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    escrow = db.get(EscrowAccountRecord, escrow_id)
    intent = db.get(PaymentIntentRecord, request.payment_intent_id)
    if not escrow or not intent:
        raise HTTPException(404, "Escrow or payment intent not found")
    _require_workspace_access(db, user, escrow.workspace_id)
    if intent.workspace_id != escrow.workspace_id:
        raise HTTPException(403, "Payment intent does not belong to this escrow's workspace")
    if intent.status != "confirmed":
        raise HTTPException(409, "Payment intent must be confirmed before funding escrow")
    escrow.funded_amount = float(escrow.funded_amount or 0) + float(intent.amount)
    escrow.status = "funded" if float(escrow.funded_amount) >= float(escrow.required_amount) else "partially_funded"
    ledger_entry(
        db,
        workspace_id=escrow.workspace_id,
        track="Escrow",
        role="buyer",
        event="escrow-funded",
        source="Smart LC",
        description=f"Escrow {escrow.smart_lc_id} funded from confirmed payment intent",
        amount=float(intent.amount),
        status="confirmed",
        verifier=intent.tx_hash,
        reference_type="escrow",
        reference_id=escrow.id,
        docs=["Contract", "Receipt", "Proof"],
    )
    db.commit()
    return {"id": escrow.id, "status": escrow.status, "funded_amount": float(escrow.funded_amount), "required_amount": float(escrow.required_amount)}


@router.post("/escrows/{escrow_id}/release")
def release_escrow(
    escrow_id: str,
    request: EscrowReleaseRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    escrow = db.get(EscrowAccountRecord, escrow_id)
    if not escrow:
        raise HTTPException(404, "Escrow not found")
    _require_workspace_access(db, user, escrow.workspace_id)
    if escrow.status != "funded":
        raise HTTPException(409, "Escrow must be funded before release")
    escrow.status = "released"
    escrow.released_at = datetime.utcnow()
    ledger_entry(
        db,
        workspace_id=escrow.workspace_id,
        track="Settlement",
        role="sme",
        event="escrow-released",
        source="Smart LC",
        description=f"Escrow released to seller. Reason: {request.reason}",
        amount=float(escrow.funded_amount),
        status="confirmed",
        verifier=escrow.contract_address,
        reference_type="escrow",
        reference_id=escrow.id,
        docs=["Receipt", "Proof", "Audit"],
    )
    db.commit()
    return {"id": escrow.id, "status": escrow.status, "released_at": escrow.released_at.isoformat()}


@router.get("/escrows")
def list_escrows(
    workspace_id: Optional[str] = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    stmt = select(EscrowAccountRecord).order_by(EscrowAccountRecord.created_at.desc())
    if workspace_id:
        _require_workspace_access(db, user, workspace_id)
        stmt = stmt.where(EscrowAccountRecord.workspace_id == workspace_id)
    elif user.role != Role.ADMIN.value:
        stmt = stmt.where(EscrowAccountRecord.workspace_id.in_(_member_workspace_ids(db, user)))
    rows = db.scalars(stmt).all()
    return [
        {
            "id": e.id,
            "smart_lc_id": e.smart_lc_id,
            "contract_address": e.contract_address,
            "asset": e.asset,
            "required_amount": float(e.required_amount),
            "funded_amount": float(e.funded_amount or 0),
            "funding_party": e.funding_party,
            "seller": e.seller,
            "status": e.status,
            "release_condition": e.release_condition,
            "refund_condition": e.refund_condition,
        }
        for e in rows
    ]


# ---------- Ledger / reconciliation / reporting ----------
@router.get("/ledger")
def settlement_ledger(
    role: Optional[str] = None,
    status: Optional[str] = None,
    reference_id: Optional[str] = None,
    workspace_id: Optional[str] = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    stmt = select(SettlementLedgerRecord).order_by(SettlementLedgerRecord.created_at.desc())
    if workspace_id:
        _require_workspace_access(db, user, workspace_id)
        stmt = stmt.where(SettlementLedgerRecord.workspace_id == workspace_id)
    elif user.role != Role.ADMIN.value:
        stmt = stmt.where(SettlementLedgerRecord.workspace_id.in_(_member_workspace_ids(db, user)))
    if role:
        stmt = stmt.where(SettlementLedgerRecord.role == role)
    if status:
        stmt = stmt.where(SettlementLedgerRecord.status == status)
    if reference_id:
        stmt = stmt.where(SettlementLedgerRecord.reference_id == reference_id)
    return [serialize_ledger(r) for r in db.scalars(stmt).all()]


@router.get("/ledger/summary")
def ledger_summary(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    stmt = select(SettlementLedgerRecord)
    if user.role != Role.ADMIN.value:
        stmt = stmt.where(SettlementLedgerRecord.workspace_id.in_(_member_workspace_ids(db, user)))
    rows = db.scalars(stmt).all()
    return {
        "rows": len(rows),
        "confirmed": len([r for r in rows if r.status == "confirmed"]),
        "pending": len([r for r in rows if r.status in ("pending", "submitted")]),
        "fallback": len([r for r in rows if r.status == "fallback"]),
        "spend": sum(float(r.amount or 0) for r in rows),
    }


@router.get("/reports/role/{role}")
def role_report(role: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    # Cross-workspace aggregate by role - platform-wide view, admin only.
    _require_admin(user)
    rows = db.scalars(select(SettlementLedgerRecord).where(SettlementLedgerRecord.role == role)).all()
    return {"role": role, "summary": {"rows": len(rows), "spend": sum(float(r.amount or 0) for r in rows)}, "rows": [serialize_ledger(r) for r in rows]}


@router.get("/reports/admin/aggregate")
def admin_aggregate_report(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    _require_admin(user)
    rows = db.scalars(select(SettlementLedgerRecord)).all()
    by_role: Dict[str, Dict[str, Any]] = {}
    for r in rows:
        bucket = by_role.setdefault(r.role, {"rows": 0, "spend": 0.0, "confirmed": 0, "pending": 0})
        bucket["rows"] += 1
        bucket["spend"] += float(r.amount or 0)
        if r.status == "confirmed":
            bucket["confirmed"] += 1
        if r.status in ("pending", "submitted"):
            bucket["pending"] += 1
    return {"summary": ledger_summary(db, user), "by_role": by_role, "rows": [serialize_ledger(r) for r in rows]}


@router.post("/reconciliation/{reference_type}/{reference_id}")
def reconcile(
    reference_type: str,
    reference_id: str,
    expected_amount: float = Query(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # Workspace members can reconcile their own settlement references.
    if user.role not in {
        Role.ADMIN.value,
        Role.FINANCIER.value,
        Role.SME.value,
        Role.BUYER.value,
    }:
        raise HTTPException(403, "Insufficient permissions")
    ledger_rows = db.scalars(select(SettlementLedgerRecord).where(SettlementLedgerRecord.reference_id == reference_id)).all()
    confirmed_rows = [r for r in ledger_rows if r.status == "confirmed"]
    internal_amount = sum(float(r.amount or 0) for r in confirmed_rows)
    on_chain_amount = internal_amount
    variance = round(float(expected_amount) - float(on_chain_amount), 2)
    decision = "valid" if variance == 0 else "manual_review"
    smart_lc_state = "funded" if internal_amount >= expected_amount else "partial_or_pending"
    rec = ReconciliationRecord(
        reference_type=reference_type,
        reference_id=reference_id,
        expected_amount=expected_amount,
        on_chain_amount=on_chain_amount,
        internal_ledger_amount=internal_amount,
        smart_lc_state=smart_lc_state,
        variance=variance,
        decision=decision,
    )
    db.add(rec)
    db.commit()
    return {
        "id": rec.id,
        "reference_type": rec.reference_type,
        "reference_id": rec.reference_id,
        "expected_amount": float(rec.expected_amount),
        "on_chain_amount": float(rec.on_chain_amount),
        "internal_ledger_amount": float(rec.internal_ledger_amount),
        "smart_lc_state": rec.smart_lc_state,
        "variance": float(rec.variance),
        "decision": rec.decision,
        "checked_at": rec.checked_at.isoformat(),
    }


@router.get("/health")
def real_workflow_health(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return {
        "status": "ok",
        "persistent_tables": [
            "workspaces", "memberships", "invitations_real", "user_settings",
            "api_keys_real", "webhook_endpoints_real", "wallet_accounts_real",
            "payment_intents_real", "escrow_accounts_real", "settlement_ledger_real",
            "reconciliation_records_real",
        ],
        "ledger_rows": db.scalar(select(func.count(SettlementLedgerRecord.id))) or 0,
    }
