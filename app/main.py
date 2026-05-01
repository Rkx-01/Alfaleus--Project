import logging
import traceback
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.endpoints import router as api_router
from app.utils.config import settings
from app.scheduler.main import setup_scheduler
from app.db import db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="InsightMatrix API",
    description="NoSQL News Aggregator",
    version="2.0.0",
)

# 1. ADD CORS FIRST (Outermost)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Global Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"GLOBAL CRASH: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": str(exc),
            "traceback": traceback.format_exc()
        }
    )

# Temporarily disabled security middleware to find the crash cause
# from app.utils.security import ProductionSecurityMiddleware
# app.add_middleware(ProductionSecurityMiddleware)

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.on_event("startup")
async def startup_event():
    if db:
        try:
            await db.connect()
            logger.info("Connected to MongoDB Atlas.")
        except Exception as e:
            logger.error(f"DB Connect Error: {e}")
    setup_scheduler()

@app.on_event("shutdown")
async def shutdown_event():
    if db and db.is_connected():
        await db.disconnect()

@app.get("/")
async def root():
    return {"status": "online"}
