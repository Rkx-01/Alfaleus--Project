import logging
import traceback
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.endpoints import router as api_router
from app.utils.config import settings
from app.scheduler.main import setup_scheduler
from app.db import db_manager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up application (Motor Mode)...")
    await db_manager.connect()
    setup_scheduler()
    yield
    await db_manager.disconnect()

app = FastAPI(
    title="InsightMatrix API",
    description="Motor-powered AI News Aggregator",
    version="3.0.0",
    lifespan=lifespan
)

# CORS MIDDLEWARE (Ultra-Permissive for Vercel)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS", "PUT", "DELETE"],
    allow_headers=["*"],
    expose_headers=["*"],
)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"FATAL ERROR: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": str(exc),
            "traceback": traceback.format_exc()
        }
    )

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
async def root():
    return {
        "status": "online",
        "database": "connected" if db_manager.db is not None else "disconnected",
        "engine": "Motor"
    }
