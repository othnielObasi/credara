from datetime import datetime
from uuid import uuid4
from sqlalchemy import DateTime, ForeignKey, Integer, JSON, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base
from app.models.enums import InvoiceStatus, OrderStatus, ProofStatus, ReceivableStatus, SmartLCStatus

class Order(Base):
    __tablename__ = 'orders'
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    seller_business_id: Mapped[str] = mapped_column(ForeignKey('businesses.id'), index=True)
    buyer_business_id: Mapped[str | None] = mapped_column(ForeignKey('businesses.id'), index=True)
    buyer_name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    currency: Mapped[str] = mapped_column(String(10), default='USDC')
    total_amount: Mapped[float] = mapped_column(Numeric(18, 2))
    status: Mapped[str] = mapped_column(String(50), default=OrderStatus.DRAFT.value)
    expected_delivery_date: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Invoice(Base):
    __tablename__ = 'invoices'
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    order_id: Mapped[str] = mapped_column(ForeignKey('orders.id'), index=True)
    seller_business_id: Mapped[str] = mapped_column(ForeignKey('businesses.id'), index=True)
    buyer_name: Mapped[str] = mapped_column(String(255))
    invoice_number: Mapped[str] = mapped_column(String(120), index=True)
    currency: Mapped[str] = mapped_column(String(10), default='USDC')
    amount: Mapped[float] = mapped_column(Numeric(18, 2))
    due_date: Mapped[datetime]
    status: Mapped[str] = mapped_column(String(50), default=InvoiceStatus.ISSUED.value)
    proof_hash: Mapped[str | None] = mapped_column(String(80))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class DeliveryProof(Base):
    __tablename__ = 'delivery_proofs'
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    order_id: Mapped[str] = mapped_column(ForeignKey('orders.id'), index=True)
    submitted_by_user_id: Mapped[str] = mapped_column(ForeignKey('users.id'))
    evidence_uri: Mapped[str] = mapped_column(String(500))
    otp_code_hash: Mapped[str | None] = mapped_column(String(80))
    gps_lat: Mapped[str | None] = mapped_column(String(40))
    gps_lng: Mapped[str | None] = mapped_column(String(40))
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    confidence_score: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(50), default=ProofStatus.SUBMITTED.value)
    proof_hash: Mapped[str | None] = mapped_column(String(80))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class ProofBundle(Base):
    __tablename__ = 'proof_bundles'
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    business_id: Mapped[str] = mapped_column(ForeignKey('businesses.id'), index=True)
    order_id: Mapped[str | None] = mapped_column(ForeignKey('orders.id'))
    invoice_id: Mapped[str | None] = mapped_column(ForeignKey('invoices.id'))
    delivery_proof_id: Mapped[str | None] = mapped_column(ForeignKey('delivery_proofs.id'))
    bundle_type: Mapped[str] = mapped_column(String(80))
    payload_json: Mapped[dict] = mapped_column(JSON, default=dict)
    proof_hash: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    polygon_tx_hash: Mapped[str | None] = mapped_column(String(120))
    status: Mapped[str] = mapped_column(String(50), default=ProofStatus.VERIFIED.value)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Receivable(Base):
    __tablename__ = 'receivables'
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    invoice_id: Mapped[str] = mapped_column(ForeignKey('invoices.id'), index=True)
    seller_business_id: Mapped[str] = mapped_column(ForeignKey('businesses.id'), index=True)
    debtor_name: Mapped[str] = mapped_column(String(255))
    face_value: Mapped[float] = mapped_column(Numeric(18, 2))
    currency: Mapped[str] = mapped_column(String(10), default='USDC')
    maturity_date: Mapped[datetime]
    proof_hash: Mapped[str] = mapped_column(String(80))
    status: Mapped[str] = mapped_column(String(50), default=ReceivableStatus.CREATED.value)
    token_id: Mapped[int | None] = mapped_column(Integer)
    polygon_tx_hash: Mapped[str | None] = mapped_column(String(120))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class SmartLC(Base):
    __tablename__ = 'smart_lcs'
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    order_id: Mapped[str] = mapped_column(ForeignKey('orders.id'), index=True)
    seller_business_id: Mapped[str] = mapped_column(ForeignKey('businesses.id'), index=True)
    buyer_name: Mapped[str] = mapped_column(String(255))
    amount: Mapped[float] = mapped_column(Numeric(18, 2))
    currency: Mapped[str] = mapped_column(String(10), default='USDC')
    status: Mapped[str] = mapped_column(String(50), default=SmartLCStatus.CREATED.value)
    contract_address: Mapped[str | None] = mapped_column(String(120))
    polygon_tx_hash: Mapped[str | None] = mapped_column(String(120))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
