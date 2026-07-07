from app.schemas.common import ORMModel

class TrustScoreRead(ORMModel):
    business_id: str
    score: int
    grade: str
    factors_json: dict
    proof_hash: str | None
    polygon_tx_hash: str | None

class FinanceReadinessRead(ORMModel):
    business_id: str
    verified_invoice_value: float
    completed_transactions: int
    dispute_rate: float
    recommended_limit: float
    report_json: dict
