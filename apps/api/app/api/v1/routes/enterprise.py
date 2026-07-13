from datetime import datetime, timedelta
from secrets import token_urlsafe

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.hashing import sha256_hex
from app.core.security import Role, require_roles
from app.models.audit import BlockchainOutbox
from app.models.business import Business, KYBProfile
from app.models.enterprise import (
    ApiKey,
    ApiUsageLog,
    BusinessDirectoryProfile,
    CounterpartyRelationship,
    TradeOpportunity,
    SellerProposal,
    TradeContract,
    BuyerAction,
    EvidenceBundle,
    EvidenceBundleItem,
    LogisticsVerification,
    RepaymentScheduleItem,
    RiskRule,
    WebhookDelivery,
    WebhookEndpoint,
)
from app.models.enums import InvoiceStatus, OrderStatus, ProofStatus, ReceivableStatus, SmartLCStatus
from app.models.finance import FinancingOffer, TrustScore
from app.models.identity import User
from app.models.trade import DeliveryProof, Invoice, Order, ProofBundle, Receivable, SmartLC
from app.schemas.enterprise import (
    ApiKeyCreate,
    ApiKeyCreateResponse,
    ApiKeyRead,
    ApiSimulationRequest,
    ApiSimulationResponse,
    BusinessDirectoryProfileUpsert,
    BusinessDirectoryProfileRead,
    CounterpartyInviteCreate,
    CounterpartyRelationshipRead,
    RelationshipDecision,
    TradeOpportunityCreate,
    TradeOpportunityRead,
    SellerProposalCreate,
    SellerProposalRead,
    ProposalDecision,
    TradeContractCreate,
    TradeContractRead,
    TradeContractDecision,
    FinancierMarketplaceItem,
    NetworkSummary,
    BuyerActionCreate,
    BuyerActionDecision,
    BuyerActionRead,
    DealRoomSummary,
    EvidenceBundleCreate,
    EvidenceBundleDetail,
    EvidenceBundleItemRead,
    EvidenceBundleRead,
    LogisticsVerificationCreate,
    LogisticsVerificationRead,
    LogisticsVerificationUpdate,
    PermissionMatrixResponse,
    RepaymentScheduleCreate,
    RepaymentScheduleRead,
    RepaymentStatusUpdate,
    RiskRuleCreate,
    RiskRuleEvaluationRequest,
    RiskRuleEvaluationResult,
    RiskRuleRead,
    SmartLCActionRequest,
    WebhookDeliveryRead,
    WebhookEndpointCreate,
    WebhookEndpointRead,
)
from app.schemas.trade import OrderRead
from app.services.audit import record_audit
from app.services.polygon import explorer_tx_url, publish_tx
from app.services.proofs import create_proof_bundle
from app.services.scoring import calculate_trade_credit_score

router = APIRouter()


def _now() -> datetime:
    return datetime.utcnow()


def _get_or_404(db: Session, model, resource_id: str, label: str):
    resource = db.get(model, resource_id)
    if not resource:
        raise HTTPException(status_code=404, detail=f'{label} not found')
    return resource


def _log_webhook(db: Session, event_type: str, payload: dict, endpoint_id: str | None = None) -> WebhookDelivery:
    delivery = WebhookDelivery(
        endpoint_id=endpoint_id,
        event_type=event_type,
        payload_json=payload,
        status='delivered',
        attempts=1,
        delivered_at=_now(),
    )
    db.add(delivery)
    return delivery


def _score_logistics_confidence(record: LogisticsVerification) -> int:
    score = 10
    if record.delivery_status in {'delivered', 'confirmed'}:
        score += 35
    if record.gps_match_status in {'matched', 'matched_buyer_location', 'verified'}:
        score += 20
    if record.timestamp_status in {'within_window', 'verified'}:
        score += 15
    if record.handover_status in {'otp_matched', 'signed', 'confirmed'}:
        score += 20
    if record.evidence_uri:
        score += 10
    return min(score, 100)


def _build_default_buyer_action_for_invoice(invoice: Invoice) -> dict:
    return {
        'seller_business_id': invoice.seller_business_id,
        'order_id': invoice.order_id,
        'invoice_id': invoice.id,
        'action_type': 'invoice_confirmation',
        'priority': 'high',
        'title': f'Confirm invoice {invoice.invoice_number}',
        'description': f'Buyer confirmation is required for invoice {invoice.invoice_number} before receivable financing.',
        'metadata_json': {'invoice_number': invoice.invoice_number, 'buyer_name': invoice.buyer_name},
    }


def _find_business_display_name(db: Session, business_id: str | None, fallback: str | None = None) -> str:
    if business_id:
        business = db.get(Business, business_id)
        if business:
            return business.legal_name
    return fallback or 'External counterparty'


def _latest_business_score(db: Session, business_id: str | None) -> int:
    if not business_id:
        return 0
    score = db.query(TrustScore).filter(TrustScore.business_id == business_id).order_by(TrustScore.created_at.desc()).first()
    return int(score.score) if score else 0


def _create_trade_contract_from_proposal(db: Session, proposal: SellerProposal, user_id: str | None) -> TradeContract:
    opportunity = _get_or_404(db, TradeOpportunity, proposal.opportunity_id, 'Trade opportunity')
    buyer_name = _find_business_display_name(db, opportunity.buyer_business_id, 'Buyer')
    contract = TradeContract(
        buyer_business_id=opportunity.buyer_business_id,
        seller_business_id=proposal.seller_business_id,
        opportunity_id=opportunity.id,
        proposal_id=proposal.id,
        created_by_user_id=user_id,
        buyer_name=buyer_name,
        seller_name=proposal.seller_name,
        title=opportunity.title,
        description=opportunity.description,
        amount=proposal.amount,
        currency=proposal.currency,
        delivery_terms=proposal.delivery_terms,
        payment_terms=opportunity.payment_terms,
        delivery_deadline=opportunity.delivery_deadline,
        smart_lc_required=opportunity.smart_lc_required,
        financing_allowed=opportunity.financing_allowed,
        status='accepted',
        metadata_json={'source': 'accepted_proposal'},
    )
    db.add(contract)
    return contract


@router.get('/network/summary', response_model=NetworkSummary)
def network_summary(
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.ADMIN, Role.SME, Role.BUYER, Role.FINANCIER, Role.DEVELOPER)),
):
    return NetworkSummary(
        directory_count=db.query(BusinessDirectoryProfile).filter(BusinessDirectoryProfile.discovery_status == 'listed').count(),
        open_opportunities=db.query(TradeOpportunity).filter(TradeOpportunity.status == 'open').count(),
        active_contracts=db.query(TradeContract).filter(TradeContract.status.in_(['accepted', 'active'])).count(),
        submitted_proposals=db.query(SellerProposal).filter(SellerProposal.status.in_(['submitted', 'shortlisted'])).count(),
        financeable_deals=db.query(Receivable).filter(Receivable.status.in_([ReceivableStatus.CREATED.value, ReceivableStatus.TOKENIZED.value])).count(),
        relationship_count=db.query(CounterpartyRelationship).filter(CounterpartyRelationship.status == 'accepted').count(),
    )


