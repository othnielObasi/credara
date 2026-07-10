from pydantic import BaseModel, Field
from app.schemas.common import ORMModel

class BusinessCreate(BaseModel):
    legal_name: str = Field(min_length=2)
    country: str = Field(min_length=2, max_length=2)
    registration_number: str | None = None
    industry: str | None = None
    wallet_address: str | None = None

class BusinessWalletUpdate(BaseModel):
    wallet_address: str = Field(min_length=42, max_length=42)

class BusinessRead(ORMModel):
    id: str
    legal_name: str
    country: str
    registration_number: str | None
    status: str
    industry: str | None
    wallet_address: str | None
