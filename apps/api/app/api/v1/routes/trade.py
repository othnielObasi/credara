from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session
from app.core.config import get_settings
from app.core.database import get_db
from app.core.hashing import sha256_hex
from app.core.idempotency import assert_idempotent
from app.core.security import Role, require_roles
from app.models.business import Business
from app.models.enums import InvoiceStatus, OrderStatus, ProofStatus, ReceivableStatus, SmartLCStatus
from app.models.identity import User
from app.models.trade import DeliveryProof, Invoice, Order, Receivable, SmartLC
from app.schemas.trade import DeliveryProofCreate, DeliveryProofRead, InvoiceBuyerConfirmRequest, InvoiceCreate, InvoiceRead, OrderConfirmRequest, OrderCreate, OrderRead, ReceivableCreate, ReceivableRead, SmartLCCreate, SmartLCRead
from app.services.audit import record_audit
from app.services.polygon import ChainUnavailableError
from app.services.proofs import build_delivery_hash, build_invoice_hash, create_proof_bundle, score_delivery_proof
from app.services.smart_lc_chain import create_smart_lc_on_chain

router = APIRouter()

@router.get('/orders', response_model=list[OrderRead])
def list_orders(
    seller_business_id: str | None = None,
    buyer_business_id: str | None = None,
    pending_buyer: bool = False,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.SME, Role.BUYER, Role.FINANCIER, Role.ADMIN)),
):
    q = db.query(Order)
    if seller_business_id:
        _require_owns_business(db, user, seller_business_id)
        q = q.filter(Order.seller_business_id == seller_business_id)
    elif buyer_business_id:
        _require_owns_buyer_business(db, user, buyer_business_id)
        q = q.filter(Order.buyer_business_id == buyer_business_id)
    elif pending_buyer and user.role in {Role.BUYER.value, Role.ADMIN.value}:
        owned_ids = [b.id for b in db.query(Business).filter(Business.owner_user_id == user.id).all()]
        if user.role == Role.ADMIN.value:
            q = q.filter(Order.buyer_business_id.is_(None))
        elif owned_ids:
            q = q.filter(or_(Order.buyer_business_id.in_(owned_ids), Order.buyer_business_id.is_(None)))
        else:
            q = q.filter(Order.buyer_business_id.is_(None))
    elif user.role == Role.SME.value:
        owned_ids = [b.id for b in db.query(Business).filter(Business.owner_user_id == user.id).all()]
        q = q.filter(Order.seller_business_id.in_(owned_ids)) if owned_ids else q.filter(False)
    elif user.role == Role.BUYER.value:
        owned_ids = [b.id for b in db.query(Business).filter(Business.owner_user_id == user.id).all()]
        q = q.filter(Order.buyer_business_id.in_(owned_ids)) if owned_ids else q.filter(False)
    return q.order_by(Order.created_at.desc()).limit(100).all()

@router.get('/invoices', response_model=list[InvoiceRead])
def list_invoices(
    seller_business_id: str | None = None,
    buyer_business_id: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.SME, Role.BUYER, Role.FINANCIER, Role.ADMIN)),
):
    q = db.query(Invoice)
    if seller_business_id:
        _require_owns_business(db, user, seller_business_id)
        q = q.filter(Invoice.seller_business_id == seller_business_id)
    elif buyer_business_id:
        _require_owns_buyer_business(db, user, buyer_business_id)
        order_ids = [o.id for o in db.query(Order).filter(Order.buyer_business_id == buyer_business_id).all()]
        q = q.filter(Invoice.order_id.in_(order_ids)) if order_ids else q.filter(False)
    elif user.role == Role.SME.value:
        owned_ids = [b.id for b in db.query(Business).filter(Business.owner_user_id == user.id).all()]
        q = q.filter(Invoice.seller_business_id.in_(owned_ids)) if owned_ids else q.filter(False)
    elif user.role == Role.BUYER.value:
        owned_ids = [b.id for b in db.query(Business).filter(Business.owner_user_id == user.id).all()]
        if owned_ids:
            order_ids = [o.id for o in db.query(Order).filter(Order.buyer_business_id.in_(owned_ids)).all()]
            q = q.filter(Invoice.order_id.in_(order_ids)) if order_ids else q.filter(False)
        else:
            q = q.filter(False)
    return q.order_by(Invoice.created_at.desc()).limit(100).all()