@router.get('/network/directory', response_model=list[BusinessDirectoryProfileRead])
def search_business_directory(
    role_type: str | None = None,
    sector: str | None = None,
    country: str | None = None,
    q: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.ADMIN, Role.SME, Role.BUYER, Role.FINANCIER, Role.DEVELOPER)),
):
    query = db.query(BusinessDirectoryProfile).filter(
        BusinessDirectoryProfile.discovery_status == 'listed',
        BusinessDirectoryProfile.visibility.in_(['network', 'public']),
    )
    if role_type:
        query = query.filter(BusinessDirectoryProfile.role_type == role_type)
    profiles = query.order_by(BusinessDirectoryProfile.trust_score_snapshot.desc(), BusinessDirectoryProfile.created_at.desc()).limit(300).all()
    def matches(profile: BusinessDirectoryProfile) -> bool:
        if sector and sector not in (profile.sectors_json or []):
            return False
        if country and country not in (profile.countries_json or []):
            return False
        if q:
            haystack = ' '.join([profile.display_name or '', profile.headline or '', profile.description or '']).lower()
            return q.lower() in haystack
        return True
    return [p for p in profiles if matches(p)]


@router.post('/network/directory/{business_id}', response_model=BusinessDirectoryProfileRead)
def upsert_business_directory_profile(
    business_id: str,
    payload: BusinessDirectoryProfileUpsert,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.ADMIN, Role.SME, Role.BUYER, Role.FINANCIER, Role.DEVELOPER)),
):
    _get_or_404(db, Business, business_id, 'Business')
    profile = db.query(BusinessDirectoryProfile).filter(BusinessDirectoryProfile.business_id == business_id).first()
    data = payload.model_dump()
    if profile:
        before = {'display_name': profile.display_name, 'role_type': profile.role_type, 'visibility': profile.visibility, 'discovery_status': profile.discovery_status}
        for key, value in data.items():
            setattr(profile, key, value)
        profile.trust_score_snapshot = _latest_business_score(db, business_id)
        profile.updated_at = _now()
        record_audit(db, user.id, 'network.directory_profile.updated', 'business', business_id, {'before': before, 'after': data})
    else:
        profile = BusinessDirectoryProfile(**data, business_id=business_id, trust_score_snapshot=_latest_business_score(db, business_id))
        db.add(profile)
        record_audit(db, user.id, 'network.directory_profile.created', 'business', business_id, data)
    _log_webhook(db, 'network.directory_profile.upserted', {'business_id': business_id, 'role_type': profile.role_type})
    db.commit(); db.refresh(profile)
    return profile


@router.post('/network/invitations', response_model=CounterpartyRelationshipRead)
def create_counterparty_invitation(
    payload: CounterpartyInviteCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.ADMIN, Role.SME, Role.BUYER, Role.FINANCIER)),
):
    if payload.requester_business_id:
        _get_or_404(db, Business, payload.requester_business_id, 'Requester business')
    if payload.counterparty_business_id:
        _get_or_404(db, Business, payload.counterparty_business_id, 'Counterparty business')
    relationship = CounterpartyRelationship(
        **payload.model_dump(),
        created_by_user_id=user.id,
        invite_token=token_urlsafe(24),
        status='invited',
    )
    db.add(relationship)
    record_audit(db, user.id, 'network.counterparty_invited', 'counterparty_relationship', relationship.id, payload.model_dump())
    _log_webhook(db, 'network.counterparty_invited', {'relationship_id': relationship.id, 'relationship_type': relationship.relationship_type})
    db.commit(); db.refresh(relationship)
    return relationship


@router.get('/network/invitations', response_model=list[CounterpartyRelationshipRead])
def list_counterparty_relationships(
    status: str | None = None,
    relationship_type: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.ADMIN, Role.SME, Role.BUYER, Role.FINANCIER)),
):
    query = db.query(CounterpartyRelationship)
    if status:
        query = query.filter(CounterpartyRelationship.status == status)
    if relationship_type:
        query = query.filter(CounterpartyRelationship.relationship_type == relationship_type)
    return query.order_by(CounterpartyRelationship.created_at.desc()).limit(300).all()


@router.post('/network/invitations/{relationship_id}/decision', response_model=CounterpartyRelationshipRead)
def decide_counterparty_relationship(
    relationship_id: str,
    payload: RelationshipDecision,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.ADMIN, Role.SME, Role.BUYER, Role.FINANCIER)),
):
    relationship = _get_or_404(db, CounterpartyRelationship, relationship_id, 'Counterparty relationship')
    before = {'status': relationship.status}
    relationship.status = payload.decision
    relationship.metadata_json = {**(relationship.metadata_json or {}), **payload.metadata_json, 'decision_reason': payload.reason}
    relationship.updated_at = _now()
    if payload.decision == 'accepted':
        relationship.accepted_at = _now()
    record_audit(db, user.id, 'network.counterparty_relationship.decided', 'counterparty_relationship', relationship.id, {'before': before, 'after': {'status': relationship.status}, 'reason': payload.reason})
    _log_webhook(db, 'network.counterparty_relationship.decided', {'relationship_id': relationship.id, 'decision': payload.decision})
    db.commit(); db.refresh(relationship)
    return relationship


@router.post('/network/trade-contracts', response_model=TradeContractRead)
def create_trade_contract(
    payload: TradeContractCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.ADMIN, Role.BUYER, Role.SME)),
):
    if payload.buyer_business_id:
        _get_or_404(db, Business, payload.buyer_business_id, 'Buyer business')
    if payload.seller_business_id:
        _get_or_404(db, Business, payload.seller_business_id, 'Seller business')
    relationship = None
    if payload.seller_business_id or payload.seller_invite_email:
        relationship = CounterpartyRelationship(
            requester_business_id=payload.buyer_business_id,
            counterparty_business_id=payload.seller_business_id,
            created_by_user_id=user.id,
            relationship_type='buyer_seller',
            status='invited' if not payload.seller_business_id else 'accepted',
            invited_email=payload.seller_invite_email,
            invited_business_name=payload.seller_name,
            invite_token=token_urlsafe(24),
            invitation_message=f'You have been invited to trade contract: {payload.title}',
        )
        db.add(relationship)
        db.flush()
    contract = TradeContract(
        **payload.model_dump(),
        relationship_id=relationship.id if relationship else None,
        created_by_user_id=user.id,
        status='invited' if payload.seller_invite_email and not payload.seller_business_id else 'draft',
    )
    db.add(contract)
    record_audit(db, user.id, 'network.trade_contract.created', 'trade_contract', contract.id, payload.model_dump())
    _log_webhook(db, 'network.trade_contract.created', {'trade_contract_id': contract.id, 'status': contract.status})
    db.commit(); db.refresh(contract)
    return contract


@router.get('/network/trade-contracts', response_model=list[TradeContractRead])
def list_trade_contracts(
    status: str | None = None,
    business_id: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.ADMIN, Role.BUYER, Role.SME, Role.FINANCIER)),
):
    query = db.query(TradeContract)
    if status:
        query = query.filter(TradeContract.status == status)
    if business_id:
        query = query.filter((TradeContract.buyer_business_id == business_id) | (TradeContract.seller_business_id == business_id))
    return query.order_by(TradeContract.created_at.desc()).limit(300).all()


