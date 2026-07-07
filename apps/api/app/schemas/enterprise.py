from datetime import datetime
from pydantic import BaseModel, Field
from app.schemas.common import ORMModel


class BuyerActionCreate(BaseModel):
    buyer_business_id: str | None = None
    seller_business_id: str | None = None
    order_id: str | None = None
    invoice_id: str | None = None
    smart_lc_id: str | None = None
    action_type: str
    title: str
    description: str | None = None
    priority: str = 'medium'
    due_at: datetime | None = None
    metadata_json: dict = {}


class BuyerActionDecision(BaseModel):
    decision: str = Field(pattern='^(approved|rejected|disputed|needs_more_info)$')
    reason: str | None = None
    metadata_json: dict = {}


class BuyerActionRead(ORMModel):
    id: str
    buyer_user_id: str | None
    buyer_business_id: str | None
    seller_business_id: str | None
    order_id: str | None
    invoice_id: str | None
    smart_lc_id: str | None
    action_type: str
    priority: str
    status: str
    title: str
    description: str | None
    due_at: datetime | None
    decision_reason: str | None
    metadata_json: dict
    created_at: datetime


class LogisticsVerificationCreate(BaseModel):
    order_id: str
    invoice_id: str | None = None
    provider: str = 'mock'
    carrier_name: str | None = None
    tracking_reference: str | None = None
    delivery_status: str = 'pending'
    gps_match_status: str = 'unknown'
    timestamp_status: str = 'unknown'
    handover_status: str = 'unknown'
    evidence_uri: str | None = None
    metadata_json: dict = {}


class LogisticsVerificationUpdate(BaseModel):
    delivery_status: str | None = None
    gps_match_status: str | None = None
    timestamp_status: str | None = None
    handover_status: str | None = None
    evidence_uri: str | None = None
    metadata_json: dict | None = None


class LogisticsVerificationRead(ORMModel):
    id: str
    order_id: str
    invoice_id: str | None
    provider: str
    carrier_name: str | None
    tracking_reference: str | None
    delivery_status: str
    gps_match_status: str
    timestamp_status: str
    handover_status: str
    evidence_uri: str | None
    confidence_score: int
    metadata_json: dict
    created_at: datetime


class EvidenceBundleCreate(BaseModel):
    business_id: str
    invoice_id: str | None = None
    receivable_id: str | None = None
    smart_lc_id: str | None = None
    bundle_type: str = 'underwriting'
    expires_in_days: int = Field(default=7, ge=1, le=90)
    metadata_json: dict = {}


class EvidenceBundleRead(ORMModel):
    id: str
    business_id: str
    invoice_id: str | None
    receivable_id: str | None
    smart_lc_id: str | None
    bundle_type: str
    status: str
    completeness_score: int
    secure_share_token: str | None
    expires_at: datetime | None
    payload_json: dict
    created_at: datetime


class EvidenceBundleItemRead(ORMModel):
    id: str
    bundle_id: str
    item_type: str
    title: str
    source: str
    status: str
    resource_type: str | None
    resource_id: str | None
    proof_hash: str | None
    polygon_tx_hash: str | None
    metadata_json: dict


class EvidenceBundleDetail(BaseModel):
    bundle: EvidenceBundleRead
    items: list[EvidenceBundleItemRead]
    export_url: str | None = None


class RepaymentScheduleCreate(BaseModel):
    receivable_id: str
    smart_lc_id: str | None = None
    payer_name: str
    payee_name: str
    event_type: str = 'buyer_repayment_due'
    due_at: datetime
    amount: float = Field(gt=0)
    currency: str = 'USDC'
    metadata_json: dict = {}


class RepaymentScheduleRead(ORMModel):
    id: str
    receivable_id: str
    smart_lc_id: str | None
    payer_name: str
    payee_name: str
    event_type: str
    due_at: datetime
    amount: float
    currency: str
    status: str
    metadata_json: dict
    created_at: datetime


class RepaymentStatusUpdate(BaseModel):
    status: str
    metadata_json: dict = {}


