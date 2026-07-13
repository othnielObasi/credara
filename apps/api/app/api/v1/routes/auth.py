import secrets
from urllib.parse import quote, urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.core.security import create_access_token, hash_password, verify_password
from app.models.identity import User
from app.schemas.auth import RegisterRequest, TokenResponse

router = APIRouter()

OAUTH_STATE_COOKIE = 'credara_oauth_state'


@router.post('/register', response_model=TokenResponse)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=409, detail='Email already registered')
    user = User(email=payload.email, full_name=payload.full_name, role=payload.role, password_hash=hash_password(payload.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return TokenResponse(access_token=create_access_token(user.id, user.role), role=user.role)

@router.post('/login', response_model=TokenResponse)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form.username).first()
    if not user or not verify_password(form.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid credentials')
    return TokenResponse(access_token=create_access_token(user.id, user.role), role=user.role)


@router.get('/oauth/login')
def oauth_login():
    """Starts the Auth0 Authorization Code flow (Regular Web App). The state
    value is stored in a short-lived HttpOnly cookie rather than any server
    session store, and validated against the callback's own state param -
    standard CSRF protection for this flow without needing shared session state.
    """
    settings = get_settings()
    if not settings.auth0_domain or not settings.auth0_client_id:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, 'OAuth is not configured')
    state = secrets.token_urlsafe(24)
    params = {
        'response_type': 'code',
        'client_id': settings.auth0_client_id,
        'redirect_uri': settings.auth0_callback_url,
        'scope': 'openid profile email',
        'state': state,
    }
    redirect = RedirectResponse(f'https://{settings.auth0_domain}/authorize?{urlencode(params)}')
    redirect.set_cookie(OAUTH_STATE_COOKIE, state, max_age=600, httponly=True, secure=True, samesite='lax')
    return redirect


@router.get('/oauth/callback')
async def oauth_callback(
    request: Request,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    error_description: str | None = None,
    db: Session = Depends(get_db),
):
    settings = get_settings()

    def _fail(message: str) -> RedirectResponse:
        redirect = RedirectResponse(f'{settings.auth0_frontend_redirect}?error={quote(message)}')
        redirect.delete_cookie(OAUTH_STATE_COOKIE)
        return redirect

    if error:
        return _fail(f'Auth0 error: {error} - {error_description or ""}')
    if not code or not state:
        return _fail('Missing code or state from Auth0 callback')
    cookie_state = request.cookies.get(OAUTH_STATE_COOKIE)
    if not cookie_state or cookie_state != state:
        return _fail(
            'Invalid or expired OAuth state. Start sign-in again from Credara (do not reuse an old callback link).'
        )

    async with httpx.AsyncClient(timeout=15.0) as client:
        token_resp = await client.post(f'https://{settings.auth0_domain}/oauth/token', json={
            'grant_type': 'authorization_code',
            'client_id': settings.auth0_client_id,
            'client_secret': settings.auth0_client_secret,
            'code': code,
            'redirect_uri': settings.auth0_callback_url,
        })
        if token_resp.status_code != 200:
            return _fail(f'Auth0 token exchange failed: {token_resp.text}')
        tokens = token_resp.json()
        id_token = tokens.get('id_token')
        if not id_token:
            return _fail('Auth0 did not return an id_token')

        jwks_resp = await client.get(f'https://{settings.auth0_domain}/.well-known/jwks.json')
        jwks = jwks_resp.json()

    try:
        claims = jwt.decode(
            id_token, jwks, algorithms=['RS256'],
            audience=settings.auth0_client_id,
            issuer=f'https://{settings.auth0_domain}/',
        )
    except JWTError as exc:
        return _fail(f'Invalid Auth0 id_token: {exc}')

    email = claims.get('email')
    if not email:
        return _fail('Auth0 identity has no email claim')
    full_name = claims.get('name') or email

    user = db.query(User).filter(User.email == email).first()
    if not user:
        # OAuth-created accounts get an unusable random password hash - there's
        # no password to verify against, sign-in only ever happens via Auth0.
        user = User(email=email, full_name=full_name, role='sme', password_hash=hash_password(secrets.token_urlsafe(32)))
        db.add(user)
        db.commit()
        db.refresh(user)

    access_token = create_access_token(user.id, user.role)
    redirect = RedirectResponse(f'{settings.auth0_frontend_redirect}#token={access_token}&role={user.role}')
    redirect.delete_cookie(OAUTH_STATE_COOKIE)
    return redirect
