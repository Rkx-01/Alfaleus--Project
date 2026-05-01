import logging
from fastapi import APIRouter, HTTPException
from typing import List, Optional
from app.db import db_manager, check_db_health
from bson import ObjectId
from app.services.collector import collect_all_news
from datetime import datetime, timezone

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/")
async def api_root():
    return {"status": "online", "message": "InsightMatrix API v1"}

def serialize_mongo(doc):
    if not doc: return doc
    doc["id"] = str(doc.pop("_id"))
    return doc

@router.get("/digest")
async def read_digest(category: str = None, limit: int = 10):
    try:
        query = {}
        if category and category.lower() != "all":
            query["category"] = category
            
        cursor = db_manager.db.clusters.find(query).sort("createdAt", -1).limit(limit)
        clusters = await cursor.to_list(length=limit)
        
        # If no clusters, return raw articles grouped by title (Pseudo-clusters)
        if not clusters:
            articles_cursor = db_manager.db.articles.find(query).sort("publishedAt", -1).limit(limit)
            raw_articles = await articles_cursor.to_list(length=limit)
            return [{
                "id": str(a["_id"]),
                "topicName": a["title"],
                "category": a.get("category", "General"),
                "createdAt": a.get("publishedAt"),
                "articles": [serialize_mongo(a)]
            } for a in raw_articles]
            
        # Hydrate articles
        for cluster in clusters:
            article_ids = [ObjectId(aid) if isinstance(aid, str) else aid for aid in cluster.get("articleIds", [])]
            articles_cursor = db_manager.db.articles.find({"_id": {"$in": article_ids}})
            cluster["articles"] = [serialize_mongo(a) for a in await articles_cursor.to_list(length=100)]
            serialize_mongo(cluster)
            
        return clusters
    except Exception as e:
        logger.error(f"Digest fetch error: {e}")
        return []

@router.get("/nuclear-fetch")
async def nuclear_fetch():
    """Forces 10 articles into DB instantly with NO processing."""
    try:
        articles = await collect_all_news()
        count = 0
        for a in articles[:15]:
            await db_manager.db.articles.update_one(
                {"url": a.url},
                {"$setOnInsert": {
                    "title": a.title,
                    "url": a.url,
                    "source": a.source,
                    "category": a.category or "World",
                    "content": a.content,
                    "publishedAt": a.published_at,
                    "summary": a.description or a.title,
                    "clusterIds": []
                }},
                upsert=True
            )
            count += 1
        return {"status": "success", "articles_added": count}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.get("/digest/count")
async def get_digest_count(category: str = None):
    try:
        query = {}
        if category and category.lower() != "all":
            query["category"] = category
        count = await db_manager.db.clusters.count_documents(query)
        if count == 0:
            return await db_manager.db.articles.count_documents(query)
        return count
    except: return 0

@router.get("/articles/saved")
async def get_saved_articles(): return []

@router.get("/categories")
async def get_unique_categories():
    return ["Technology", "Politics", "Science", "Sports", "World"]

@router.get("/stats")
async def get_stats():
    try:
        count = await db_manager.db.articles.count_documents({})
        return {"last_updated": "Just now", "sources": count}
    except: return {"sources": 0}

@router.get("/subscriptions")
async def get_subscriptions(): return []

@router.get("/test")
async def test_route():
    from app.scheduler.main import run_news_digest_pipeline
    import asyncio
    asyncio.create_task(run_news_digest_pipeline())
    return {"status": "ok", "message": "Manual sync triggered."}

@router.get("/debug")
async def debug_database():
    health, msg = await check_db_health()
    try:
        articles = await db_manager.db.articles.count_documents({})
        clusters = await db_manager.db.clusters.count_documents({})
        return {
            "articles_in_db": articles,
            "clusters_in_db": clusters,
            "db_health": health,
            "health_msg": msg,
            "engine": "Motor"
        }
    except Exception as e:
        return {"error": str(e), "engine": "Motor"}
