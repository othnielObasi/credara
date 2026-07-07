from datetime import datetime
from uuid import uuid4
from sqlalchemy import DateTime, ForeignKey, Integer, JSON, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class BuyerAction(Base):
    """Buyer-side inbox task for invoice confirmation, delivery confirmation and settlement decisions."""
    __tablename__ = 'buyer_actions'

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    buyer_user_id: Mapped[str | None] = mapped_column(ForeignKey('users.id'), index=True)
    buyer_business_id: Mapped[str | None] = mapped_column(ForeignKey('businesses.id'), index=True)
    seller_business_id: Mapped[str | None] = mapped_column(ForeignKey('businesses.id'), index=True)
    order_id: Mapped[str | None] = mapped_column(ForeignKey('orders.id'), index=True)
    invoice_id: Mapped[str | None] = mapped_column(ForeignKey('invoices.id'), index=True)
    smart_lc_id: Mapped[str | None] = mapped_column(ForeignKey('smart_lcs.id'), index=True)
    action_type: Mapped[str] = mapped_column(String(80), index=True)
    priority: Mapped[str] = mapped_column(String(30), default='medium')
    status: Mapped[str] = mapped_column(String(50), default='open', index=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    due_at: Mapped[datetime | None] = mapped_column(DateTime)
    decision_reason: Mapped[str | None] = mapped_column(Text)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class LogisticsVerification(Base):
    """Delivery evidence from logistics partners or manual operations."""
    __tablename__ = 'logistics_verifications'

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    order_id: Mapped[str] = mapped_column(ForeignKey('orders.id'), index=True)
    invoice_id: Mapped[str | None] = mapped_column(ForeignKey('invoices.id'), index=True)
    provider: Mapped[str] = mapped_column(String(120), default='mock')
    carrier_name: Mapped[str | None] = mapped_column(String(255))
    tracking_reference: Mapped[str | None] = mapped_column(String(255), index=True)
    delivery_status: Mapped[str] = mapped_column(String(80), default='pending', index=True)
    gps_match_status: Mapped[str] = mapped_column(String(80), default='unknown')
    timestamp_status: Mapped[str] = mapped_column(String(80), default='unknown')
    handover_status: Mapped[str] = mapped_column(String(80), default='unknown')
    evidence_uri: Mapped[str | None] = mapped_column(String(500))
    confidence_score: Mapped[int] = mapped_column(Integer, default=0)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class EvidenceBundle(Base):
    """Exportable underwriting/compliance package linking invoice, proof, KYB, tx and score evidence."""
    __tablename__ = 'evidence_bundles'

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    business_id: Mapped[str] = mapped_column(ForeignKey('businesses.id'), index=True)
    invoice_id: Mapped[str | None] = mapped_column(ForeignKey('invoices.id'), index=True)
    receivable_id: Mapped[str | None] = mapped_column(ForeignKey('receivables.id'), index=True)
    smart_lc_id: Mapped[str | None] = mapped_column(ForeignKey('smart_lcs.id'), index=True)
    bundle_type: Mapped[str] = mapped_column(String(80), default='underwriting')
    status: Mapped[str] = mapped_column(String(50), default='generated', index=True)
    completeness_score: Mapped[int] = mapped_column(Integer, default=0)
    secure_share_token: Mapped[str | None] = mapped_column(String(255), unique=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime)
    payload_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_by_user_id: Mapped[str | None] = mapped_column(ForeignKey('users.id'))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class EvidenceBundleItem(Base):
    __tablename__ = 'evidence_bundle_items'

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    bundle_id: Mapped[str] = mapped_column(ForeignKey('evidence_bundles.id'), index=True)
    item_type: Mapped[str] = mapped_column(String(80), index=True)
    title: Mapped[str] = mapped_column(String(255))
    source: Mapped[str] = mapped_column(String(120))
    status: Mapped[str] = mapped_column(String(50), default='included')
    resource_type: Mapped[str | None] = mapped_column(String(120))
    resource_id: Mapped[str | None] = mapped_column(String, index=True)
    proof_hash: Mapped[str | None] = mapped_column(String(80))
    polygon_tx_hash: Mapped[str | None] = mapped_column(String(120))
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class RepaymentScheduleItem(Base):
    __tablename__ = 'repayment_schedule_items'

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    receivable_id: Mapped[str] = mapped_column(ForeignKey('receivables.id'), index=True)
    smart_lc_id: Mapped[str | None] = mapped_column(ForeignKey('smart_lcs.id'), index=True)
    payer_name: Mapped[str] = mapped_column(String(255))
    payee_name: Mapped[str] = mapped_column(String(255))
    event_type: Mapped[str] = mapped_column(String(80), index=True)
    due_at: Mapped[datetime]
    amount: Mapped[float] = mapped_column(Numeric(18, 2))
    currency: Mapped[str] = mapped_column(String(10), default='USDC')
    status: Mapped[str] = mapped_column(String(50), default='scheduled', index=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class RiskRule(Base):
    __tablename__ = 'risk_rules'

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    name: Mapped[str] = mapped_column(String(255))
    scope: Mapped[str] = mapped_column(String(80), index=True)
    severity: Mapped[str] = mapped_column(String(40), default='medium')
    condition_json: Mapped[dict] = mapped_column(JSON, default=dict)
    action: Mapped[str] = mapped_column(String(120), default='manual_review')
    is_enabled: Mapped[bool] = mapped_column(default=True)
    created_by_user_id: Mapped[str | None] = mapped_column(ForeignKey('users.id'))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ApiKey(Base):
    __tablename__ = 'api_keys'
    __table_args__ = (UniqueConstraint('key_prefix', name='uq_api_key_prefix'),)

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    owner_user_id: Mapped[str] = mapped_column(ForeignKey('users.id'), index=True)
    name: Mapped[str] = mapped_column(String(120))
    key_prefix: Mapped[str] = mapped_column(String(32), index=True)
    key_hash: Mapped[str] = mapped_column(String(80))
    scopes_json: Mapped[list] = mapped_column(JSON, default=list)
    environment: Mapped[str] = mapped_column(String(40), default='sandbox')
    status: Mapped[str] = mapped_column(String(40), default='active', index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime)


class WebhookEndpoint(Base):
    __tablename__ = 'webhook_endpoints'

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    owner_user_id: Mapped[str] = mapped_column(ForeignKey('users.id'), index=True)
    url: Mapped[str] = mapped_column(String(500))
    events_json: Mapped[list] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String(40), default='active')
    signing_secret_hash: Mapped[str | None] = mapped_column(String(80))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class WebhookDelivery(Base):
    __tablename__ = 'webhook_deliveries'

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    endpoint_id: Mapped[str | None] = mapped_column(ForeignKey('webhook_endpoints.id'), index=True)
    event_type: Mapped[str] = mapped_column(String(120), index=True)
    payload_json: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(50), default='pending', index=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    last_error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime)


