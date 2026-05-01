import logging
import traceback
import os

# CRITICAL: Force Render Compatibility
os.environ["PRISMA_PY_DEBUG"] = "1"
os.environ["PRISMA_CLI_BINARY_TARGETS"] = "native,debian-openssl-1.1.x,debian-openssl-3.0.x"
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.endpoints import router as api_router
from app.utils.config import settings
from app.scheduler.main import setup_scheduler
from app.db import db
from tenacity import retry, stop_after_attempt, wait_fixed

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

@retry(stop=stop_after_attempt(5), wait=wait_fixed(2))
async def connect_to_db():
    if db:
        if not db.is_connected():
            await db.connect()
            logger.info("Successfully connected to MongoDB Atlas.")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    logger.info("Starting up application...")
    try:
        await connect_to_db()
    except Exception as e:
        logger.error(f"CRITICAL: Failed to connect to DB after retries: {e}")
    
    setup_scheduler()
    yield
    # Shutdown logic
    if db and db.is_connected():
        await db.disconnect()
        logger.info("Database disconnected.")

app = FastAPI(
    title="InsightMatrix API",
    description="NoSQL AI News Aggregator",
    version="2.0.0",
    lifespan=lifespan
)

# CORS MIDDLEWARE
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# GLOBAL ERROR HANDLER
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"FATAL ERROR: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": str(exc),
            "traceback": traceback.format_exc()
        },
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*"
        }
    )

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
async def root():
    return {
        "status": "online",
        "database": "connected" if (db and db.is_connected()) else "disconnected"
    }

@app.get("/test")
async def test_root():
    return {"status": "ok", "message": "Main App is reachable!"}