@router.get('/delivery-proofs', response_model=list[DeliveryProofRead])
def list_delivery_proofs(
    order_id: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.SME, Role.BUYER, Role.FINANCIER, Role.ADMIN)),
):
    q = db.query(DeliveryProof)
    if order_id:
        order = db.get(Order, order_id)
        if not order:
            raise HTTPException(404, 'Order not found')
        if user.role == Role.SME.value:
            _require_owns_business(db, user, order.seller_business_id)
        elif user.role == Role.BUYER.value and order.buyer_business_id:
            _require_owns_buyer_business(db, user, order.buyer_business_id)
        q = q.filter(DeliveryProof.order_id == order_id)
    elif user.role == Role.SME.value:
        owned_ids = [b.id for b in db.query(Business).filter(Business.owner_user_id == user.id).all()]
        if not owned_ids:
            return []
        order_ids = [o.id for o in db.query(Order).filter(Order.seller_business_id.in_(owned_ids)).all()]
        q = q.filter(DeliveryProof.order_id.in_(order_ids)) if order_ids else q.filter(False)
    return q.order_by(DeliveryProof.created_at.desc()).limit(100).all()

@router.get('/receivables', response_model=list[ReceivableRead])
def list_receivables(
    seller_business_id: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.SME, Role.BUYER, Role.FINANCIER, Role.ADMIN)),
):
    q = db.query(Receivable)
    if seller_business_id:
        _require_owns_business(db, user, seller_business_id)
        q = q.filter(Receivable.seller_business_id == seller_business_id)
    elif user.role == Role.SME.value:
        owned_ids = [b.id for b in db.query(Business).filter(Business.owner_user_id == user.id).all()]
        q = q.filter(Receivable.seller_business_id.in_(owned_ids)) if owned_ids else q.filter(False)
    return q.order_by(Receivable.created_at.desc()).limit(100).all()

def _require_owns_business(db: Session, user: User, business_id: str) -> None:
    # SMEs may only act on their own business; admins act on any.
    if user.role == Role.ADMIN.value:
        return
    business = db.get(Business, business_id)
    if not business or business.owner_user_id != user.id:
        raise HTTPException(403, 'You do not have access to this business')

def _require_owns_buyer_business(db: Session, user: User, buyer_business_id: str) -> None:
    # Buyers may only act as a business they own; admins act on any.
    if user.role == Role.ADMIN.value:
        return
    business = db.get(Business, buyer_business_id)
    if not business or business.owner_user_id != user.id:
        raise HTTPException(403, 'You do not have access to this buyer business')

@router.post('/orders', response_model=OrderRead)
def create_order(payload: OrderCreate, idempotency_key: str | None = Header(None), db: Session = Depends(get_db), user: User = Depends(require_roles(Role.SME, Role.ADMIN))):
    assert_idempotent(db, idempotency_key, 'create_order')
    _require_owns_business(db, user, payload.seller_business_id)
    order = Order(**payload.model_dump())
    db.add(order); db.flush()
    record_audit(db, user.id, 'order.created', 'order', order.id)
    db.commit(); db.refresh(order)
    return order

@router.post('/orders/{order_id}/confirm', response_model=OrderRead)
def confirm_order(order_id: str, payload: OrderConfirmRequest, db: Session = Depends(get_db), user: User = Depends(require_roles(Role.BUYER, Role.ADMIN))):
    order = db.get(Order, order_id)
    if not order: raise HTTPException(404, 'Order not found')
    _require_owns_buyer_business(db, user, payload.buyer_business_id)
    if order.buyer_business_id and order.buyer_business_id != payload.buyer_business_id:
        raise HTTPException(403, 'This order is already bound to a different buyer business')
    order.buyer_business_id = payload.buyer_business_id
    order.status = OrderStatus.CONFIRMED.value
    record_audit(db, user.id, 'order.confirmed', 'order', order.id)
    db.commit(); db.refresh(order)
    return order

