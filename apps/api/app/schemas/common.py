from datetime import datetime
from pydantic import BaseModel, ConfigDict

class APIResponse(BaseModel):
    ok: bool = True
    message: str | None = None

class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

class Pagination(BaseModel):
    limit: int = 50
    offset: int = 0

class BlockchainReference(BaseModel):
    tx_hash: str | None = None
    explorer_url: str | None = None
