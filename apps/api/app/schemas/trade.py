from datetime import datetime
from pydantic import BaseModel, Field
from app.schemas.common import ORMModel

class OrderCreate(BaseModel):
    seller_business_id: str
    buyer_name: str
    description: str
    total_amount: float = Field(gt=0)
    currency: str = 'USDC'
    expected_delivery_date: datetime | None = None

class OrderConfirmRequest(BaseModel):
    buyer_business_id: str

class OrderRead(ORMModel):
    id: str
    seller_business_id: str
    buyer_name: str
    description: str
    total_amount: float
    currency: str
    status: str

class InvoiceCreate(BaseModel):
    order_id: str
    invoice_number: str
    amount: float = Field(gt=0)
    due_date: datetime

class InvoiceBuyerConfirmRequest(BaseModel):
    buyer_business_id: str

class InvoiceRead(ORMModel):
    id: str
    order_id: str
    invoice_number: str
    amount: float
    currency: str
    status: str
    proof_hash: str | None

class DeliveryProofCreate(BaseModel):
    order_id: str
    evidence_uri: str
    otp_code: str | None = None
    gps_lat: str | None = None
    gps_lng: str | None = None
    metadata_json: dict = {}

class DeliveryProofRead(ORMModel):
    id: str
    order_id: str
    evidence_uri: str
    confidence_score: int
    status: str
    proof_hash: str | None

class ReceivableCreate(BaseModel):
    invoice_id: str

class ReceivableRead(ORMModel):
    id: str
    invoice_id: str
    seller_business_id: str
    debtor_name: str
    face_value: float
    currency: str
    maturity_date: datetime
    proof_hash: str
    status: str
    token_id: int | None
    polygon_tx_hash: str | None

class SmartLCCreate(BaseModel):
    order_id: str
    amount: float = Field(gt=0)
    currency: str = 'USDC'

class SmartLCRead(ORMModel):
    id: str
    order_id: str
    seller_business_id: str
    buyer_name: str
    amount: float
    currency: str
    status: str
    contract_address: str | None
    polygon_tx_hash: str | None
