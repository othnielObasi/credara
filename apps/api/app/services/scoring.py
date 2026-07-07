from sqlalchemy.orm import Session
from app.core.hashing import sha256_hex
from app.models.finance import FinanceReadinessReport, TrustScore
from app.models.trade import DeliveryProof, Invoice, Order, Receivable
from app.models.enums import InvoiceStatus, OrderStatus


def calculate_trade_credit_score(db: Session, business_id: str) -> TrustScore:
    invoices = db.query(Invoice).filter(Invoice.seller_business_id == business_id).all()
    orders = db.query(Order).filter(Order.seller_business_id == business_id).all()
    proofs = db.query(DeliveryProof).join(Order, DeliveryProof.order_id == Order.id).filter(Order.seller_business_id == business_id).all()
    receivables = db.query(Receivable).filter(Receivable.seller_business_id == business_id).all()

    completed_orders = sum(1 for o in orders if o.status in {OrderStatus.DELIVERED.value, OrderStatus.CLOSED.value})
    disputed_orders = sum(1 for o in orders if o.status == OrderStatus.DISPUTED.value)
    confirmed_invoices = sum(1 for i in invoices if i.status in {InvoiceStatus.BUYER_CONFIRMED.value, InvoiceStatus.PAID.value})
    avg_proof_conf = int(sum(p.confidence_score for p in proofs) / len(proofs)) if proofs else 0
    receivable_count = len(receivables)

    score = 40
    score += min(completed_orders * 4, 20)
    score += min(confirmed_invoices * 3, 15)
    score += min(avg_proof_conf // 5, 15)
    score += min(receivable_count * 2, 5)
    score -= min(disputed_orders * 7, 20)
    score = max(0, min(100, score))
    grade = 'A' if score >= 85 else 'B' if score >= 70 else 'C' if score >= 55 else 'D'
    factors = {
        'completed_orders': completed_orders,
        'disputed_orders': disputed_orders,
        'confirmed_invoices': confirmed_invoices,
        'average_delivery_proof_confidence': avg_proof_conf,
        'receivable_count': receivable_count,
    }
    proof_hash = sha256_hex({'business_id': business_id, 'score': score, 'grade': grade, 'factors': factors})
    trust = TrustScore(business_id=business_id, score=score, grade=grade, factors_json=factors, proof_hash=proof_hash)
    db.add(trust)
    return trust


def build_finance_readiness_report(db: Session, business_id: str) -> FinanceReadinessReport:
    invoices = db.query(Invoice).filter(Invoice.seller_business_id == business_id).all()
    orders = db.query(Order).filter(Order.seller_business_id == business_id).all()
    verified_value = sum(float(i.amount) for i in invoices if i.status in {InvoiceStatus.BUYER_CONFIRMED.value, InvoiceStatus.PAID.value})
    completed = sum(1 for o in orders if o.status in {OrderStatus.DELIVERED.value, OrderStatus.CLOSED.value})
    disputed = sum(1 for o in orders if o.status == OrderStatus.DISPUTED.value)
    dispute_rate = disputed / len(orders) if orders else 0
    recommended_limit = max(0, verified_value * (0.3 if dispute_rate < 0.05 else 0.15))
    report = FinanceReadinessReport(
        business_id=business_id,
        verified_invoice_value=verified_value,
        completed_transactions=completed,
        dispute_rate=dispute_rate,
        recommended_limit=recommended_limit,
        report_json={
            'summary': 'Finance readiness is based on buyer-confirmed invoices, completed delivery proofs, dispute rate and receivable performance.',
            'risk_level': 'low' if dispute_rate < 0.05 and verified_value > 0 else 'medium' if verified_value > 0 else 'insufficient_data',
        },
    )
    db.add(report)
    return report