@router.post('/network/trade-contracts/{contract_id}/decision', response_model=TradeContractRead)
def decide_trade_contract(
    contract_id: str,
    payload: TradeContractDecision,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.ADMIN, Role.SME, Role.BUYER)),
):
    contract = _get_or_404(db, TradeContract, contract_id, 'Trade contract')
    before = {'status': contract.status}
    contract.status = payload.decision
    contract.change_request_reason = payload.reason if payload.decision == 'changes_requested' else contract.change_request_reason
    contract.metadata_json = {**(contract.metadata_json or {}), **payload.metadata_json}
    contract.updated_at = _now()
    record_audit(db, user.id, 'network.trade_contract.decided', 'trade_contract', contract.id, {'before': before, 'after': {'status': contract.status}, 'reason': payload.reason})
    _log_webhook(db, 'network.trade_contract.decided', {'trade_contract_id': contract.id, 'decision': payload.decision})
    db.commit(); db.refresh(contract)
    return contract


@router.post('/network/trade-contracts/{contract_id}/activate', response_model=OrderRead)
def activate_trade_contract(
    contract_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.ADMIN, Role.BUYER, Role.SME)),
):
    contract = _get_or_404(db, TradeContract, contract_id, 'Trade contract')
    if contract.status not in {'accepted', 'draft', 'invited'}:
        raise HTTPException(400, 'Only draft, invited or accepted contracts can be activated')
    order = Order(
        seller_business_id=contract.seller_business_id or contract.buyer_business_id,
        buyer_business_id=contract.buyer_business_id,
        buyer_name=contract.buyer_name,
        description=contract.description,
        currency=contract.currency,
        total_amount=contract.amount,
        expected_delivery_date=contract.delivery_deadline,
        status=OrderStatus.CONFIRMED.value,
    )
    db.add(order); db.flush()
    contract.status = 'active'
    contract.linked_order_id = order.id
    contract.updated_at = _now()
    record_audit(db, user.id, 'network.trade_contract.activated', 'trade_contract', contract.id, {'order_id': order.id})
    _log_webhook(db, 'network.trade_contract.activated', {'trade_contract_id': contract.id, 'order_id': order.id})
    db.commit(); db.refresh(order)
    return order


@router.post('/network/opportunities', response_model=TradeOpportunityRead)
def create_trade_opportunity(
    payload: TradeOpportunityCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.ADMIN, Role.BUYER)),
):
    if payload.buyer_business_id:
        _get_or_404(db, Business, payload.buyer_business_id, 'Buyer business')
    opportunity = TradeOpportunity(**payload.model_dump(), created_by_user_id=user.id)
    db.add(opportunity)
    record_audit(db, user.id, 'network.trade_opportunity.created', 'trade_opportunity', opportunity.id, payload.model_dump())
    _log_webhook(db, 'network.trade_opportunity.created', {'opportunity_id': opportunity.id})
    db.commit(); db.refresh(opportunity)
    return opportunity


@router.get('/network/opportunities', response_model=list[TradeOpportunityRead])
def list_trade_opportunities(
    sector: str | None = None,
    country: str | None = None,
    status: str | None = 'open',
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.ADMIN, Role.BUYER, Role.SME, Role.FINANCIER)),
):
    query = db.query(TradeOpportunity)
    if status:
        query = query.filter(TradeOpportunity.status == status)
    if sector:
        query = query.filter(TradeOpportunity.sector == sector)
    if country:
        query = query.filter(TradeOpportunity.country == country)
    return query.order_by(TradeOpportunity.created_at.desc()).limit(300).all()


@router.post('/network/opportunities/{opportunity_id}/proposals', response_model=SellerProposalRead)
def submit_seller_proposal(
    opportunity_id: str,
    payload: SellerProposalCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.ADMIN, Role.SME)),
):
    opportunity = _get_or_404(db, TradeOpportunity, opportunity_id, 'Trade opportunity')
    if opportunity.status != 'open':
        raise HTTPException(400, 'Opportunity is not open')
    if payload.seller_business_id:
        _get_or_404(db, Business, payload.seller_business_id, 'Seller business')
    proposal = SellerProposal(**payload.model_dump(), opportunity_id=opportunity.id, created_by_user_id=user.id)
    db.add(proposal)
    record_audit(db, user.id, 'network.seller_proposal.submitted', 'seller_proposal', proposal.id, {'opportunity_id': opportunity.id})
    _log_webhook(db, 'network.seller_proposal.submitted', {'opportunity_id': opportunity.id, 'proposal_id': proposal.id})
    db.commit(); db.refresh(proposal)
    return proposal


@router.get('/network/opportunities/{opportunity_id}/proposals', response_model=list[SellerProposalRead])
def list_seller_proposals(
    opportunity_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.ADMIN, Role.BUYER, Role.SME)),
):
    _get_or_404(db, TradeOpportunity, opportunity_id, 'Trade opportunity')
    return db.query(SellerProposal).filter(SellerProposal.opportunity_id == opportunity_id).order_by(SellerProposal.created_at.desc()).limit(300).all()


@router.post('/network/proposals/{proposal_id}/decision', response_model=dict)
def decide_seller_proposal(
    proposal_id: str,
    payload: ProposalDecision,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.ADMIN, Role.BUYER)),
):
    proposal = _get_or_404(db, SellerProposal, proposal_id, 'Seller proposal')
    before = {'status': proposal.status}
    proposal.status = payload.decision
    proposal.metadata_json = {**(proposal.metadata_json or {}), **payload.metadata_json, 'decision_reason': payload.reason}
    proposal.updated_at = _now()
    contract = None
    if payload.decision == 'accepted' and payload.create_contract:
        opportunity = _get_or_404(db, TradeOpportunity, proposal.opportunity_id, 'Trade opportunity')
        opportunity.status = 'awarded'
        contract = _create_trade_contract_from_proposal(db, proposal, user.id)
    record_audit(db, user.id, 'network.seller_proposal.decided', 'seller_proposal', proposal.id, {'before': before, 'after': {'status': proposal.status}, 'reason': payload.reason})
    _log_webhook(db, 'network.seller_proposal.decided', {'proposal_id': proposal.id, 'decision': payload.decision, 'contract_id': contract.id if contract else None})
    db.commit(); db.refresh(proposal)
    return {'proposal': proposal, 'trade_contract': contract}


