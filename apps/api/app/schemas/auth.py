from typing import Literal

from pydantic import BaseModel, EmailStr

SelfServeRole = Literal['sme', 'buyer', 'financier']

class RegisterRequest(BaseModel):
    email: EmailStr
    full_name: str
    password: str
    role: SelfServeRole

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = 'bearer'
    role: str
