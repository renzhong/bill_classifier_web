from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1 import api_v1
from app.core.config import get_settings
from app.core.logging import setup_logging
from app.core.response import fail

setup_logging()
settings = get_settings()

app = FastAPI(
    title="Bill Classifier Web API",
    version="0.1.0",
    docs_url="/docs",
    redoc_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(HTTPException)
async def http_exception_handler(_, exc: HTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=fail(str(exc.detail), code=exc.status_code),
    )


@app.get("/healthz")
async def healthz() -> dict:
    return {"status": "ok", "env": settings.env}


app.include_router(api_v1)
