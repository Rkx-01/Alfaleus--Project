import logging
from fastapi import APIRouter, HTTPException
from typing import List, Optional
from app.db import db as prisma

router = APIRouter()
logger = logging.getLogger(__name__)

# --- HARDCODED MOCK DATA ---
MOCK_CLUSTERS = [
    {
        "id": "mock-1", "topicName": "Llama 4 Release Leaks", "category": "Technology", "createdAt": "2026-05-01T12:00:00Z",
        "articles": [{"title": "Meta internal memos hint at Llama 4 training scale", "source": "TechCrunch", "url": "#1"}]
    },
    {
        "id": "mock-2", "topicName": "Global Green Energy Surge", "category": "Science", "createdAt": "2026-05-01T11:00:00Z",
        "articles": [{"title": "Solar capacity exceeds coal for first time globally", "source": "BBC News", "url": "#3"}]
    }
]
for i in range(3, 20):
    MOCK_CLUSTERS.append({
        "id": f"mock-{i}", "topicName": f"Trending Topic {i}", "category": "Technology" if i % 2 == 0 else "Science",
        "createdAt": "2026-05-01T09:00:00Z", "articles": [{"title": f"Story {i}", "source": "InsightMatrix", "url": f"#{i}"}]
    })

async def ensure_db_connected():
    if prisma and not prisma.is_connected():
        try: await prisma.connect()
        except: pass

@router.get("/digest")
async def read_digest(category: str = None, limit: int = 10):
    await ensure_db_connected()
    try:
        where = {}
        if category and category.lower() != "all": where = {"category": category}
        clusters = await prisma.cluster.find_many(where=where, take=limit, order={"createdAt": "desc"}, include={"articles": True})
        if not clusters: return [c for c in MOCK_CLUSTERS if not category or category.lower() == "all" or c["category"] == category][:limit]
        return clusters
    except: return MOCK_CLUSTERS[:limit]

@router.get("/digest/count")
async def get_digest_count(category: str = None):
    await ensure_db_connected()
    try:
        where = {}
        if category and category.lower() != "all": where = {"category": category}
        count = await prisma.cluster.count(where=where)
        if count == 0: return len([c for c in MOCK_CLUSTERS if not category or category.lower() == "all" or c["category"] == category])
        return count
    except: return len(MOCK_CLUSTERS)

@router.get("/articles/saved")
async def get_saved_articles(): return []

@router.get("/categories")
async def get_unique_categories(): return ["Technology", "Politics", "Science", "Sports", "World"]

@router.get("/stats")
async def get_stats(): return {"last_updated": "2026-05-01T15:00:00Z", "sources": 24}

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
    await ensure_db_connected()
    try:
        articles = await prisma.article.count()
        clusters = await prisma.cluster.count()
        return {"articles_in_db": articles, "clusters_in_db": clusters}
    except Exception as e: return {"error": str(e)}
