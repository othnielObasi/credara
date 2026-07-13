from sqlalchemy.orm import Session
from app.core.hashing import sha256_hex
from app.models.audit import BlockchainOutbox
from app.models.trade import DeliveryProof, Invoice, Order, ProofBundle
from app.models.enums import ProofStatus
from app.services.polygon import publish_tx


def score_delivery_proof(proof: DeliveryProof) -> int:
    score = 20
    if proof.evidence_uri:
        score += 20
    if proof.otp_code_hash:
        score += 30
    if proof.gps_lat and proof.gps_lng:
        score += 15
    if proof.metadata_json.get('buyer_confirmed') is True:
        score += 25
    if proof.metadata_json.get('logistics_tracking_status') == 'delivered':
        score += 20
    return min(score, 100)


def build_invoice_hash(invoice: Invoice) -> str:
    return sha256_hex({
        'type': 'invoice',
        'invoice_id': invoice.id,
        'order_id': invoice.order_id,
        'seller_business_id': invoice.seller_business_id,
        'buyer_name': invoice.buyer_name,
        'invoice_number': invoice.invoice_number,
        'amount': invoice.amount,
        'currency': invoice.currency,
        'due_date': invoice.due_date,
    })


def build_delivery_hash(proof: DeliveryProof) -> str:
    return sha256_hex({
        'type': 'delivery_proof',
        'delivery_proof_id': proof.id,
        'order_id': proof.order_id,
        'evidence_uri': proof.evidence_uri,
        'otp_code_hash': proof.otp_code_hash,
        'gps_lat': proof.gps_lat,
        'gps_lng': proof.gps_lng,
        'metadata': proof.metadata_json,
    })


def create_proof_bundle(db: Session, business_id: str, bundle_type: str, payload: dict, order_id: str | None = None, invoice_id: str | None = None, delivery_proof_id: str | None = None) -> ProofBundle:
    proof_hash = sha256_hex({'type': bundle_type, 'payload': payload})
    # Anchored synchronously (same pattern as the Smart LC handlers in
    # enterprise.py) rather than left pending for a background poller -
    # there is no long-running worker process in the serverless deployment.
    tx_hash, _on_chain = publish_tx(f'anchor:{bundle_type}:{proof_hash}', proof_hash=proof_hash)
    bundle = ProofBundle(
        business_id=business_id,
        order_id=order_id,
        invoice_id=invoice_id,
        delivery_proof_id=delivery_proof_id,
        bundle_type=bundle_type,
        payload_json=payload,
        proof_hash=proof_hash,
        polygon_tx_hash=tx_hash,
        status=ProofStatus.ANCHORED.value,
    )
    db.add(bundle)
    db.add(BlockchainOutbox(action='ANCHOR_PROOF', payload_json={'proof_hash': proof_hash, 'bundle_type': bundle_type, 'business_id': business_id}, status='sent', tx_hash=tx_hash))
    return bundle
