from fastapi import APIRouter

from app.auth.router import router as auth_router

api_v1 = APIRouter(prefix="/api/v1")
api_v1.include_router(auth_router)
