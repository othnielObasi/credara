from pydantic import BaseModel, EmailStr

class RegisterRequest(BaseModel):
    email: EmailStr
    full_name: str
    password: str
    role: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = 'bearer'
    role: str