class ApiUsageLog(Base):
    __tablename__ = 'api_usage_logs'

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    api_key_id: Mapped[str | None] = mapped_column(ForeignKey('api_keys.id'), index=True)
    user_id: Mapped[str | None] = mapped_column(ForeignKey('users.id'), index=True)
    endpoint: Mapped[str] = mapped_column(String(255), index=True)
    method: Mapped[str] = mapped_column(String(12))
    status_code: Mapped[int] = mapped_column(Integer, default=200)
    latency_ms: Mapped[int] = mapped_column(Integer, default=0)
    request_json: Mapped[dict] = mapped_column(JSON, default=dict)
    response_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)



class BusinessDirectoryProfile(Base):
    """Discoverable verified business profile for the Credara trade finance network."""
    __tablename__ = 'business_directory_profiles'

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    business_id: Mapped[str] = mapped_column(ForeignKey('businesses.id'), nullable=False, index=True, unique=True)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role_type: Mapped[str] = mapped_column(String(40), index=True)  # buyer, seller, financier, logistics
    headline: Mapped[str | None] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    sectors_json: Mapped[list] = mapped_column(JSON, default=list)
    countries_json: Mapped[list] = mapped_column(JSON, default=list)
    capabilities_json: Mapped[list] = mapped_column(JSON, default=list)
    preferred_currencies_json: Mapped[list] = mapped_column(JSON, default=list)
    contact_email: Mapped[str | None] = mapped_column(String(255))
    visibility: Mapped[str] = mapped_column(String(40), default='private', index=True)  # private, network, public
    discovery_status: Mapped[str] = mapped_column(String(40), default='draft', index=True)  # draft, listed, suspended
    trust_score_snapshot: Mapped[int] = mapped_column(Integer, default=0)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class CounterpartyRelationship(Base):
    """Invite/relationship graph between buyers, sellers, financiers and providers."""
    __tablename__ = 'counterparty_relationships'

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    requester_business_id: Mapped[str | None] = mapped_column(ForeignKey('businesses.id'), index=True)
    counterparty_business_id: Mapped[str | None] = mapped_column(ForeignKey('businesses.id'), index=True)
    created_by_user_id: Mapped[str | None] = mapped_column(ForeignKey('users.id'), index=True)
    relationship_type: Mapped[str] = mapped_column(String(60), index=True)  # buyer_seller, financier_sme, logistics_partner
    status: Mapped[str] = mapped_column(String(40), default='invited', index=True)  # invited, accepted, rejected, blocked
    invited_email: Mapped[str | None] = mapped_column(String(255), index=True)
    invited_business_name: Mapped[str | None] = mapped_column(String(255))
    invite_token: Mapped[str | None] = mapped_column(String(255), unique=True, index=True)
    invitation_message: Mapped[str | None] = mapped_column(Text)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class TradeOpportunity(Base):
    """Buyer-posted request that verified sellers can discover and propose against."""
    __tablename__ = 'trade_opportunities'

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    buyer_business_id: Mapped[str | None] = mapped_column(ForeignKey('businesses.id'), index=True)
    created_by_user_id: Mapped[str | None] = mapped_column(ForeignKey('users.id'), index=True)
    title: Mapped[str] = mapped_column(String(255), index=True)
    description: Mapped[str] = mapped_column(Text)
    sector: Mapped[str | None] = mapped_column(String(120), index=True)
    country: Mapped[str | None] = mapped_column(String(2), index=True)
    delivery_location: Mapped[str | None] = mapped_column(String(255))
    amount_min: Mapped[float | None] = mapped_column(Numeric(18, 2))
    amount_max: Mapped[float | None] = mapped_column(Numeric(18, 2))
    currency: Mapped[str] = mapped_column(String(10), default='USDC')
    delivery_deadline: Mapped[datetime | None] = mapped_column(DateTime)
    payment_terms: Mapped[str | None] = mapped_column(String(255))
    smart_lc_required: Mapped[bool] = mapped_column(default=True)
    financing_allowed: Mapped[bool] = mapped_column(default=True)
    visibility: Mapped[str] = mapped_column(String(40), default='network', index=True)
    status: Mapped[str] = mapped_column(String(40), default='open', index=True)  # open, closed, awarded, cancelled
    requirements_json: Mapped[dict] = mapped_column(JSON, default=dict)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class SellerProposal(Base):
    """Seller response/quote against a buyer opportunity."""
    __tablename__ = 'seller_proposals'

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    opportunity_id: Mapped[str] = mapped_column(ForeignKey('trade_opportunities.id'), index=True)
    seller_business_id: Mapped[str | None] = mapped_column(ForeignKey('businesses.id'), index=True)
    created_by_user_id: Mapped[str | None] = mapped_column(ForeignKey('users.id'), index=True)
    seller_name: Mapped[str] = mapped_column(String(255))
    amount: Mapped[float] = mapped_column(Numeric(18, 2))
    currency: Mapped[str] = mapped_column(String(10), default='USDC')
    delivery_terms: Mapped[str | None] = mapped_column(Text)
    message: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(40), default='submitted', index=True)  # submitted, shortlisted, accepted, rejected, withdrawn
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class TradeContract(Base):
    """Buyer/seller agreement created directly, from an invite, or from an accepted proposal."""
    __tablename__ = 'trade_contracts'

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    buyer_business_id: Mapped[str | None] = mapped_column(ForeignKey('businesses.id'), index=True)
    seller_business_id: Mapped[str | None] = mapped_column(ForeignKey('businesses.id'), index=True)
    opportunity_id: Mapped[str | None] = mapped_column(ForeignKey('trade_opportunities.id'), index=True)
    proposal_id: Mapped[str | None] = mapped_column(ForeignKey('seller_proposals.id'), index=True)
    relationship_id: Mapped[str | None] = mapped_column(ForeignKey('counterparty_relationships.id'), index=True)
    created_by_user_id: Mapped[str | None] = mapped_column(ForeignKey('users.id'), index=True)
    buyer_name: Mapped[str] = mapped_column(String(255))
    seller_name: Mapped[str] = mapped_column(String(255))
    seller_invite_email: Mapped[str | None] = mapped_column(String(255), index=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    amount: Mapped[float] = mapped_column(Numeric(18, 2))
    currency: Mapped[str] = mapped_column(String(10), default='USDC')
    delivery_terms: Mapped[str | None] = mapped_column(Text)
    payment_terms: Mapped[str | None] = mapped_column(String(255))
    delivery_deadline: Mapped[datetime | None] = mapped_column(DateTime)
    smart_lc_required: Mapped[bool] = mapped_column(default=True)
    financing_allowed: Mapped[bool] = mapped_column(default=True)
    status: Mapped[str] = mapped_column(String(40), default='draft', index=True)  # draft, invited, accepted, changes_requested, active, cancelled, completed
    change_request_reason: Mapped[str | None] = mapped_column(Text)
    linked_order_id: Mapped[str | None] = mapped_column(ForeignKey('orders.id'), index=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
