import logging
from fastapi import APIRouter, HTTPException
from typing import List, Optional
from app.db import db as prisma

router = APIRouter()
logger = logging.getLogger(__name__)

async def ensure_db_connected():
    if prisma and not prisma.is_connected():
        try: await prisma.connect()
        except: pass

@router.get("/digest")
async def read_digest(category: str = None, limit: int = 10):
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
        logger.error(f"Error fetching digest: {e}")
        return []

@router.get("/digest/count")
async def get_digest_count(category: str = None):
    await ensure_db_connected()
    try:
        where = {}
        if category and category.lower() != "all": 
            where = {"category": category}
        return await prisma.cluster.count(where=where)
    except Exception as e:
        logger.error(f"Error fetching count: {e}")
        return 0

@router.get("/articles/saved")
async def get_saved_articles(): 
    return []

@router.get("/categories")
async def get_unique_categories(): 
    return ["Technology", "Politics", "Science", "Sports", "World"]

@router.get("/stats")
async def get_stats(): 
    await ensure_db_connected()
    try:
        articles = await prisma.article.count()
        return {"last_updated": "Just now", "sources": articles}
    except:
        return {"last_updated": "Unknown", "sources": 0}

@router.get("/subscriptions")
async def get_subscriptions(): 
    return []

@router.get("/test")
async def test_route():
    from app.scheduler.main import run_news_digest_pipeline
    import asyncio
    asyncio.create_task(run_news_digest_pipeline())
    return {"status": "ok", "message": "Manual sync triggered."}

@router.get("/debug")
async def debug_database():
    import traceback
    try:
        from app.db import check_db_health
        health, msg = await check_db_health()
        
        # If check failed, try a raw connect to get the real error
        if not health:
            return {
                "db_health": health,
                "health_msg": msg,
                "traceback": traceback.format_exc()
            }
            
        articles = await prisma.article.count()
        clusters = await prisma.cluster.count()
        return {
            "articles_in_db": articles, 
            "clusters_in_db": clusters,
            "db_health": health,
            "health_msg": msg
        }
    except Exception as e: 
        return {
            "error": str(e),
            "traceback": traceback.format_exc()
        }
