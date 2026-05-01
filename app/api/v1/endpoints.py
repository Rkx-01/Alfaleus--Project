from fastapi import APIRouter, HTTPException
from typing import List, Optional
from app.main import prisma

router = APIRouter()

@router.get("/digest/count")
async def get_clusters_count(category: str = None):
    where = {}
    if category and category.lower() != "all":
        where = {"category": category}
    
    count = await prisma.cluster.count(where=where)
    return {"total": count}

@router.get("/categories")
async def get_unique_categories():
    clusters = await prisma.cluster.find_many(
        distinct=["category"],
    )
    categories = [c.category for c in clusters if c.category]
    return sorted(list(set(categories)))

@router.get(
    "/digest", 
    summary="Get News Digest",
    description="Retrieve a complete list of news clusters. Each cluster contains a topic name and its associated articles."
)
async def read_digest(
    skip: int = 0, 
    limit: int = 20,
    category: str = None
):
    where = {}
    if category and category.lower() != "all":
        where = {"category": category}
        
    clusters = await prisma.cluster.find_many(
        where=where,
        take=limit,
        skip=skip,
        include={"articles": True},
        order={"createdAt": "desc"}
    )
    return clusters

@router.get(
    "/topic/{name}", 
    summary="Get Articles by Topic"
)
async def read_articles_by_topic(name: str):
    cluster = await prisma.cluster.find_first(
        where={"topicName": {"contains": name, "mode": "insensitive"}},
        include={"articles": True}
    )
    
    if not cluster:
        raise HTTPException(
            status_code=404, 
            detail=f"Topic '{name}' not found."
        )
        
    return cluster.articles

@router.get("/subscriptions", response_model=List[str])
async def get_subscriptions():
    subs = await prisma.subscription.find_many()
    return [s.category for s in subs]

@router.post("/subscriptions/{category}")
async def subscribe_category(category: str):
    existing = await prisma.subscription.find_unique(where={"category": category})
    if existing:
        return {"message": f"Already subscribed to {category}"}
    
    await prisma.subscription.create(data={"category": category})
    return {"message": f"Successfully subscribed to {category}"}

@router.delete("/subscriptions/{category}")
async def unsubscribe_category(category: str):
    await prisma.subscription.delete(where={"category": category})
    return {"message": f"Successfully unsubscribed from {category}"}

@router.get("/stats")
async def get_stats():
    # 1. Last run
    status = await prisma.systemstatus.find_first(order={"lastRunAt": "desc"})
    last_updated_str = status.lastRunAt.isoformat() if status else None

    # 2. Source count (Prisma doesn't have a direct distinct count for a field in MongoDB easily without grouping)
    # We'll use find_many with distinct or just a raw count for now
    articles = await prisma.article.find_many(distinct=["source"])
    source_count = len(articles)
    
    return {
        "last_updated": last_updated_str,
        "sources": source_count
    }

@router.get("/articles/saved")
async def get_saved_articles():
    # Find articles that have at least one SavedArticle record
    saved = await prisma.savedarticle.find_many(include={"article": True})
    return [s.article for s in saved]

@router.post("/articles/{article_id}/save")
async def save_article(article_id: str):
    existing = await prisma.savedarticle.find_first(where={"articleId": article_id})
    if existing:
        return {"message": "Already saved"}
    
    await prisma.savedarticle.create(data={"articleId": article_id})
    return {"message": "Article saved"}

@router.delete("/articles/{article_id}/save")
async def unsave_article(article_id: str):
    # We need to find the ID of the SavedArticle record to delete it
    record = await prisma.savedarticle.find_first(where={"articleId": article_id})
    if record:
        await prisma.savedarticle.delete(where={"id": record.id})
    return {"message": "Article removed from saved"}

@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "mode": "nosql",
        "version": "2.0.0"
    }

@router.get("/debug/trigger")
async def remote_trigger():
    from app.scheduler.main import run_news_digest_pipeline
    import asyncio
    asyncio.create_task(run_news_digest_pipeline())
    return {"message": "Pipeline triggered in background (MongoDB mode)."}

@router.get("/debug/pulse")
async def pulse_check():
    art_count = await prisma.article.count()
    sum_count = await prisma.article.count(where={"summary": {"not": None}})
    clu_count = await prisma.cluster.count()
    return {
        "total_articles": art_count,
        "summarized_articles": sum_count,
        "total_clusters": clu_count
    }