@router.get('/network/financier-marketplace/deals', response_model=list[FinancierMarketplaceItem])
def financier_deal_marketplace(
    min_amount: float | None = None,
    max_amount: float | None = None,
    currency: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.ADMIN, Role.FINANCIER)),
):
    query = db.query(Receivable).filter(Receivable.status.in_([ReceivableStatus.CREATED.value, ReceivableStatus.TOKENIZED.value, ReceivableStatus.FINANCED.value]))
    if currency:
        query = query.filter(Receivable.currency == currency)
    receivables = query.order_by(Receivable.created_at.desc()).limit(300).all()
    response: list[FinancierMarketplaceItem] = []
    for receivable in receivables:
        face = float(receivable.face_value)
        if min_amount is not None and face < min_amount:
            continue
        if max_amount is not None and face > max_amount:
            continue
        invoice = db.get(Invoice, receivable.invoice_id)
        latest_bundle = db.query(ProofBundle).filter(ProofBundle.invoice_id == receivable.invoice_id).order_by(ProofBundle.created_at.desc()).first()
        score = _latest_business_score(db, receivable.seller_business_id)
        response.append(FinancierMarketplaceItem(
            receivable_id=receivable.id,
            seller_business_id=receivable.seller_business_id,
            debtor_name=receivable.debtor_name,
            face_value=face,
            currency=receivable.currency,
            maturity_date=receivable.maturity_date,
            status=receivable.status,
            recommended_advance=round(face * 0.8, 2),
            proof_hash=receivable.proof_hash,
            polygon_tx_hash=receivable.polygon_tx_hash or (latest_bundle.polygon_tx_hash if latest_bundle else None),
            risk_inputs={
                'buyer_confirmed': invoice.status == InvoiceStatus.BUYER_CONFIRMED.value if invoice else False,
                'seller_score': score,
                'proof_bundle_status': latest_bundle.status if latest_bundle else None,
                'disputed': invoice.status == InvoiceStatus.DISPUTED.value if invoice else False,
            },
        ))
    return response


@router.post('/network/financier-marketplace/deals/{receivable_id}/express-interest')
def express_financier_interest(
    receivable_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.FINANCIER, Role.ADMIN)),
):
    receivable = _get_or_404(db, Receivable, receivable_id, 'Receivable')
    offer_amount = round(float(receivable.face_value) * 0.8, 2)
    offer = FinancingOffer(
        financier_user_id=user.id,
        receivable_id=receivable.id,
        advance_rate_bps=8000,
        fee_bps=50,
        offer_amount=offer_amount,
        status='interested',
    )
    db.add(offer)
    record_audit(db, user.id, 'network.financier_interest.expressed', 'receivable', receivable.id, {'offer_amount': offer_amount})
    _log_webhook(db, 'network.financier_interest.expressed', {'receivable_id': receivable.id, 'offer_amount': offer_amount})
    db.commit(); db.refresh(offer)
    return {'offer': offer, 'recommended_advance': offer_amount}



@router.get('/buyer-inbox/actions', response_model=list[BuyerActionRead])
def list_buyer_actions(
    status: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.BUYER, Role.ADMIN)),
):
    q = db.query(BuyerAction)
    if user.role == Role.BUYER.value:
        q = q.filter((BuyerAction.buyer_user_id == user.id) | (BuyerAction.buyer_user_id.is_(None)))
    if status:
        q = q.filter(BuyerAction.status == status)
    return q.order_by(BuyerAction.created_at.desc()).limit(200).all()


@router.post('/buyer-inbox/actions', response_model=BuyerActionRead)
def create_buyer_action(
    payload: BuyerActionCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.SME, Role.ADMIN)),
):
    action = BuyerAction(**payload.model_dump())
    db.add(action)
    record_audit(db, user.id, 'buyer_action.created', 'buyer_action', action.id, payload.model_dump())
    db.commit(); db.refresh(action)
    return action


@router.post('/buyer-inbox/invoices/{invoice_id}/request-confirmation', response_model=BuyerActionRead)
def request_invoice_confirmation(
    invoice_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.SME, Role.ADMIN)),
):
    invoice = _get_or_404(db, Invoice, invoice_id, 'Invoice')
    payload = _build_default_buyer_action_for_invoice(invoice)
    action = BuyerAction(**payload)
    db.add(action)
    record_audit(db, user.id, 'buyer_action.invoice_confirmation_requested', 'invoice', invoice.id, {'buyer_action_id': action.id})
    db.commit(); db.refresh(action)
    return action


@router.post('/buyer-inbox/actions/{action_id}/decision', response_model=BuyerActionRead)
def decide_buyer_action(
    action_id: str,
    payload: BuyerActionDecision,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.BUYER, Role.ADMIN)),
):
    action = _get_or_404(db, BuyerAction, action_id, 'Buyer action')
    before = {'status': action.status}
    action.status = payload.decision
    action.decision_reason = payload.reason
    action.metadata_json = {**(action.metadata_json or {}), **payload.metadata_json}
    action.updated_at = _now()

    if action.invoice_id:
        invoice = db.get(Invoice, action.invoice_id)
        if invoice and payload.decision == 'approved' and action.action_type == 'invoice_confirmation':
            invoice.status = InvoiceStatus.BUYER_CONFIRMED.value
            create_proof_bundle(db, invoice.seller_business_id, 'INVOICE_BUYER_CONFIRMED', {'invoice_id': invoice.id, 'buyer_action_id': action.id}, order_id=invoice.order_id, invoice_id=invoice.id)
        elif invoice and payload.decision in {'rejected', 'disputed'}:
            invoice.status = InvoiceStatus.DISPUTED.value
            order = db.get(Order, invoice.order_id)
            if order:
                order.status = OrderStatus.DISPUTED.value

    if action.smart_lc_id and payload.decision == 'disputed':
        lc = db.get(SmartLC, action.smart_lc_id)
        if lc:
            lc.status = SmartLCStatus.DISPUTED.value

    after = {'status': action.status}
    record_audit(db, user.id, 'buyer_action.decided', 'buyer_action', action.id, {'before': before, 'after': after, 'reason': payload.reason})
    _log_webhook(db, 'buyer_action.decided', {'buyer_action_id': action.id, 'decision': payload.decision})
    db.commit(); db.refresh(action)
    return action


@router.get('/logistics/verifications', response_model=list[LogisticsVerificationRead])
def list_logistics_verifications(
    order_id: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.ADMIN, Role.SME, Role.BUYER, Role.FINANCIER, Role.DEVELOPER)),
):
    q = db.query(LogisticsVerification)
    if order_id:
        q = q.filter(LogisticsVerification.order_id == order_id)
    return q.order_by(LogisticsVerification.created_at.desc()).limit(200).all()


@router.post('/logistics/verifications', response_model=LogisticsVerificationRead)
def create_logistics_verification(
    payload: LogisticsVerificationCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.SME, Role.ADMIN, Role.DEVELOPER)),
):
    order = _get_or_404(db, Order, payload.order_id, 'Order')
    if payload.invoice_id:
        _get_or_404(db, Invoice, payload.invoice_id, 'Invoice')
    record = LogisticsVerification(**payload.model_dump())
    record.confidence_score = _score_logistics_confidence(record)
    db.add(record)
    if record.confidence_score >= 70:
        order.status = OrderStatus.DELIVERED.value
    record_audit(db, user.id, 'logistics_verification.created', 'logistics_verification', record.id, payload.model_dump())
    _log_webhook(db, 'logistics.verification.created', {'logistics_verification_id': record.id, 'order_id': order.id})
    db.commit(); db.refresh(record)
    return record


