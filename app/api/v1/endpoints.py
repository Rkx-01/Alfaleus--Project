import logging
from fastapi import APIRouter, HTTPException
from typing import List, Optional
from app.db import db as prisma

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/digest/count")
async def get_clusters_count(category: str = None):
    if not prisma:
        return {"count": 0}
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
    # Safe Fallback
    default_cats = ["Technology", "Politics", "Science", "Sports", "World"]
    if not prisma:
        return default_cats
    
    try:
        clusters = await prisma.cluster.find_many()
        if not clusters:
            return default_cats
        categories = {c.category for c in clusters if c.category}
        return sorted(list(categories)) if categories else default_cats
    except Exception as e:
        logger.error(f"Categories Fetch Failed: {e}")
        return default_cats

@router.get("/digest")
async def read_digest(category: str = None, limit: int = 10):
    if not prisma:
        return []
    
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
        logger.error(f"Digest Fetch Failed: {e}")
        return []

@router.get("/topic/{topic_id}")
async def get_topic_details(topic_id: str):
    if not prisma:
        raise HTTPException(status_code=503, detail="Database Offline")
    try:
        topic = await prisma.cluster.find_unique(
            where={"id": topic_id},
            include={"articles": True}
        )
        if not topic:
            raise HTTPException(status_code=404, detail="Topic not found")
        return topic
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_stats():
    if not prisma:
        return {"last_updated": None, "sources": 0}
        
    try:
        status = await prisma.systemstatus.find_first(order={"lastRunAt": "desc"})
        last_updated = status.lastRunAt.isoformat() if status else None
        
        # In MongoDB, we fetch all and set-ify to avoid 'distinct' crash
        articles = await prisma.article.find_many()
        sources = {a.source for a in articles if a.source}
        
        return {
            "last_updated": last_updated,
            "sources": len(sources)
        }
    except Exception:
        return {"last_updated": None, "sources": 0}
