import logging
from fastapi import APIRouter, HTTPException
from typing import List, Optional
from app.db import db as prisma

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/")
async def api_root():
    return {
        "message": "Welcome to the News Digest API v1",
        "endpoints": ["/digest", "/categories", "/subscriptions", "/stats", "/test"]
    }

async def ensure_db_connected():
    """Ensure database is connected before running a query."""
    if prisma and not prisma.is_connected():
        try:
            await prisma.connect()
            logger.info("Reconnected to database on-the-fly.")
        except Exception as e:
            logger.error(f"Failed to reconnect to database: {e}")

@router.get("/digest/count")
async def get_clusters_count(category: str = None):
    if not prisma:
        return {"count": 0}
    
    await ensure_db_connected()
    
    try:
        where = {}
        if category and category.lower() != "all":
            where = {"category": category}
        count = await prisma.cluster.count(where=where)
        return {"count": count}
    except Exception:
        return {"count": 0}

@router.get("/categories")
async def get_unique_categories():
    default_cats = ["Technology", "Politics", "Science", "Sports", "World"]
    if not prisma:
        return default_cats
    
    await ensure_db_connected()
    
    try:
        clusters = await prisma.cluster.find_many()
        if not clusters:
            return default_cats
        categories = {c.category for c in clusters if c.category}
        return sorted(list(categories)) if categories else default_cats
    except Exception as e:
        return default_cats

@router.get("/digest")
async def read_digest(category: str = None, limit: int = 10):
    if not prisma:
        return []
    
    await ensure_db_connected()
    
    try:
        where = {}
        if category and category.lower() != "all":
            where = {"category": category}
            
        clusters = await prisma.cluster.find_many(
            where=where,
            take=limit,
            order={"createdAt": "desc"},
            include={"articles": True}
        )
        return clusters
    except Exception as e:
        return []

@router.get("/stats")
async def get_stats():
    if not prisma:
        return {"last_updated": None, "sources": 0}
        
    await ensure_db_connected()
    
    try:
        status = await prisma.systemstatus.find_first(order={"lastRunAt": "desc"})
        last_updated = status.lastRunAt.isoformat() if status else None
        
        articles = await prisma.article.find_many()
        sources = {a.source for a in articles if a.source}
        
        return {
            "last_updated": last_updated,
            "sources": len(sources)
        }
    except Exception:
        return {"last_updated": None, "sources": 0}

@router.get("/subscriptions")
async def get_subscriptions():
    if not prisma: return []
    await ensure_db_connected()
    try:
        return await prisma.subscription.find_many()
    except: return []

@router.post("/subscriptions")
async def create_subscription(data: dict):
    if not prisma: raise HTTPException(status_code=503)
    await ensure_db_connected()
    try:
        return await prisma.subscription.create(data={"email": data["email"]})
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/articles/saved")
async def get_saved_articles():
    if not prisma: return []
    await ensure_db_connected()
    try:
        return await prisma.savedarticle.find_many()
    except: return []

@router.get("/test")
async def test_route():
    return {"status": "ok", "message": "Backend is reachable!"}