@router.patch('/logistics/verifications/{verification_id}', response_model=LogisticsVerificationRead)
def update_logistics_verification(
    verification_id: str,
    payload: LogisticsVerificationUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.ADMIN, Role.DEVELOPER, Role.SME)),
):
    record = _get_or_404(db, LogisticsVerification, verification_id, 'Logistics verification')
    before = {
        'delivery_status': record.delivery_status,
        'gps_match_status': record.gps_match_status,
        'timestamp_status': record.timestamp_status,
        'handover_status': record.handover_status,
    }
    for key, value in payload.model_dump(exclude_unset=True).items():
        if value is not None:
            setattr(record, key, value)
    record.confidence_score = _score_logistics_confidence(record)
    record.updated_at = _now()
    if record.confidence_score >= 70:
        order = db.get(Order, record.order_id)
        if order:
            order.status = OrderStatus.DELIVERED.value
    after = {'confidence_score': record.confidence_score, 'delivery_status': record.delivery_status}
    record_audit(db, user.id, 'logistics_verification.updated', 'logistics_verification', record.id, {'before': before, 'after': after})
    _log_webhook(db, 'logistics.verification.updated', {'logistics_verification_id': record.id, 'confidence_score': record.confidence_score})
    db.commit(); db.refresh(record)
    return record


@router.get('/deal-room/summary', response_model=DealRoomSummary)
def deal_room_summary(
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.FINANCIER, Role.ADMIN)),
):
    receivables = db.query(Receivable).all()
    total = float(sum(float(r.face_value) for r in receivables))
    disputes = db.query(Invoice).filter(Invoice.status == InvoiceStatus.DISPUTED.value).count()
    proof_receipts = db.query(ProofBundle).filter(ProofBundle.polygon_tx_hash.isnot(None)).count()
    risk_band = 'low' if disputes == 0 and proof_receipts > 0 else 'medium' if disputes < 3 else 'high'
    return DealRoomSummary(
        receivable_count=len(receivables),
        total_face_value=total,
        recommended_advance=round(total * 0.8, 2),
        risk_band=risk_band,
        open_disputes=disputes,
        proof_receipts=proof_receipts,
    )


@router.get('/deal-room/receivables')
def deal_room_receivables(
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.FINANCIER, Role.ADMIN)),
):
    receivables = db.query(Receivable).order_by(Receivable.created_at.desc()).limit(200).all()
    response = []
    for r in receivables:
        invoice = db.get(Invoice, r.invoice_id)
        offers = db.query(FinancingOffer).filter(FinancingOffer.receivable_id == r.id).order_by(FinancingOffer.created_at.desc()).all()
        response.append({
            'receivable': r,
            'invoice': invoice,
            'offers': offers,
            'recommended_advance': round(float(r.face_value) * 0.8, 2),
            'risk_inputs': {
                'buyer_confirmed': invoice.status == InvoiceStatus.BUYER_CONFIRMED.value if invoice else False,
                'proof_hash': r.proof_hash,
                'polygon_tx_hash': r.polygon_tx_hash,
                'debtor_name': r.debtor_name,
            },
        })
    return response


@router.post('/deal-room/receivables/{receivable_id}/offers')
def create_financing_offer(
    receivable_id: str,
    advance_rate_bps: int = 8000,
    fee_bps: int = 50,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.FINANCIER, Role.ADMIN)),
):
    receivable = _get_or_404(db, Receivable, receivable_id, 'Receivable')
    offer_amount = round(float(receivable.face_value) * advance_rate_bps / 10000, 2)
    offer = FinancingOffer(
        financier_user_id=user.id,
        receivable_id=receivable.id,
        advance_rate_bps=advance_rate_bps,
        fee_bps=fee_bps,
        offer_amount=offer_amount,
        status='offered',
    )
    db.add(offer)
    record_audit(db, user.id, 'financing_offer.created', 'receivable', receivable.id, {'offer_amount': offer_amount})
    _log_webhook(db, 'financing_offer.created', {'receivable_id': receivable.id, 'offer_amount': offer_amount})
    db.commit(); db.refresh(offer)
    return offer


@router.post('/deal-room/offers/{offer_id}/{decision}')
def decide_financing_offer(
    offer_id: str,
    decision: str,
    reason: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.FINANCIER, Role.ADMIN, Role.SME)),
):
    if decision not in {'approved', 'rejected', 'accepted', 'cancelled'}:
        raise HTTPException(400, 'Invalid offer decision')
    offer = _get_or_404(db, FinancingOffer, offer_id, 'Financing offer')
    before = {'status': offer.status}
    offer.status = decision
    receivable = db.get(Receivable, offer.receivable_id)
    if receivable and decision in {'approved', 'accepted'}:
        receivable.status = ReceivableStatus.FINANCED.value
    record_audit(db, user.id, f'financing_offer.{decision}', 'financing_offer', offer.id, {'before': before, 'after': {'status': offer.status}, 'reason': reason})
    _log_webhook(db, f'financing_offer.{decision}', {'offer_id': offer.id, 'receivable_id': offer.receivable_id})
    db.commit(); db.refresh(offer)
    return offer


@router.get('/repayments', response_model=list[RepaymentScheduleRead])
def list_repayments(
    receivable_id: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.ADMIN, Role.SME, Role.FINANCIER)),
):
    q = db.query(RepaymentScheduleItem)
    if receivable_id:
        q = q.filter(RepaymentScheduleItem.receivable_id == receivable_id)
    return q.order_by(RepaymentScheduleItem.due_at.asc()).limit(300).all()


@router.post('/repayments', response_model=RepaymentScheduleRead)
def create_repayment_schedule_item(
    payload: RepaymentScheduleCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.ADMIN, Role.FINANCIER)),
):
    _get_or_404(db, Receivable, payload.receivable_id, 'Receivable')
    if payload.smart_lc_id:
        _get_or_404(db, SmartLC, payload.smart_lc_id, 'Smart LC')
    item = RepaymentScheduleItem(**payload.model_dump())
    db.add(item)
    record_audit(db, user.id, 'repayment_schedule.created', 'receivable', payload.receivable_id, payload.model_dump())
    _log_webhook(db, 'repayment.scheduled', {'receivable_id': payload.receivable_id, 'amount': payload.amount})
    db.commit(); db.refresh(item)
    return item


@router.patch('/repayments/{repayment_id}', response_model=RepaymentScheduleRead)
def update_repayment_status(
    repayment_id: str,
    payload: RepaymentStatusUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.ADMIN, Role.FINANCIER)),
):
    item = _get_or_404(db, RepaymentScheduleItem, repayment_id, 'Repayment item')
    before = {'status': item.status}
    item.status = payload.status
    item.metadata_json = {**(item.metadata_json or {}), **payload.metadata_json}
    item.updated_at = _now()
    receivable = db.get(Receivable, item.receivable_id)
    if receivable and payload.status in {'paid', 'completed'}:
        receivable.status = ReceivableStatus.SETTLED.value
    elif receivable and payload.status in {'defaulted', 'overdue'}:
        receivable.status = ReceivableStatus.DEFAULTED.value
    record_audit(db, user.id, 'repayment.status_updated', 'repayment', item.id, {'before': before, 'after': {'status': item.status}})
    _log_webhook(db, 'repayment.status_updated', {'repayment_id': item.id, 'status': item.status})
    db.commit(); db.refresh(item)
    return item


