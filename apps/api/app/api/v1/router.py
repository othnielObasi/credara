from fastapi import APIRouter
from app.api.v1.routes import auth, businesses, trade, finance, proof_ledger, admin, kyb, enterprise

api_router = APIRouter()
api_router.include_router(auth.router, prefix='/auth', tags=['auth'])
api_router.include_router(businesses.router, prefix='/businesses', tags=['businesses'])
api_router.include_router(trade.router, prefix='/trade', tags=['trade'])
api_router.include_router(finance.router, prefix='/finance', tags=['finance'])
api_router.include_router(proof_ledger.router, prefix='/proof-ledger', tags=['proof-ledger'])
api_router.include_router(admin.router, prefix='/admin', tags=['admin'])

api_router.include_router(kyb.router, prefix='/kyb', tags=['kyb'])

api_router.include_router(enterprise.router, tags=['enterprise'])
