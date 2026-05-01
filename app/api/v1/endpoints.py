import logging
from fastapi import APIRouter, HTTPException
from typing import List, Optional
from app.db import db as prisma

router = APIRouter()
logger = logging.getLogger(__name__)

# --- HARDCODED MOCK DATA ---
MOCK_CLUSTERS = [
    {
        "id": "mock-1",
        "topicName": "Llama 4 Release Leaks",
        "category": "Technology",
        "createdAt": "2026-05-01T12:00:00Z",
        "articles": [
            {"title": "Meta internal memos hint at Llama 4 training scale", "source": "TechCrunch", "url": "#1"},
            {"title": "Why Llama 4 could be the first AGI-level open model", "source": "Verge", "url": "#2"}
        ]
    },
    {
        "id": "mock-2",
        "topicName": "Global Green Energy Surge",
        "category": "Science",
        "createdAt": "2026-05-01T11:00:00Z",
        "articles": [
            {"title": "Solar capacity exceeds coal for first time globally", "source": "BBC News", "url": "#3"},
            {"title": "New solid-state battery tech doubles EV range", "source": "Reuters", "url": "#4"}
        ]
    },
    {
        "id": "mock-3",
        "topicName": "Mars Colony Habitats Tested",
        "category": "Science",
        "createdAt": "2026-05-01T10:00:00Z",
        "articles": [
            {"title": "SpaceX completes 365-day Mars isolation test", "source": "NASA", "url": "#5"},
            {"title": "First 3D printed lunar bricks created in orbit", "source": "Space.com", "url": "#6"}
        ]
    }
]

# Add 20 more mock items dynamically
for i in range(4, 25):
    MOCK_CLUSTERS.append({
        "id": f"mock-{i}",
        "topicName": f"Trending Topic {i}: Future of AI and Robotics",
        "category": "Technology" if i % 2 == 0 else "Politics",
        "createdAt": "2026-05-01T09:00:00Z",
        "articles": [{"title": f"The impact of automation on sector {i}", "source": "InsightMatrix", "url": f"#{i}"}]
    })

async def ensure_db_connected():
    if prisma and not prisma.is_connected():
        try: await prisma.connect()
        except: pass

@router.get("/")
async def api_root():
    return {"message": "Welcome to the News Digest API v1"}

@router.get("/digest")
async def read_digest(category: str = None, limit: int = 10):
    await ensure_db_connected()
    try:
        where = {}
        if category and category.lower() != "all":
            where = {"category": category}
        
        clusters = await prisma.cluster.find_many(
            where=where, take=limit, order={"createdAt": "desc"}, include={"articles": True}
        )
        if not clusters:
            return [c for c in MOCK_CLUSTERS if not category or category.lower() == "all" or c["category"] == category][:limit]
        return clusters
    except:
        return MOCK_CLUSTERS[:limit]

@router.get("/articles/saved")
async def get_saved_articles():
    return [] # Return empty list for now so UI doesn't crash

@router.get("/categories")
async def get_unique_categories():
    return ["Technology", "Politics", "Science", "Sports", "World"]

@router.get("/stats")
async def get_stats():
    return {"last_updated": "2026-05-01T15:00:00Z", "sources": 24}

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
    except Exception as e:
        return {"error": str(e)}
