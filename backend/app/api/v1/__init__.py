from fastapi import APIRouter

from app.ai.router import router as ai_router
from app.assets.router import router as assets_router
from app.auth.router import router as auth_router
from app.bills.router import router as bills_router
from app.categories.router import router as categories_router
from app.dicts.router import router as dicts_router
from app.incomes.router import router as incomes_router
from app.pipeline.router import router as pipeline_router
from app.reports.router import router as reports_router
from app.tags.router import router as tags_router

api_v1 = APIRouter(prefix="/api/v1")
api_v1.include_router(auth_router)
api_v1.include_router(categories_router)
api_v1.include_router(tags_router)
api_v1.include_router(dicts_router)
api_v1.include_router(pipeline_router)
api_v1.include_router(ai_router)
api_v1.include_router(bills_router)
api_v1.include_router(assets_router)
api_v1.include_router(incomes_router)
api_v1.include_router(reports_router)