@router.post('/evidence/bundles', response_model=EvidenceBundleDetail)
def generate_evidence_bundle(
    payload: EvidenceBundleCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.ADMIN, Role.SME, Role.FINANCIER)),
):
    business = _get_or_404(db, Business, payload.business_id, 'Business')
    if payload.invoice_id:
        _get_or_404(db, Invoice, payload.invoice_id, 'Invoice')
    if payload.receivable_id:
        _get_or_404(db, Receivable, payload.receivable_id, 'Receivable')
    if payload.smart_lc_id:
        _get_or_404(db, SmartLC, payload.smart_lc_id, 'Smart LC')
    share_token = token_urlsafe(24)
    bundle = EvidenceBundle(
        business_id=business.id,
        invoice_id=payload.invoice_id,
        receivable_id=payload.receivable_id,
        smart_lc_id=payload.smart_lc_id,
        bundle_type=payload.bundle_type,
        secure_share_token=share_token,
        expires_at=_now() + timedelta(days=payload.expires_in_days),
        payload_json=payload.metadata_json,
        created_by_user_id=user.id,
    )
    db.add(bundle); db.flush()

    items: list[EvidenceBundleItem] = []
    def add_item(item_type: str, title: str, source: str, resource_type: str | None, resource_id: str | None, proof_hash: str | None = None, tx_hash: str | None = None, status: str = 'included'):
        item = EvidenceBundleItem(
            bundle_id=bundle.id,
            item_type=item_type,
            title=title,
            source=source,
            status=status,
            resource_type=resource_type,
            resource_id=resource_id,
            proof_hash=proof_hash,
            polygon_tx_hash=tx_hash,
        )
        db.add(item)
        items.append(item)

    invoice = db.get(Invoice, payload.invoice_id) if payload.invoice_id else None
    receivable = db.get(Receivable, payload.receivable_id) if payload.receivable_id else None
    lc = db.get(SmartLC, payload.smart_lc_id) if payload.smart_lc_id else None
    kyb = db.query(KYBProfile).filter(KYBProfile.business_id == business.id).first()
    latest_score = db.query(TrustScore).filter(TrustScore.business_id == business.id).order_by(TrustScore.created_at.desc()).first()
    latest_bundle = db.query(ProofBundle).filter(ProofBundle.business_id == business.id).order_by(ProofBundle.created_at.desc()).first()

    add_item('invoice', 'Invoice record', 'trade_api', 'invoice', invoice.id if invoice else None, invoice.proof_hash if invoice else None, status='included' if invoice else 'missing')
    add_item('buyer_confirmation', 'Buyer confirmation', 'buyer_inbox', 'invoice', invoice.id if invoice else None, invoice.proof_hash if invoice else None, status='included' if invoice and invoice.status == InvoiceStatus.BUYER_CONFIRMED.value else 'available')
    add_item('kyb', 'KYB profile', 'kyb_provider', 'kyb_profile', kyb.id if kyb else None, status='included' if kyb else 'missing')
    add_item('proof_receipt', 'Polygon proof receipt', 'proof_ledger', 'proof_bundle', latest_bundle.id if latest_bundle else None, latest_bundle.proof_hash if latest_bundle else None, latest_bundle.polygon_tx_hash if latest_bundle else None, status='included' if latest_bundle else 'missing')
    add_item('receivable', 'Receivable record', 'receivable_registry', 'receivable', receivable.id if receivable else None, receivable.proof_hash if receivable else None, receivable.polygon_tx_hash if receivable else None, status='included' if receivable else 'available')
    add_item('smart_lc', 'Smart LC settlement', 'smart_lc_factory', 'smart_lc', lc.id if lc else None, tx_hash=lc.polygon_tx_hash if lc else None, status='included' if lc else 'available')
    add_item('credit_score', 'Trade credit score', 'credit_score_attestation', 'trust_score', latest_score.id if latest_score else None, latest_score.proof_hash if latest_score else None, latest_score.polygon_tx_hash if latest_score else None, status='included' if latest_score else 'available')

    included = sum(1 for i in items if i.status == 'included')
    bundle.completeness_score = int(included / len(items) * 100) if items else 0
    record_audit(db, user.id, 'evidence_bundle.generated', 'evidence_bundle', bundle.id, {'completeness_score': bundle.completeness_score})
    _log_webhook(db, 'evidence_bundle.generated', {'evidence_bundle_id': bundle.id, 'completeness_score': bundle.completeness_score})
    db.commit(); db.refresh(bundle)
    refreshed_items = db.query(EvidenceBundleItem).filter(EvidenceBundleItem.bundle_id == bundle.id).all()
    return EvidenceBundleDetail(bundle=bundle, items=refreshed_items, export_url=f'/api/v1/evidence/bundles/{bundle.id}/export/{bundle.secure_share_token}')


@router.get('/evidence/bundles/{bundle_id}', response_model=EvidenceBundleDetail)
def read_evidence_bundle(
    bundle_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.ADMIN, Role.SME, Role.FINANCIER, Role.BUYER)),
):
    bundle = _get_or_404(db, EvidenceBundle, bundle_id, 'Evidence bundle')
    items = db.query(EvidenceBundleItem).filter(EvidenceBundleItem.bundle_id == bundle.id).order_by(EvidenceBundleItem.created_at.asc()).all()
    return EvidenceBundleDetail(bundle=bundle, items=items, export_url=f'/api/v1/evidence/bundles/{bundle.id}/export/{bundle.secure_share_token}')


@router.get('/risk-rules', response_model=list[RiskRuleRead])
def list_risk_rules(
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.ADMIN, Role.FINANCIER)),
):
    return db.query(RiskRule).order_by(RiskRule.created_at.desc()).limit(200).all()


@router.post('/risk-rules', response_model=RiskRuleRead)
def create_risk_rule(
    payload: RiskRuleCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.ADMIN)),
):
    rule = RiskRule(**payload.model_dump(), created_by_user_id=user.id)
    db.add(rule)
    record_audit(db, user.id, 'risk_rule.created', 'risk_rule', rule.id, payload.model_dump())
    db.commit(); db.refresh(rule)
    return rule


@router.post('/risk-rules/evaluate', response_model=RiskRuleEvaluationResult)
def evaluate_risk_rules(
    payload: RiskRuleEvaluationRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.ADMIN, Role.FINANCIER, Role.DEVELOPER)),
):
    context = payload.context_json
    rules = db.query(RiskRule).filter(RiskRule.is_enabled.is_(True)).all()
    triggered = []
    for rule in rules:
        condition = rule.condition_json or {}
        # Minimal deterministic policy evaluator for enterprise demo/back-end parity.
        field = condition.get('field')
        equals = condition.get('equals')
        min_value = condition.get('min')
        max_value = condition.get('max')
        value = context.get(field) if field else None
        matched = False
        if field and 'equals' in condition:
            matched = value == equals
        if field and min_value is not None:
            matched = value is not None and float(value) >= float(min_value)
        if field and max_value is not None:
            matched = value is not None and float(value) <= float(max_value)
        if not condition and rule.scope in {'kyb', 'settlement', 'proof'}:
            matched = False
        if matched:
            triggered.append({'id': rule.id, 'name': rule.name, 'scope': rule.scope, 'severity': rule.severity, 'action': rule.action})
    decision = 'blocked' if any(r['severity'] == 'critical' for r in triggered) else 'manual_review' if triggered else 'allowed'
    return RiskRuleEvaluationResult(allowed=decision == 'allowed', triggered_rules=triggered, decision=decision)


