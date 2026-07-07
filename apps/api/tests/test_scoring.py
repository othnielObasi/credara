from app.services.proofs import score_delivery_proof
from app.models.trade import DeliveryProof

def test_delivery_confidence_high_with_otp_gps_buyer_confirmation():
    proof = DeliveryProof(order_id='o1', submitted_by_user_id='u1', evidence_uri='s3://proof.jpg', otp_code_hash='0xabc', gps_lat='1', gps_lng='2', metadata_json={'buyer_confirmed': True})
    assert score_delivery_proof(proof) >= 85
