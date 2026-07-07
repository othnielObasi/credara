from datetime import datetime
from uuid import uuid4
from sqlalchemy import DateTime, ForeignKey, Integer, JSON, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base

class TrustScore(Base):
    __tablename__ = 'trust_scores'
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    business_id: Mapped[str] = mapped_column(ForeignKey('businesses.id'), index=True)
    score: Mapped[int] = mapped_column(Integer)
    grade: Mapped[str] = mapped_column(String(5))
    factors_json: Mapped[dict] = mapped_column(JSON, default=dict)
    proof_hash: Mapped[str | None] = mapped_column(String(80))
    polygon_tx_hash: Mapped[str | None] = mapped_column(String(120))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class FinanceReadinessReport(Base):
    __tablename__ = 'finance_readiness_reports'
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    business_id: Mapped[str] = mapped_column(ForeignKey('businesses.id'), index=True)
    verified_invoice_value: Mapped[float] = mapped_column(Numeric(18, 2), default=0)
    completed_transactions: Mapped[int] = mapped_column(Integer, default=0)
    dispute_rate: Mapped[float] = mapped_column(Numeric(5, 4), default=0)
    recommended_limit: Mapped[float] = mapped_column(Numeric(18, 2), default=0)
    report_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class FinancingOffer(Base):
    __tablename__ = 'financing_offers'
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    financier_user_id: Mapped[str] = mapped_column(ForeignKey('users.id'))
    receivable_id: Mapped[str] = mapped_column(ForeignKey('receivables.id'), index=True)
    advance_rate_bps: Mapped[int] = mapped_column(Integer)
    fee_bps: Mapped[int] = mapped_column(Integer)
    offer_amount: Mapped[float] = mapped_column(Numeric(18, 2))
    status: Mapped[str] = mapped_column(String(50), default='offered')
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