@router.post('/developer/api-keys', response_model=ApiKeyCreateResponse)
def create_api_key(
    payload: ApiKeyCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.DEVELOPER, Role.ADMIN)),
):
    secret = 'cr_' + payload.environment[:4] + '_' + token_urlsafe(28)
    api_key = ApiKey(
        owner_user_id=user.id,
        name=payload.name,
        key_prefix=secret[:18],
        key_hash=sha256_hex(secret),
        scopes_json=payload.scopes_json,
        environment=payload.environment,
    )
    db.add(api_key)
    record_audit(db, user.id, 'api_key.created', 'api_key', api_key.id, {'name': payload.name, 'environment': payload.environment})
    db.commit(); db.refresh(api_key)
    return ApiKeyCreateResponse(api_key=api_key, secret_key=secret)


@router.get('/developer/api-keys', response_model=list[ApiKeyRead])
def list_api_keys(
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.DEVELOPER, Role.ADMIN)),
):
    q = db.query(ApiKey)
    if user.role == Role.DEVELOPER.value:
        q = q.filter(ApiKey.owner_user_id == user.id)
    return q.order_by(ApiKey.created_at.desc()).limit(100).all()


@router.post('/developer/webhook-endpoints', response_model=WebhookEndpointRead)
def create_webhook_endpoint(
    payload: WebhookEndpointCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.DEVELOPER, Role.ADMIN)),
):
    secret = token_urlsafe(24)
    endpoint = WebhookEndpoint(owner_user_id=user.id, url=payload.url, events_json=payload.events_json, signing_secret_hash=sha256_hex(secret))
    db.add(endpoint)
    record_audit(db, user.id, 'webhook_endpoint.created', 'webhook_endpoint', endpoint.id, {'url': payload.url, 'events': payload.events_json})
    db.commit(); db.refresh(endpoint)
    return endpoint


@router.get('/developer/webhook-deliveries', response_model=list[WebhookDeliveryRead])
def list_webhook_deliveries(
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.DEVELOPER, Role.ADMIN)),
):
    return db.query(WebhookDelivery).order_by(WebhookDelivery.created_at.desc()).limit(200).all()


@router.post('/developer/api-simulations', response_model=ApiSimulationResponse)
def simulate_api_call(
    payload: ApiSimulationRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.DEVELOPER, Role.ADMIN)),
):
    from app.core.config import get_settings

    if get_settings().is_production:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail='API simulations are disabled in production')
    endpoint_map = {
        'anchorProof': ('POST', '/api/v1/proof-ledger/anchor'),
        'createReceivable': ('POST', '/api/v1/trade/receivables'),
        'smartLC': ('POST', '/api/v1/trade/smart-lcs'),
        'score': ('GET', '/api/v1/finance/businesses/{business_id}/score'),
    }
    method, endpoint = endpoint_map.get(payload.endpoint_key, ('POST', '/api/v1/sandbox'))
    response = {'ok': True, 'endpoint_key': payload.endpoint_key, 'simulated': True, 'polygon_network': 'amoy'}
    usage = ApiUsageLog(user_id=user.id, endpoint=endpoint, method=method, status_code=200, request_json=payload.request_json, response_json=response, latency_ms=12)
    db.add(usage)
    delivery = _log_webhook(db, f'api_simulation.{payload.endpoint_key}', response)
    record_audit(db, user.id, 'api_simulation.executed', 'api_usage_log', usage.id, {'endpoint': endpoint})
    db.commit(); db.refresh(delivery)
    return ApiSimulationResponse(endpoint=endpoint, method=method, request_json=payload.request_json, response_json=response, webhook_delivery_id=delivery.id)


@router.get('/developer/endpoints')
def api_explorer_endpoints(user: User = Depends(require_roles(Role.DEVELOPER, Role.ADMIN, Role.FINANCIER))):
    return [
        {'key': 'anchorProof', 'method': 'POST', 'path': '/api/v1/proof-ledger/anchor', 'description': 'Anchor proof bundle hash on Polygon'},
        {'key': 'createReceivable', 'method': 'POST', 'path': '/api/v1/trade/receivables', 'description': 'Create tokenized receivable from buyer-confirmed invoice'},
        {'key': 'smartLC', 'method': 'POST', 'path': '/api/v1/trade/smart-lcs', 'description': 'Create Smart LC escrow'},
        {'key': 'score', 'method': 'GET', 'path': '/api/v1/finance/businesses/{business_id}/score', 'description': 'Read trade credit score'},
    ]


@router.get('/permissions/matrix', response_model=PermissionMatrixResponse)
def permission_matrix(user: User = Depends(require_roles(Role.ADMIN, Role.DEVELOPER, Role.FINANCIER))):
    roles = ['sme', 'buyer', 'financier', 'admin', 'developer', 'auditor']
    capabilities = [
        {'capability': 'create_invoice', 'sme': True, 'buyer': False, 'financier': False, 'admin': True, 'developer': 'api', 'auditor': False},
        {'capability': 'confirm_invoice', 'sme': False, 'buyer': True, 'financier': False, 'admin': True, 'developer': 'webhook', 'auditor': False},
        {'capability': 'verify_delivery', 'sme': 'submit', 'buyer': 'confirm', 'financier': 'view', 'admin': 'override', 'developer': 'api', 'auditor': 'view'},
        {'capability': 'fund_receivable', 'sme': 'request', 'buyer': False, 'financier': True, 'admin': True, 'developer': 'api', 'auditor': False},
        {'capability': 'release_settlement', 'sme': 'view', 'buyer': 'approve', 'financier': 'fund', 'admin': 'freeze', 'developer': 'api', 'auditor': 'view'},
        {'capability': 'manage_kyb', 'sme': 'submit', 'buyer': 'view', 'financier': 'view', 'admin': True, 'developer': 'webhook', 'auditor': 'view'},
        {'capability': 'audit_evidence', 'sme': 'view', 'buyer': 'view', 'financier': 'view', 'admin': True, 'developer': 'read_only_api', 'auditor': True},
    ]
    return PermissionMatrixResponse(roles=roles, capabilities=capabilities)


