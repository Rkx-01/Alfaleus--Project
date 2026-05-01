import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.endpoints import router as api_router
from app.utils.config import settings
from app.scheduler.main import setup_scheduler
from app.models.base import Base, engine

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
    * **Async Processing**: Built on SQLAlchemy Async and AsyncIO.
    * **AI Insights**: Summaries generated via OpenAI GPT.
    * **Smart Clustering**: ML-based grouping of related stories.
    * **Secure**: API Key authentication and Rate Limiting included.
    """,
    version="1.0.0",
    contact={
        "name": "Antigravity Dev Team",
        "url": "https://github.com/rkx-01/news-digest-api",
    },
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Register Security Middleware
app.add_middleware(ProductionSecurityMiddleware)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, specify the frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.on_event("startup")
async def startup_event():
    logger.info("Application starting up...")
    
    # Create tables asynchronously
    async with engine.begin() as conn:
        # await conn.run_sync(Base.metadata.drop_all) # Optional for reset
        await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables verified.")
    
    setup_scheduler()

@app.get("/")
async def root():
    return {"message": "Welcome to the Optimized News Digest API (Async Mode)"}
