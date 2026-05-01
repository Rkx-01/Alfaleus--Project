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
    description="NoSQL AI News Aggregator",
    version="2.0.0",
)

# 1. CORS MIDDLEWARE (Must be Outermost)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# 2. GLOBAL ERROR HANDLER (With CORS Headers)
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"FATAL CRASH: {request.url.path} - {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "error": "Internal Server Error",
            "details": str(exc),
            "path": request.url.path
        },
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*"
        }
    )

# 3. ROUTES
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.on_event("startup")
async def startup_event():
    logger.info("Initializing Application...")
    if db:
        try:
            await db.connect()
            logger.info("Database Connection Established.")
        except Exception as e:
            logger.error(f"Initial DB Connection Failed: {e}")
    
    # Start background scheduler
    setup_scheduler()

@app.on_event("shutdown")
async def shutdown_event():
    if db and db.is_connected():
        await db.disconnect()

@app.get("/")
async def root():
    return {
        "status": "online",
        "database": "connected" if (db and db.is_connected()) else "disconnected"
    }

@app.get("/trigger-now")
async def manual_trigger():
    from app.scheduler.main import run_news_digest_pipeline
    import asyncio
    asyncio.create_task(run_news_digest_pipeline())
    return {"status": "success", "message": "Manual sync triggered."}