@router.post('/smart-lcs/{lc_id}/fund')
def fund_smart_lc(
    lc_id: str,
    payload: SmartLCActionRequest | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.BUYER, Role.FINANCIER, Role.ADMIN)),
):
    lc = _get_or_404(db, SmartLC, lc_id, 'Smart LC')
    before = {'status': lc.status}
    lc.status = SmartLCStatus.FUNDED.value
    try:
        tx_hash, on_chain = publish_tx(f'fund:{lc.id}:{lc.amount}')
    except Exception:
        tx_hash, on_chain = None, False
    lc.polygon_tx_hash = tx_hash if on_chain else None
    db.add(BlockchainOutbox(action='SMART_LC_FUNDED', payload_json={'smart_lc_id': lc.id, 'amount': float(lc.amount), 'on_chain': on_chain}, status='sent' if on_chain else 'pending', tx_hash=lc.polygon_tx_hash))
    create_proof_bundle(db, lc.seller_business_id, 'SMART_LC_FUNDED', {'smart_lc_id': lc.id, 'tx_hash': lc.polygon_tx_hash, 'on_chain': on_chain}, order_id=lc.order_id)
    record_audit(db, user.id, 'smart_lc.funded', 'smart_lc', lc.id, {'before': before, 'after': {'status': lc.status}, 'reason': payload.reason if payload else None})
    _log_webhook(db, 'smart_lc.funded', {'smart_lc_id': lc.id, 'tx_hash': lc.polygon_tx_hash, 'on_chain': on_chain})
    db.commit(); db.refresh(lc)
    return {'smart_lc': lc, 'on_chain': on_chain, 'explorer_url': explorer_tx_url(lc.polygon_tx_hash, on_chain=on_chain)}


@router.post('/smart-lcs/{lc_id}/release')
def release_smart_lc(
    lc_id: str,
    payload: SmartLCActionRequest | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.BUYER, Role.FINANCIER, Role.ADMIN)),
):
    lc = _get_or_404(db, SmartLC, lc_id, 'Smart LC')
    if lc.status == SmartLCStatus.DISPUTED.value:
        raise HTTPException(400, 'Cannot release a disputed Smart LC')
    before = {'status': lc.status}
    lc.status = SmartLCStatus.RELEASED.value
    try:
        tx_hash, on_chain = publish_tx(f'release:{lc.id}:{lc.amount}')
    except Exception:
        tx_hash, on_chain = None, False
    lc.polygon_tx_hash = tx_hash if on_chain else None
    order = db.get(Order, lc.order_id)
    if order:
        order.status = OrderStatus.CLOSED.value
    db.add(BlockchainOutbox(action='SMART_LC_RELEASED', payload_json={'smart_lc_id': lc.id, 'amount': float(lc.amount), 'on_chain': on_chain}, status='sent' if on_chain else 'pending', tx_hash=lc.polygon_tx_hash))
    create_proof_bundle(db, lc.seller_business_id, 'SMART_LC_RELEASED', {'smart_lc_id': lc.id, 'tx_hash': lc.polygon_tx_hash, 'on_chain': on_chain}, order_id=lc.order_id)
    record_audit(db, user.id, 'smart_lc.released', 'smart_lc', lc.id, {'before': before, 'after': {'status': lc.status}, 'reason': payload.reason if payload else None})
    _log_webhook(db, 'smart_lc.released', {'smart_lc_id': lc.id, 'tx_hash': lc.polygon_tx_hash, 'on_chain': on_chain})
    db.commit(); db.refresh(lc)
    return {'smart_lc': lc, 'on_chain': on_chain, 'explorer_url': explorer_tx_url(lc.polygon_tx_hash, on_chain=on_chain)}


@router.post('/smart-lcs/{lc_id}/dispute')
def dispute_smart_lc(
    lc_id: str,
    payload: SmartLCActionRequest | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.BUYER, Role.SME, Role.ADMIN)),
):
    lc = _get_or_404(db, SmartLC, lc_id, 'Smart LC')
    before = {'status': lc.status}
    lc.status = SmartLCStatus.DISPUTED.value
    order = db.get(Order, lc.order_id)
    if order:
        order.status = OrderStatus.DISPUTED.value
    record_audit(db, user.id, 'smart_lc.disputed', 'smart_lc', lc.id, {'before': before, 'after': {'status': lc.status}, 'reason': payload.reason if payload else None})
    _log_webhook(db, 'smart_lc.disputed', {'smart_lc_id': lc.id})
    db.commit(); db.refresh(lc)
    return lc


@router.post('/smart-lcs/{lc_id}/refund')
def refund_smart_lc(
    lc_id: str,
    payload: SmartLCActionRequest | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.ADMIN, Role.BUYER)),
):
    lc = _get_or_404(db, SmartLC, lc_id, 'Smart LC')
    before = {'status': lc.status}
    lc.status = SmartLCStatus.REFUNDED.value
    try:
        tx_hash, on_chain = publish_tx(f'refund:{lc.id}:{lc.amount}')
    except Exception:
        tx_hash, on_chain = None, False
    lc.polygon_tx_hash = tx_hash if on_chain else None
    db.add(BlockchainOutbox(action='SMART_LC_REFUNDED', payload_json={'smart_lc_id': lc.id, 'amount': float(lc.amount), 'on_chain': on_chain}, status='sent' if on_chain else 'pending', tx_hash=lc.polygon_tx_hash))
    create_proof_bundle(db, lc.seller_business_id, 'SMART_LC_REFUNDED', {'smart_lc_id': lc.id, 'tx_hash': lc.polygon_tx_hash, 'on_chain': on_chain}, order_id=lc.order_id)
    record_audit(db, user.id, 'smart_lc.refunded', 'smart_lc', lc.id, {'before': before, 'after': {'status': lc.status}, 'reason': payload.reason if payload else None})
    _log_webhook(db, 'smart_lc.refunded', {'smart_lc_id': lc.id, 'tx_hash': lc.polygon_tx_hash, 'on_chain': on_chain})
    db.commit(); db.refresh(lc)
    return {'smart_lc': lc, 'on_chain': on_chain, 'explorer_url': explorer_tx_url(lc.polygon_tx_hash, on_chain=on_chain)}


@router.post('/finance/businesses/{business_id}/score/attest')
def attest_trade_credit_score(
    business_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.ADMIN, Role.FINANCIER, Role.SME)),
):
    _get_or_404(db, Business, business_id, 'Business')
    score = db.query(TrustScore).filter(TrustScore.business_id == business_id).order_by(TrustScore.created_at.desc()).first()
    if not score:
        score = calculate_trade_credit_score(db, business_id)
        db.flush()
    tx_hash, on_chain = publish_tx(f'score:{score.id}:{score.score}', proof_hash=score.proof_hash)
    score.polygon_tx_hash = tx_hash if on_chain else None
    db.add(BlockchainOutbox(action='CREDIT_SCORE_ATTESTED', payload_json={'trust_score_id': score.id, 'business_id': business_id, 'score': score.score, 'on_chain': on_chain}, status='sent' if on_chain else 'pending', tx_hash=score.polygon_tx_hash))
    create_proof_bundle(db, business_id, 'CREDIT_SCORE_ATTESTED', {'trust_score_id': score.id, 'score': score.score, 'tx_hash': score.polygon_tx_hash, 'on_chain': on_chain})
    record_audit(db, user.id, 'credit_score.attested', 'trust_score', score.id, {'score': score.score, 'tx_hash': score.polygon_tx_hash, 'on_chain': on_chain})
    _log_webhook(db, 'credit_score.attested', {'trust_score_id': score.id, 'score': score.score, 'tx_hash': score.polygon_tx_hash, 'on_chain': on_chain})
    db.commit(); db.refresh(score)
    return {'trust_score': score, 'on_chain': on_chain, 'explorer_url': explorer_tx_url(score.polygon_tx_hash, on_chain=on_chain)}
