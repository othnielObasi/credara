from datetime import datetime, timedelta, timezone
from enum import StrEnum

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.models.identity import User


oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/api/v1/auth/login')


class Role(StrEnum):
    ADMIN = 'admin'
    SME = 'sme'
    BUYER = 'buyer'
    FINANCIER = 'financier'
    DEVELOPER = 'developer'


def _password_bytes(password: str) -> bytes:
    """Return bcrypt-safe UTF-8 bytes.

    bcrypt 5 rejects passwords longer than 72 bytes. Raising a clear API-level
    error is safer than silently truncating credentials.
    """
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail='Password must be 72 bytes or fewer after UTF-8 encoding',
        )
    return password_bytes


def hash_password(password: str) -> str:
    return bcrypt.hashpw(_password_bytes(password), bcrypt.gensalt(rounds=12)).decode('utf-8')


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(_password_bytes(password), password_hash.encode('utf-8'))
    except (ValueError, TypeError):
        return False


def create_access_token(subject: str, role: str, minutes: int | None = None) -> str:
    settings = get_settings()
    ttl = minutes if minutes is not None else settings.jwt_access_token_minutes
    now = datetime.now(timezone.utc)
    payload = {
        'sub': subject,
        'role': role,
        'iss': settings.jwt_issuer,
        'aud': settings.jwt_audience,
        'iat': int(now.timestamp()),
        'exp': int((now + timedelta(minutes=ttl)).timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm='HS256')


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=['HS256'], audience=settings.jwt_audience, issuer=settings.jwt_issuer)
    except JWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid authentication token') from exc
    user = db.get(User, payload.get('sub'))
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Inactive or missing user')
    return user


def require_roles(*roles: Role):
    def dependency(user: User = Depends(get_current_user)) -> User:
        if user.role not in {r.value for r in roles}:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Insufficient permissions')
        return user
    return dependency
