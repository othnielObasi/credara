"""
Credara v9 Onboarding and Invitation Flows.

This module makes onboarding first-class:
- self-signup business setup
- invitation onboarding
- business profile
- KYB setup state
- wallet setup state
- workspace members
- role routing
"""
from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Literal, Optional
from fastapi import APIRouter
from pydantic import BaseModel, EmailStr, Field

router = APIRouter(prefix="/onboarding", tags=["onboarding"])


Role = Literal["sme", "buyer", "financier", "admin", "developer", "logistics", "auditor"]
InviteStatus = Literal["pending", "accepted", "rejected", "expired"]


class BusinessProfile(BaseModel):
    business_id: str
    legal_name: str
    registration_number: str
    country: str
    sector: str
    website: Optional[str] = None
    address: Optional[str] = None
    primary_role: Role
    expected_monthly_volume: Optional[str] = None
    kyb_status: str = "pending_review"
    wallet_status: str = "not_connected"


class OnboardingProgress(BaseModel):
    business_id: str
    percent: int
    account_created: bool
    email_verified: bool
    role_selected: bool
    business_profile_created: bool
    kyb_status: str
    wallet_status: str
    first_workflow: Optional[str]


class Invitation(BaseModel):
    invitation_id: str
    invite_type: str
    from_business: str
    to_email: EmailStr
    target_id: str
    target_route: str
    invited_role: Role
    status: InviteStatus
    message: str
    created_at: str


class InvitationDecision(BaseModel):
    decision: Literal["accept", "reject"]
    reason: Optional[str] = None


class Member(BaseModel):
    member_id: str
    name: str
    email: EmailStr
    role: str
    status: str


class CreateBusinessProfileRequest(BaseModel):
    legal_name: str
    registration_number: str
    country: str
    sector: str
    primary_role: Role
    website: Optional[str] = None
    address: Optional[str] = None
    expected_monthly_volume: Optional[str] = None


class CreateInvitationRequest(BaseModel):
    invite_type: str
    to_email: EmailStr
    target_id: str
    target_route: str
    invited_role: Role
    message: str


def demo_profile() -> BusinessProfile:
    return BusinessProfile(
        business_id="biz_seller_acme_textiles",
        legal_name="Acme Textiles Ltd",
        registration_number="AE-TRD-2026-0012",
        country="United Arab Emirates / United Kingdom",
        sector="Textiles and trade finance",
        website="https://acme.example",
        address="Jebel Ali Free Zone, Dubai",
        primary_role="sme",
        expected_monthly_volume="GBP 50k - 250k",
        kyb_status="pending_review",
        wallet_status="connected",
    )


def demo_invitations() -> List[Invitation]:
    return [
        Invitation(invitation_id="INVITE-001", invite_type="Trade Contract", from_business="Global Retail Ltd", to_email="amara@acme.example", target_id="TC-2026-0012", target_route="/contracts/TC-2026-0012", invited_role="sme", status="pending", message="Review and accept trade contract.", created_at="2026-06-04T09:00:00Z"),
        Invitation(invitation_id="INVITE-002", invite_type="Invoice Confirmation", from_business="Acme Textiles Ltd", to_email="daniel@globalretail.example", target_id="INV-2025-045", target_route="/invoices/INV-2025-045", invited_role="buyer", status="accepted", message="Confirm buyer obligation for invoice.", created_at="2026-06-04T09:05:00Z"),
        Invitation(invitation_id="INVITE-003", invite_type="Funding Review", from_business="Acme Textiles Ltd", to_email="maya@credaracapital.example", target_id="REC-045", target_route="/deal-room/REC-045", invited_role="financier", status="pending", message="Review evidence bundle and make funding offer.", created_at="2026-06-04T09:10:00Z"),
    ]


@router.get("/progress", response_model=OnboardingProgress)
def get_progress() -> OnboardingProgress:
    return OnboardingProgress(
        business_id="biz_seller_acme_textiles",
        percent=72,
        account_created=True,
        email_verified=True,
        role_selected=True,
        business_profile_created=True,
        kyb_status="pending_review",
        wallet_status="connected",
        first_workflow="Contract invite accepted",
    )


@router.get("/business-profile", response_model=BusinessProfile)
def get_business_profile() -> BusinessProfile:
    return demo_profile()


@router.post("/business-profile", response_model=BusinessProfile)
def create_business_profile(request: CreateBusinessProfileRequest) -> BusinessProfile:
    return BusinessProfile(
        business_id=f"biz_{request.legal_name.lower().replace(' ', '_')[:24]}",
        legal_name=request.legal_name,
        registration_number=request.registration_number,
        country=request.country,
        sector=request.sector,
        website=request.website,
        address=request.address,
        primary_role=request.primary_role,
        expected_monthly_volume=request.expected_monthly_volume,
        kyb_status="not_submitted",
        wallet_status="not_connected",
    )


@router.get("/role-routing")
def role_routing() -> Dict[str, Dict[str, str]]:
    return {
        "sme": {"first_success": "Invoice is buyer-confirmed and receivable-ready", "route": "/invoiceDetail"},
        "buyer": {"first_success": "Contract accepted or escrow funded", "route": "/contractDetail"},
        "financier": {"first_success": "First receivable offer made", "route": "/dealRoom"},
        "developer": {"first_success": "Sandbox webhook received", "route": "/apiExplorer"},
        "admin": {"first_success": "Risk or KYB exception resolved", "route": "/admin"},
        "logistics": {"first_success": "Delivery proof verified", "route": "/logistics"},
    }


@router.get("/invitations", response_model=List[Invitation])
def list_invitations() -> List[Invitation]:
    return demo_invitations()


@router.post("/invitations", response_model=Invitation)
def create_invitation(request: CreateInvitationRequest) -> Invitation:
    return Invitation(
        invitation_id=f"INVITE-{int(datetime.utcnow().timestamp())}",
        invite_type=request.invite_type,
        from_business="Current Workspace",
        to_email=request.to_email,
        target_id=request.target_id,
        target_route=request.target_route,
        invited_role=request.invited_role,
        status="pending",
        message=request.message,
        created_at=datetime.utcnow().isoformat() + "Z",
    )


@router.get("/invitations/{invitation_id}", response_model=Invitation)
def get_invitation(invitation_id: str) -> Invitation:
    invite = demo_invitations()[0]
    invite.invitation_id = invitation_id
    return invite


@router.post("/invitations/{invitation_id}/decision", response_model=Invitation)
def decide_invitation(invitation_id: str, request: InvitationDecision) -> Invitation:
    invite = demo_invitations()[0]
    invite.invitation_id = invitation_id
    invite.status = "accepted" if request.decision == "accept" else "rejected"
    return invite


@router.get("/members", response_model=List[Member])
def members() -> List[Member]:
    return [
        Member(member_id="MEM-001", name="Amara Okafor", email="amara@acme.example", role="SME Admin", status="active"),
        Member(member_id="MEM-002", name="Daniel Reed", email="daniel@globalretail.example", role="Buyer Ops", status="invited"),
        Member(member_id="MEM-003", name="Maya Chen", email="maya@credaracapital.example", role="Underwriter", status="active"),
    ]


@router.get("/setup-checklist")
def setup_checklist() -> Dict[str, List[str]]:
    return {
        "identity": ["Create account", "Verify email", "Enable MFA"],
        "business": ["Create profile", "Submit KYB", "Assign role"],
        "settlement": ["Choose wallet mode", "Connect wallet", "Select settlement asset"],
        "first_workflow": ["Accept invite or create contract", "Create invoice", "Verify proof"],
    }
