
from datetime import datetime
from uuid import uuid4
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class Workspace(Base):
    __tablename__ = "workspaces"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    business_id: Mapped[str] = mapped_column(ForeignKey("businesses.id"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    primary_role: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    environment: Mapped[str] = mapped_column(String(80), default="sandbox")
    region: Mapped[str | None] = mapped_column(String(80))
    status: Mapped[str] = mapped_column(String(50), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Membership(Base):
    __tablename__ = "memberships"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id"), index=True, nullable=False)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    role: Mapped[str] = mapped_column(String(80), index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="active")
    permissions_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class OnboardingProgressRecord(Base):
    __tablename__ = "onboarding_progress"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id"), index=True, nullable=False)
    account_created: Mapped[bool] = mapped_column(Boolean, default=False)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    role_selected: Mapped[bool] = mapped_column(Boolean, default=False)
    business_profile_created: Mapped[bool] = mapped_column(Boolean, default=False)
    kyb_status: Mapped[str] = mapped_column(String(50), default="not_started")
    wallet_status: Mapped[str] = mapped_column(String(50), default="not_connected")
    first_workflow: Mapped[str | None] = mapped_column(String(255))
    percent_complete: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class InvitationRecord(Base):
    __tablename__ = "invitations_real"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    token: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    from_workspace_id: Mapped[str | None] = mapped_column(ForeignKey("workspaces.id"), index=True)
    from_business_name: Mapped[str] = mapped_column(String(255), nullable=False)
    to_email: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    invite_type: Mapped[str] = mapped_column(String(80), nullable=False)
    invited_role: Mapped[str] = mapped_column(String(80), nullable=False)
    target_type: Mapped[str] = mapped_column(String(80), nullable=False)
    target_id: Mapped[str] = mapped_column(String(120), index=True, nullable=False)
    target_route: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="pending", index=True)
    message: Mapped[str | None] = mapped_column(Text)
    accepted_by_user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"))
    decision_reason: Mapped[str | None] = mapped_column(Text)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime)


class UserSettingsRecord(Base):
    __tablename__ = "user_settings"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), index=True)
    workspace_id: Mapped[str | None] = mapped_column(ForeignKey("workspaces.id"), index=True)
    profile_json: Mapped[dict] = mapped_column(JSON, default=dict)
    workspace_json: Mapped[dict] = mapped_column(JSON, default=dict)
    notifications_json: Mapped[dict] = mapped_column(JSON, default=dict)
    security_json: Mapped[dict] = mapped_column(JSON, default=dict)
    developer_json: Mapped[dict] = mapped_column(JSON, default=dict)
    admin_json: Mapped[dict] = mapped_column(JSON, default=dict)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class APIKeyRecord(Base):
    __tablename__ = "api_keys_real"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    workspace_id: Mapped[str | None] = mapped_column(ForeignKey("workspaces.id"), index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    key_prefix: Mapped[str] = mapped_column(String(30), index=True, nullable=False)
    key_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    scopes_json: Mapped[list] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String(50), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    rotated_at: Mapped[datetime | None] = mapped_column(DateTime)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime)


