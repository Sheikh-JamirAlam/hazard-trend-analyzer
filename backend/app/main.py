import os
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pymongo import AsyncMongoClient

from app.api.routes.analysis import router as analysis_router
from app.api.routes.health import router as health_router
from app.repositories.analysis_repository import AnalysisRepository


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.http_client = httpx.AsyncClient(
        timeout=httpx.Timeout(30.0, connect=5.0)
    )
    app.state.mongo_client = AsyncMongoClient(
        os.getenv("MONGODB_URL", "mongodb://localhost:27017"),
        serverSelectionTimeoutMS=3000,
        connectTimeoutMS=3000,
    )
    app.state.analysis_repository = AnalysisRepository(
        app.state.mongo_client,
        os.getenv("MONGODB_DATABASE", "hazard_trend_analyzer"),
    )
    try:
        yield
    finally:
        await app.state.http_client.aclose()
        await app.state.mongo_client.close()


app = FastAPI(title="Climate Hazard Trend Analyzer API", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in os.getenv(
        "FRONTEND_ORIGIN", "http://localhost:5173").split(",") if origin.strip()],
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)
app.include_router(health_router, prefix="/api")
app.include_router(analysis_router, prefix="/api")
