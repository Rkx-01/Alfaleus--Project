import logging
from fastapi import FastAPI
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

from app.utils.security import ProductionSecurityMiddleware

app = FastAPI(
    title="InsightMatrix API",
    description="NoSQL News Aggregator with Prisma & MongoDB",
    version="2.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Register Security Middleware
app.add_middleware(ProductionSecurityMiddleware)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.on_event("startup")
async def startup_event():
    logger.info("Application starting up...")
    if db:
        try:
            await db.connect()
            logger.info("Connected to MongoDB Atlas via Prisma.")
        except Exception as e:
            logger.error(f"Could not connect to database: {e}")
    else:
        logger.error("Database client (db.py) is missing or failed to initialize.")
    
    setup_scheduler()

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Application shutting down...")
    if db and db.is_connected():
        await db.disconnect()

@app.get("/")
async def root():
    return {"message": "InsightMatrix API is online (MongoDB Mode)"}

@app.get("/pulse-check")
async def pulse_check():
    if not db:
        return {"error": "Database not initialized"}
    
    art_count = await db.article.count()
    sum_count = await db.article.count(where={"summary": {"not": None}})
    clu_count = await db.cluster.count()
    return {
        "total_articles": art_count,
        "summarized_articles": sum_count,
        "total_clusters": clu_count
    }

@app.get("/trigger-now")
async def manual_trigger():
    from app.scheduler.main import run_news_digest_pipeline
    import asyncio
    asyncio.create_task(run_news_digest_pipeline())
    return {"status": "success", "message": "Pipeline triggered."}
