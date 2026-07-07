"""
Credara v10 Settings and Role-Based Navigation Access.

This router supports:
- role-filtered workspace navigation
- user profile settings
- workspace settings
- notifications/security settings
- developer API/webhook settings under user profile/settings
- admin preferences
"""
from __future__ import annotations

from typing import Dict, List, Literal, Optional
from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(prefix="/settings", tags=["settings-access"])

Role = Literal["sme", "buyer", "financier", "admin", "developer"]


class NavItem(BaseModel):
    page: str
    label: str
    group: str


class RoleNavigation(BaseModel):
    role: Role
    groups: Dict[str, List[NavItem]]
    allowed_pages: List[str]


class ProfileSettings(BaseModel):
    name: str
    email: str
    language: str = "English"
    timezone: str = "UTC +0"


class WorkspaceSettings(BaseModel):
    workspace_name: str
    role: Role
    environment: str = "Demo · Polygon Amoy"
    region: str = "UAE / UK"
    primary_network: str = "Polygon Amoy"
    settlement_asset: str = "MockUSDC"


class NotificationSettings(BaseModel):
    payment: bool = True
    proof: bool = True
    kyb: bool = True
    invites: bool = True


class SecuritySettings(BaseModel):
    mfa: bool = True
    sso: bool = False
    session_timeout: str = "30 minutes"
    role_filtering: bool = True


class DeveloperSettings(BaseModel):
    api_key: str = "ck_sandbox_••••_8f31"
    webhook_endpoint: str = "https://api.acme.example/credara/webhooks"
    mode: str = "Sandbox"
    subscribed_events: List[str] = Field(default_factory=lambda: ["proof.anchored", "receivable.created", "payment.confirmed"])


class AdminPreferences(BaseModel):
    risk_rules_enabled: bool = True
    override_reason_required: bool = True
    audit_export_enabled: bool = True
    fallback_receipts_manual_review: bool = True


class UserSettings(BaseModel):
    profile: ProfileSettings
    workspace: WorkspaceSettings
    notifications: NotificationSettings
    security: SecuritySettings
    developer: Optional[DeveloperSettings] = None
    admin: Optional[AdminPreferences] = None


NAV_GROUPS = {
    "Operate": [
        NavItem(page="dashboard", label="Dashboard", group="Operate"),
        NavItem(page="contractDetail", label="Contracts", group="Operate"),
        NavItem(page="invoiceDetail", label="Invoices", group="Operate"),
        NavItem(page="delivery", label="Delivery", group="Operate"),
        NavItem(page="receivables", label="Receivables", group="Operate"),
    ],
    "Network": [
        NavItem(page="directory", label="Directory", group="Network"),
        NavItem(page="opportunities", label="Opportunities", group="Network"),
        NavItem(page="proposals", label="Proposals", group="Network"),
        NavItem(page="marketplace", label="Deals", group="Network"),
    ],
    "Settlement": [
        NavItem(page="wallets", label="Wallets", group="Settlement"),
        NavItem(page="settlement", label="Smart LC", group="Settlement"),
        NavItem(page="settlementLedger", label="Settlement Ledger", group="Settlement"),
        NavItem(page="reconciliation", label="Reconciliation", group="Settlement"),
        NavItem(page="repayments", label="Repayments", group="Settlement"),
    ],
    "Trust": [
        NavItem(page="proof", label="Proof Ledger", group="Trust"),
        NavItem(page="evidence", label="Evidence", group="Trust"),
        NavItem(page="credit", label="Credit", group="Trust"),
        NavItem(page="kyb", label="KYB", group="Trust"),
        NavItem(page="riskRules", label="Risk Rules", group="Trust"),
    ],
    "Setup": [
        NavItem(page="onboarding", label="Onboarding", group="Setup"),
        NavItem(page="businessProfile", label="Business Profile", group="Setup"),
        NavItem(page="invitations", label="Invitations", group="Setup"),
        NavItem(page="members", label="Members", group="Setup"),
    ],
    "Platform": [
        NavItem(page="settings", label="Settings", group="Platform"),
        NavItem(page="admin", label="Risk Ops", group="Platform"),
        NavItem(page="launch", label="Launch", group="Platform"),
    ],
}

ROLE_ALLOWED = {
    "sme": ["dashboard","contractDetail","invoiceDetail","delivery","receivables","directory","opportunities","proposals","marketplace","wallets","settlement","settlementLedger","reconciliation","repayments","proof","evidence","credit","kyb","onboarding","businessProfile","invitations","members","settings"],
    "buyer": ["dashboard","contractDetail","invoiceDetail","delivery","directory","opportunities","wallets","settlement","settlementLedger","reconciliation","repayments","proof","evidence","credit","kyb","onboarding","businessProfile","invitations","members","settings"],
    "financier": ["dashboard","marketplace","receivables","evidence","credit","kyb","wallets","settlementLedger","reconciliation","repayments","proof","directory","onboarding","businessProfile","invitations","members","settings"],
    "admin": ["dashboard","admin","riskRules","kyb","proof","evidence","settlementLedger","reconciliation","wallets","onboarding","businessProfile","invitations","members","settings","launch"],
    "developer": ["dashboard","settings","onboarding","businessProfile","members","proof","wallets","settlementLedger"],
}


def filter_groups(role: Role) -> Dict[str, List[NavItem]]:
    allowed = set(ROLE_ALLOWED[role])
    return {group: [item for item in items if item.page in allowed] for group, items in NAV_GROUPS.items() if any(item.page in allowed for item in items)}


@router.get("/navigation/{role}", response_model=RoleNavigation)
def navigation_for_role(role: Role) -> RoleNavigation:
    return RoleNavigation(role=role, groups=filter_groups(role), allowed_pages=ROLE_ALLOWED[role])


@router.get("/me/{role}", response_model=UserSettings)
def get_settings(role: Role) -> UserSettings:
    developer = DeveloperSettings() if role in ("developer", "admin") else None
    admin = AdminPreferences() if role == "admin" else None
    names = {
        "sme": ("Amara Okafor", "amara@acme.example", "Acme Textiles Ltd"),
        "buyer": ("Daniel Reed", "daniel@globalretail.example", "Global Retail Ltd"),
        "financier": ("Maya Chen", "maya@credaracapital.example", "Credara Capital"),
        "admin": ("Ravi Singh", "ravi@credara.example", "Credara Risk"),
        "developer": ("Dev User", "dev@credara.example", "Credara Dev Team"),
    }
    name, email, workspace = names[role]
    return UserSettings(
        profile=ProfileSettings(name=name, email=email),
        workspace=WorkspaceSettings(workspace_name=workspace, role=role),
        notifications=NotificationSettings(),
        security=SecuritySettings(),
        developer=developer,
        admin=admin,
    )


@router.put("/me/{role}", response_model=UserSettings)
def update_settings(role: Role, settings: UserSettings) -> UserSettings:
    return settings


@router.get("/settings-tabs/{role}")
def settings_tabs(role: Role) -> Dict[str, List[str]]:
    base = ["profile", "workspace", "notifications", "security", "billing"]
    if role in ("developer", "admin"):
        base.append("developer")
    if role == "admin":
        base.append("admin")
    return {"role": role, "tabs": base}


@router.get("/api-access/{role}")
def api_access(role: Role) -> Dict[str, object]:
    return {
        "role": role,
        "api_settings_location": "Settings > API & Webhooks",
        "api_visible_in_main_nav": False,
        "enabled": role in ("developer", "admin"),
        "reason": "API and webhook controls are platform settings, not core trade workflow pages.",
    }