class WebhookEndpointRecord(Base):
    __tablename__ = "webhook_endpoints_real"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    workspace_id: Mapped[str | None] = mapped_column(ForeignKey("workspaces.id"), index=True)
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    secret_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    events_json: Mapped[list] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String(50), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class WalletAccountRecord(Base):
    __tablename__ = "wallet_accounts_real"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    workspace_id: Mapped[str | None] = mapped_column(ForeignKey("workspaces.id"), index=True)
    business_id: Mapped[str | None] = mapped_column(ForeignKey("businesses.id"), index=True)
    owner_name: Mapped[str] = mapped_column(String(255), nullable=False)
    wallet_type: Mapped[str] = mapped_column(String(50), default="connected")
    address: Mapped[str] = mapped_column(String(120), index=True, nullable=False)
    network: Mapped[str] = mapped_column(String(80), default="Polygon Amoy")
    stablecoin_asset: Mapped[str] = mapped_column(String(40), default="MockUSDC")
    stablecoin_balance: Mapped[float] = mapped_column(Numeric(18, 2), default=0)
    gas_asset: Mapped[str] = mapped_column(String(40), default="POL")
    gas_balance: Mapped[float] = mapped_column(Numeric(18, 6), default=0)
    status: Mapped[str] = mapped_column(String(50), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class PaymentIntentRecord(Base):
    __tablename__ = "payment_intents_real"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    workspace_id: Mapped[str | None] = mapped_column(ForeignKey("workspaces.id"), index=True)
    intent_type: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    payer_wallet_id: Mapped[str | None] = mapped_column(ForeignKey("wallet_accounts_real.id"), index=True)
    payee_reference: Mapped[str] = mapped_column(String(255), nullable=False)
    reference_type: Mapped[str] = mapped_column(String(80), nullable=False)
    reference_id: Mapped[str] = mapped_column(String(120), index=True, nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    asset: Mapped[str] = mapped_column(String(40), default="MockUSDC")
    network: Mapped[str] = mapped_column(String(80), default="Polygon Amoy")
    status: Mapped[str] = mapped_column(String(50), default="pending", index=True)
    tx_hash: Mapped[str | None] = mapped_column(String(120), index=True)
    confirmations: Mapped[int] = mapped_column(Integer, default=0)
    required_confirmations: Mapped[int] = mapped_column(Integer, default=3)
    idempotency_key: Mapped[str | None] = mapped_column(String(255), index=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime)
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime)


class EscrowAccountRecord(Base):
    __tablename__ = "escrow_accounts_real"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    workspace_id: Mapped[str | None] = mapped_column(ForeignKey("workspaces.id"), index=True)
    smart_lc_id: Mapped[str] = mapped_column(String(120), index=True, nullable=False)
    contract_address: Mapped[str | None] = mapped_column(String(120), index=True)
    asset: Mapped[str] = mapped_column(String(40), default="MockUSDC")
    required_amount: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    funded_amount: Mapped[float] = mapped_column(Numeric(18, 2), default=0)
    funding_party: Mapped[str] = mapped_column(String(255), nullable=False)
    seller: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="created", index=True)
    release_condition: Mapped[str] = mapped_column(Text)
    refund_condition: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    released_at: Mapped[datetime | None] = mapped_column(DateTime)
    refunded_at: Mapped[datetime | None] = mapped_column(DateTime)


class SettlementLedgerRecord(Base):
    __tablename__ = "settlement_ledger_real"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    workspace_id: Mapped[str | None] = mapped_column(ForeignKey("workspaces.id"), index=True)
    track: Mapped[str] = mapped_column(String(80), index=True, nullable=False)
    role: Mapped[str] = mapped_column(String(80), index=True, nullable=False)
    event: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    source: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(18, 2), default=0)
    asset: Mapped[str] = mapped_column(String(40), default="MockUSDC")
    status: Mapped[str] = mapped_column(String(50), default="pending", index=True)
    verifier: Mapped[str | None] = mapped_column(String(255))
    reference_type: Mapped[str] = mapped_column(String(80), index=True)
    reference_id: Mapped[str] = mapped_column(String(120), index=True)
    docs_json: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ReconciliationRecord(Base):
    __tablename__ = "reconciliation_records_real"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    reference_type: Mapped[str] = mapped_column(String(80), index=True, nullable=False)
    reference_id: Mapped[str] = mapped_column(String(120), index=True, nullable=False)
    expected_amount: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    on_chain_amount: Mapped[float] = mapped_column(Numeric(18, 2), default=0)
    internal_ledger_amount: Mapped[float] = mapped_column(Numeric(18, 2), default=0)
    smart_lc_state: Mapped[str] = mapped_column(String(50), default="unknown")
    variance: Mapped[float] = mapped_column(Numeric(18, 2), default=0)
    decision: Mapped[str] = mapped_column(String(50), default="manual_review")
    checked_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