@router.post('/invoices', response_model=InvoiceRead)
def create_invoice(payload: InvoiceCreate, db: Session = Depends(get_db), user: User = Depends(require_roles(Role.SME, Role.ADMIN))):
    order = db.get(Order, payload.order_id)
    if not order: raise HTTPException(404, 'Order not found')
    _require_owns_business(db, user, order.seller_business_id)
    invoice = Invoice(order_id=order.id, seller_business_id=order.seller_business_id, buyer_name=order.buyer_name, invoice_number=payload.invoice_number, amount=payload.amount, due_date=payload.due_date, currency=order.currency)
    db.add(invoice); db.flush()
    invoice.proof_hash = build_invoice_hash(invoice)
    create_proof_bundle(db, order.seller_business_id, 'INVOICE_CREATED', {'invoice_id': invoice.id, 'proof_hash': invoice.proof_hash}, order_id=order.id, invoice_id=invoice.id)
    record_audit(db, user.id, 'invoice.created', 'invoice', invoice.id)
    db.commit(); db.refresh(invoice)
    return invoice

@router.post('/invoices/{invoice_id}/buyer-confirm', response_model=InvoiceRead)
def buyer_confirm_invoice(invoice_id: str, payload: InvoiceBuyerConfirmRequest, db: Session = Depends(get_db), user: User = Depends(require_roles(Role.BUYER, Role.ADMIN))):
    invoice = db.get(Invoice, invoice_id)
    if not invoice: raise HTTPException(404, 'Invoice not found')
    _require_owns_buyer_business(db, user, payload.buyer_business_id)
    order = db.get(Order, invoice.order_id)
    if not order or order.buyer_business_id != payload.buyer_business_id:
        raise HTTPException(403, 'This buyer business is not bound to this invoice\'s order')
    invoice.status = InvoiceStatus.BUYER_CONFIRMED.value
    create_proof_bundle(db, invoice.seller_business_id, 'INVOICE_BUYER_CONFIRMED', {'invoice_id': invoice.id, 'status': invoice.status, 'proof_hash': invoice.proof_hash}, order_id=invoice.order_id, invoice_id=invoice.id)
    record_audit(db, user.id, 'invoice.buyer_confirmed', 'invoice', invoice.id)
    db.commit(); db.refresh(invoice)
    return invoice

@router.post('/delivery-proofs', response_model=DeliveryProofRead)
def submit_delivery_proof(payload: DeliveryProofCreate, db: Session = Depends(get_db), user: User = Depends(require_roles(Role.SME, Role.ADMIN))):
    order = db.get(Order, payload.order_id)
    if not order: raise HTTPException(404, 'Order not found')
    _require_owns_business(db, user, order.seller_business_id)
    otp_hash = sha256_hex(payload.otp_code) if payload.otp_code else None
    proof = DeliveryProof(order_id=order.id, submitted_by_user_id=user.id, evidence_uri=payload.evidence_uri, otp_code_hash=otp_hash, gps_lat=payload.gps_lat, gps_lng=payload.gps_lng, metadata_json=payload.metadata_json)
    db.add(proof); db.flush()
    proof.confidence_score = score_delivery_proof(proof)
    proof.proof_hash = build_delivery_hash(proof)
    if proof.confidence_score >= 70:
        proof.status = ProofStatus.VERIFIED.value
        order.status = OrderStatus.DELIVERED.value
    create_proof_bundle(db, order.seller_business_id, 'DELIVERY_PROOF_SUBMITTED', {'delivery_proof_id': proof.id, 'confidence_score': proof.confidence_score, 'proof_hash': proof.proof_hash}, order_id=order.id, delivery_proof_id=proof.id)
    record_audit(db, user.id, 'delivery_proof.submitted', 'delivery_proof', proof.id)
    db.commit(); db.refresh(proof)
    return proof

@router.post('/receivables', response_model=ReceivableRead)
def create_receivable(payload: ReceivableCreate, db: Session = Depends(get_db), user: User = Depends(require_roles(Role.SME, Role.ADMIN))):
    invoice = db.get(Invoice, payload.invoice_id)
    if not invoice: raise HTTPException(404, 'Invoice not found')
    _require_owns_business(db, user, invoice.seller_business_id)
    if invoice.status != InvoiceStatus.BUYER_CONFIRMED.value:
        raise HTTPException(400, 'Invoice must be buyer-confirmed before receivable creation')
    receivable = Receivable(invoice_id=invoice.id, seller_business_id=invoice.seller_business_id, debtor_name=invoice.buyer_name, face_value=invoice.amount, currency=invoice.currency, maturity_date=invoice.due_date, proof_hash=invoice.proof_hash or build_invoice_hash(invoice), status=ReceivableStatus.CREATED.value)
    db.add(receivable); db.flush()
    create_proof_bundle(db, invoice.seller_business_id, 'RECEIVABLE_CREATED', {'receivable_id': receivable.id, 'invoice_id': invoice.id, 'proof_hash': receivable.proof_hash}, order_id=invoice.order_id, invoice_id=invoice.id)
    record_audit(db, user.id, 'receivable.created', 'receivable', receivable.id)
    db.commit(); db.refresh(receivable)
    return receivable

