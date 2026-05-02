import logging
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from app.db import db_manager, check_db_health
from bson import ObjectId
from app.services.collector import collect_all_news
from datetime import datetime, timezone

router = APIRouter()
logger = logging.getLogger(__name__)

async def ensure_db():
    if db_manager.db is None:
        await db_manager.connect()
    if db_manager.db is None:
        raise HTTPException(status_code=503, detail="Database connection failed")

def serialize_mongo(doc):
    if not doc: return doc
    # Convert ObjectId to String
    if "_id" in doc:
        doc["id"] = str(doc.pop("_id"))
    # Convert all DateTimes to Strings
    for key, value in doc.items():
        if isinstance(value, datetime):
            doc[key] = value.isoformat()
        if isinstance(value, ObjectId):
            doc[key] = str(value)
        if isinstance(value, list):
            doc[key] = [str(i) if isinstance(i, ObjectId) else i for i in value]
    return doc

@router.get("/digest")
async def read_digest(
    category: str = "All", 
    skip: int = 0, 
    limit: int = 10
):
    await ensure_db()
    try:
        query = {}
        if category and category.lower() != "all":
            query["category"] = category
            
        cursor = db_manager.db.clusters.find(query).sort("createdAt", -1).skip(skip).limit(limit)
        clusters_raw = await cursor.to_list(length=limit)
        
        if not clusters_raw:
            # Fallback to raw articles if no clusters yet
            articles_cursor = db_manager.db.articles.find(query).sort("publishedAt", -1).skip(skip).limit(limit)
            raw_articles = await articles_cursor.to_list(length=limit)
            return [serialize_mongo({
                "topic_name": a["title"],
                "category": a.get("category", "General"),
                "createdAt": a.get("publishedAt"),
                "articles": [serialize_mongo(a)]
            }) for a in raw_articles]
            
        clusters = []
        for cluster in clusters_raw:
            # Hydrate articles
            article_ids = [ObjectId(aid) if isinstance(aid, str) else aid for aid in cluster.get("articleIds", [])]
            articles_cursor = db_manager.db.articles.find({"_id": {"$in": article_ids}})
            cluster["articles"] = [serialize_mongo(a) for a in await articles_cursor.to_list(length=100)]
            clusters.append(serialize_mongo(cluster))
            
        return clusters
    except Exception as e:
        logger.error(f"Digest error: {e}")
        return []

@router.get("/digest/count")
async def get_digest_count(category: str = "All"):
    await ensure_db()
    try:
        query = {}
        if category and category.lower() != "all":
            query["category"] = category
        count = await db_manager.db.clusters.count_documents(query)
        if count == 0:
            count = await db_manager.db.articles.count_documents(query)
        return {"total": count}
    except: 
        return {"total": 0}

@router.get("/nuclear-fetch")
async def nuclear_fetch():
    await ensure_db()
    try:
        articles = await collect_all_news()
        count = 0
        for a in articles[:20]:
            await db_manager.db.articles.update_one(
                {"url": a.url},
                {"$set": {
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

@router.get("/categories")
async def get_unique_categories():
    return ["Technology", "Politics", "Science", "Sports", "World"]

@router.get("/stats")
async def get_stats():
    await ensure_db()
    try:
        count = await db_manager.db.articles.count_documents({})
        return {"last_updated": datetime.now().isoformat(), "sources": count}
    except: return {"sources": 0}

@router.get("/subscriptions")
async def get_subscriptions(): return []

@router.get("/articles/saved")
async def get_saved_articles(): return []

@router.get("/debug")
async def debug_database():
    health, msg = await check_db_health()
    try:
        await ensure_db()
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
        return {"error": str(e)}

@router.get("/")
async def api_root():
    return {"status": "online", "message": "InsightMatrix Stable API v1"}