class RiskRuleCreate(BaseModel):
    name: str
    scope: str
    severity: str = 'medium'
    condition_json: dict = {}
    action: str = 'manual_review'
    is_enabled: bool = True


class RiskRuleRead(ORMModel):
    id: str
    name: str
    scope: str
    severity: str
    condition_json: dict
    action: str
    is_enabled: bool
    created_at: datetime


class RiskRuleEvaluationRequest(BaseModel):
    context_json: dict = {}


class RiskRuleEvaluationResult(BaseModel):
    allowed: bool
    triggered_rules: list[dict]
    decision: str


class ApiKeyCreate(BaseModel):
    name: str
    scopes_json: list[str] = ['proofs:write', 'receivables:write', 'smart_lcs:write', 'scores:read']
    environment: str = 'sandbox'


class ApiKeyRead(ORMModel):
    id: str
    name: str
    key_prefix: str
    scopes_json: list
    environment: str
    status: str
    created_at: datetime
    revoked_at: datetime | None


class ApiKeyCreateResponse(BaseModel):
    api_key: ApiKeyRead
    secret_key: str


class WebhookEndpointCreate(BaseModel):
    url: str
    events_json: list[str] = ['proof.anchored', 'receivable.created', 'smart_lc.funded', 'score.attested']


class WebhookEndpointRead(ORMModel):
    id: str
    url: str
    events_json: list
    status: str
    created_at: datetime


class WebhookDeliveryRead(ORMModel):
    id: str
    endpoint_id: str | None
    event_type: str
    payload_json: dict
    status: str
    attempts: int
    last_error: str | None
    created_at: datetime
    delivered_at: datetime | None


class ApiSimulationRequest(BaseModel):
    endpoint_key: str
    request_json: dict = {}


class ApiSimulationResponse(BaseModel):
    endpoint: str
    method: str
    request_json: dict
    response_json: dict
    webhook_delivery_id: str | None = None


class PermissionMatrixResponse(BaseModel):
    roles: list[str]
    capabilities: list[dict]


class DealRoomSummary(BaseModel):
    receivable_count: int
    total_face_value: float
    recommended_advance: float
    risk_band: str
    open_disputes: int
    proof_receipts: int


class SmartLCActionRequest(BaseModel):
    reason: str | None = None
    metadata_json: dict = {}



class BusinessDirectoryProfileUpsert(BaseModel):
    display_name: str
    role_type: str = Field(pattern='^(buyer|seller|financier|logistics)$')
    headline: str | None = None
    description: str | None = None
    sectors_json: list[str] = []
    countries_json: list[str] = []
    capabilities_json: list[str] = []
    preferred_currencies_json: list[str] = ['USDC']
    contact_email: str | None = None
    visibility: str = Field(default='network', pattern='^(private|network|public)$')
    discovery_status: str = Field(default='listed', pattern='^(draft|listed|suspended)$')
    metadata_json: dict = {}


class BusinessDirectoryProfileRead(ORMModel):
    id: str
    business_id: str
    display_name: str
    role_type: str
    headline: str | None
    description: str | None
    sectors_json: list
    countries_json: list
    capabilities_json: list
    preferred_currencies_json: list
    contact_email: str | None
    visibility: str
    discovery_status: str
    trust_score_snapshot: int
    metadata_json: dict
    created_at: datetime
    updated_at: datetime


class CounterpartyInviteCreate(BaseModel):
    requester_business_id: str | None = None
    counterparty_business_id: str | None = None
    relationship_type: str = Field(pattern='^(buyer_seller|financier_sme|logistics_partner)$')
    invited_email: str | None = None
    invited_business_name: str | None = None
    invitation_message: str | None = None
    metadata_json: dict = {}


class CounterpartyRelationshipRead(ORMModel):
    id: str
    requester_business_id: str | None
    counterparty_business_id: str | None
    created_by_user_id: str | None
    relationship_type: str
    status: str
    invited_email: str | None
    invited_business_name: str | None
    invite_token: str | None
    invitation_message: str | None
    metadata_json: dict
    accepted_at: datetime | None
    created_at: datetime
    updated_at: datetime