@router.get('/smart-lcs', response_model=list[SmartLCRead])
def list_smart_lcs(
    seller_business_id: str | None = None,
    order_id: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.SME, Role.BUYER, Role.FINANCIER, Role.ADMIN)),
):
    q = db.query(SmartLC)
    if order_id:
        q = q.filter(SmartLC.order_id == order_id)
    if seller_business_id:
        if user.role == Role.SME.value:
            _require_owns_business(db, user, seller_business_id)
        q = q.filter(SmartLC.seller_business_id == seller_business_id)
    elif user.role == Role.SME.value:
        owned_ids = [b.id for b in db.query(Business).filter(Business.owner_user_id == user.id).all()]
        q = q.filter(SmartLC.seller_business_id.in_(owned_ids)) if owned_ids else q.filter(False)
    elif user.role == Role.BUYER.value:
        owned_ids = [b.id for b in db.query(Business).filter(Business.owner_user_id == user.id).all()]
        if owned_ids:
            order_ids = [o.id for o in db.query(Order).filter(Order.buyer_business_id.in_(owned_ids)).all()]
            q = q.filter(SmartLC.order_id.in_(order_ids)) if order_ids else q.filter(False)
        else:
            q = q.filter(False)
    return q.order_by(SmartLC.created_at.desc()).limit(50).all()

@router.post('/smart-lcs', response_model=SmartLCRead)
def create_smart_lc(payload: SmartLCCreate, db: Session = Depends(get_db), user: User = Depends(require_roles(Role.BUYER, Role.FINANCIER, Role.ADMIN))):
    order = db.get(Order, payload.order_id)
    if not order: raise HTTPException(404, 'Order not found')
    if user.role == Role.BUYER.value:
        # Financiers intentionally keep marketplace-wide access to fund any
        # verified order; only the buyer side is scoped to their own business.
        business = db.get(Business, order.buyer_business_id) if order.buyer_business_id else None
        if not business or business.owner_user_id != user.id:
            raise HTTPException(403, 'You do not have access to this order')
    lc = SmartLC(order_id=order.id, seller_business_id=order.seller_business_id, buyer_name=order.buyer_name, amount=payload.amount, currency=payload.currency, status=SmartLCStatus.CREATED.value)
    db.add(lc); db.flush()
    order_proof_hash = sha256_hex({'smart_lc_id': lc.id, 'order_id': order.id, 'amount': payload.amount})
    settings = get_settings()
    try:
        chain = create_smart_lc_on_chain(order_proof_hash=order_proof_hash, amount=payload.amount)
        lc.contract_address = chain['contract_address']
        lc.polygon_tx_hash = chain['tx_hash']
    except ChainUnavailableError as exc:
        # Off-chain create is fine for local/demo; fail closed only when chain env is expected.
        if settings.smart_lc_factory_address and not settings.permits_simulated_chain:
            raise HTTPException(503, f'Smart LC on-chain create failed: {exc}') from exc
    except Exception as exc:
        if settings.smart_lc_factory_address and not settings.permits_simulated_chain:
            raise HTTPException(503, f'Smart LC on-chain create failed: {exc}') from exc
    create_proof_bundle(
        db,
        order.seller_business_id,
        'SMART_LC_CREATED',
        {
            'smart_lc_id': lc.id,
            'order_id': order.id,
            'amount': payload.amount,
            'contract_address': lc.contract_address,
            'tx_hash': lc.polygon_tx_hash,
            'on_chain': bool(lc.contract_address),
        },
        order_id=order.id,
    )
    record_audit(db, user.id, 'smart_lc.created', 'smart_lc', lc.id, {'contract_address': lc.contract_address, 'tx_hash': lc.polygon_tx_hash})
    db.commit(); db.refresh(lc)
    return lc
