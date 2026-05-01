import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.endpoints import router as api_router
from app.utils.config import settings
from app.scheduler.main import setup_scheduler
from prisma import Prisma

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

from app.utils.security import ProductionSecurityMiddleware

app = FastAPI(
    title="Antigravity News Digest API",
    description="""
    A production-ready API for multi-source news collection, clustering, and AI summarization.
    
    ### Features
    * **NoSQL Persistence**: Powered by MongoDB Atlas and Prisma.
    * **AI Insights**: Summaries generated via Groq Llama 3.
    * **Smart Clustering**: ML-based grouping of related stories.
    * **Secure**: API Key authentication and Rate Limiting included.
    """,
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Initialize Prisma
prisma = Prisma()

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
    await prisma.connect()
    logger.info("Connected to MongoDB Atlas via Prisma.")
    setup_scheduler()

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Application shutting down...")
    await prisma.disconnect()

@app.get("/")
async def root():
    return {"message": "Welcome to the Optimized News Digest API (Async Mode)"}

@app.get("/trigger-now")
async def manual_trigger():
    from app.scheduler.main import run_news_digest_pipeline
    import asyncio
    asyncio.create_task(run_news_digest_pipeline())
    return {"status": "success", "message": "Pipeline started! Please refresh your frontend in 2 minutes."}

@app.get("/pulse-check")
async def pulse_check():
    from sqlalchemy import func
    from app.models.base import AsyncSessionLocal
    from app.models import news as models
    from sqlalchemy import select
    async with AsyncSessionLocal() as db:
        art_count = await db.execute(select(func.count(models.Article.id)))
        sum_count = await db.execute(select(func.count(models.Article.id)).filter(models.Article.summary != None))
        clu_count = await db.execute(select(func.count(models.Cluster.id)))
        return {
            "total_articles": art_count.scalar(),
            "summarized_articles": sum_count.scalar(),
            "total_clusters": clu_count.scalar()
        }