class RelationshipDecision(BaseModel):
    decision: str = Field(pattern='^(accepted|rejected|blocked)$')
    reason: str | None = None
    metadata_json: dict = {}


class TradeOpportunityCreate(BaseModel):
    buyer_business_id: str | None = None
    title: str
    description: str
    sector: str | None = None
    country: str | None = None
    delivery_location: str | None = None
    amount_min: float | None = None
    amount_max: float | None = None
    currency: str = 'USDC'
    delivery_deadline: datetime | None = None
    payment_terms: str | None = None
    smart_lc_required: bool = True
    financing_allowed: bool = True
    visibility: str = Field(default='network', pattern='^(private|network|public)$')
    requirements_json: dict = {}
    metadata_json: dict = {}


class TradeOpportunityRead(ORMModel):
    id: str
    buyer_business_id: str | None
    created_by_user_id: str | None
    title: str
    description: str
    sector: str | None
    country: str | None
    delivery_location: str | None
    amount_min: float | None
    amount_max: float | None
    currency: str
    delivery_deadline: datetime | None
    payment_terms: str | None
    smart_lc_required: bool
    financing_allowed: bool
    visibility: str
    status: str
    requirements_json: dict
    metadata_json: dict
    created_at: datetime
    updated_at: datetime


class SellerProposalCreate(BaseModel):
    seller_business_id: str | None = None
    seller_name: str
    amount: float = Field(gt=0)
    currency: str = 'USDC'
    delivery_terms: str | None = None
    message: str | None = None
    metadata_json: dict = {}


class SellerProposalRead(ORMModel):
    id: str
    opportunity_id: str
    seller_business_id: str | None
    created_by_user_id: str | None
    seller_name: str
    amount: float
    currency: str
    delivery_terms: str | None
    message: str | None
    status: str
    metadata_json: dict
    created_at: datetime
    updated_at: datetime


class ProposalDecision(BaseModel):
    decision: str = Field(pattern='^(shortlisted|accepted|rejected|withdrawn)$')
    reason: str | None = None
    create_contract: bool = True
    metadata_json: dict = {}


class TradeContractCreate(BaseModel):
    buyer_business_id: str | None = None
    seller_business_id: str | None = None
    seller_invite_email: str | None = None
    seller_name: str
    buyer_name: str
    title: str
    description: str
    amount: float = Field(gt=0)
    currency: str = 'USDC'
    delivery_terms: str | None = None
    payment_terms: str | None = None
    delivery_deadline: datetime | None = None
    smart_lc_required: bool = True
    financing_allowed: bool = True
    metadata_json: dict = {}


class TradeContractRead(ORMModel):
    id: str
    buyer_business_id: str | None
    seller_business_id: str | None
    opportunity_id: str | None
    proposal_id: str | None
    relationship_id: str | None
    created_by_user_id: str | None
    buyer_name: str
    seller_name: str
    seller_invite_email: str | None
    title: str
    description: str
    amount: float
    currency: str
    delivery_terms: str | None
    payment_terms: str | None
    delivery_deadline: datetime | None
    smart_lc_required: bool
    financing_allowed: bool
    status: str
    change_request_reason: str | None
    linked_order_id: str | None
    metadata_json: dict
    created_at: datetime
    updated_at: datetime


class TradeContractDecision(BaseModel):
    decision: str = Field(pattern='^(accepted|rejected|changes_requested|cancelled)$')
    reason: str | None = None
    metadata_json: dict = {}


class FinancierMarketplaceItem(BaseModel):
    receivable_id: str
    seller_business_id: str
    debtor_name: str
    face_value: float
    currency: str
    maturity_date: datetime
    status: str
    recommended_advance: float
    proof_hash: str
    polygon_tx_hash: str | None
    risk_inputs: dict


class NetworkSummary(BaseModel):
    directory_count: int
    open_opportunities: int
    active_contracts: int
    submitted_proposals: int
    financeable_deals: int
    relationship_count: int
