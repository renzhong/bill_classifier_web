from fastapi import APIRouter

from app.auth.router import router as auth_router
from app.bills.router import router as bills_router
from app.categories.router import router as categories_router
from app.dicts.router import router as dicts_router
from app.tags.router import router as tags_router

api_v1 = APIRouter(prefix="/api/v1")
api_v1.include_router(auth_router)
api_v1.include_router(categories_router)
api_v1.include_router(tags_router)
api_v1.include_router(dicts_router)
api_v1.include_router(bills_router)
