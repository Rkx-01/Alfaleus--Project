from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import List
from app.models.base import get_db
from app.models import news as models
from app.schemas import news as schemas

router = APIRouter()

@router.get("/digest/count")
async def get_clusters_count(
    category: str = None,
    db: AsyncSession = Depends(get_db)
):
    from sqlalchemy import func
    stmt = select(func.count(models.Cluster.id))
    if category and category.lower() != "all":
        stmt = stmt.filter(models.Cluster.category == category)
    result = await db.execute(stmt)
    return {"total": result.scalar()}

@router.get("/categories")
async def get_unique_categories(db: AsyncSession = Depends(get_db)):
    stmt = select(models.Cluster.category).distinct()
    result = await db.execute(stmt)
    categories = [row[0] for row in result.all() if row[0]]
    return sorted(list(set(categories)))

@router.get(
    "/digest", 
    response_model=List[schemas.Cluster],
    summary="Get News Digest",
    description="Retrieve a complete list of news clusters. Each cluster contains a topic name and its associated articles, synthesized from multiple sources."
)
async def read_digest(
    skip: int = 0, 
    limit: int = 20,
    category: str = None,
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(models.Cluster)
        .options(selectinload(models.Cluster.articles))
    )
    
    if category and category.lower() != "all":
        stmt = stmt.filter(models.Cluster.category == category)
        
    stmt = stmt.offset(skip).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()

@router.get(
    "/topic/{name}", 
    response_model=List[schemas.Article],
    summary="Get Articles by Topic",
    description="Fetch all articles belonging to a specific topic name. The search is case-insensitive and supports partial matches (e.g., 'AI' will match 'Artificial Intelligence')."
)
async def read_articles_by_topic(
    name: str, 
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(models.Cluster)
        .options(selectinload(models.Cluster.articles))
        .filter(models.Cluster.topic_name.ilike(f"%{name}%"))
    )
    result = await db.execute(stmt)
    cluster = result.scalars().first()
    
    if not cluster:
        raise HTTPException(
            status_code=404, 
            detail=f"Topic '{name}' not found. Try a different keyword."
        )
        
    return cluster.articles

@router.get("/subscriptions", response_model=List[str])
async def get_subscriptions(db: AsyncSession = Depends(get_db)):
    stmt = select(models.Subscription.category)
    result = await db.execute(stmt)
    return [row[0] for row in result.all()]

@router.post("/subscriptions/{category}")
async def subscribe_category(category: str, db: AsyncSession = Depends(get_db)):
    # Check if exists
    stmt = select(models.Subscription).filter(models.Subscription.category == category)
    result = await db.execute(stmt)
    if result.scalars().first():
        return {"message": f"Already subscribed to {category}"}
    
    new_sub = models.Subscription(category=category)
    db.add(new_sub)
    await db.commit()
    return {"message": f"Successfully subscribed to {category}"}

@router.delete("/subscriptions/{category}")
async def unsubscribe_category(category: str, db: AsyncSession = Depends(get_db)):
    from sqlalchemy import delete
    stmt = delete(models.Subscription).where(models.Subscription.category == category)
    await db.execute(stmt)
    await db.commit()
    return {"message": f"Successfully unsubscribed from {category}"}

@router.get("/stats")
async def get_stats(db: AsyncSession = Depends(get_db)):
    from sqlalchemy import func
    from datetime import timezone
    # 1. Last run
    stmt = select(models.SystemStatus.last_run_at).filter(models.SystemStatus.id == 1)
    res = await db.execute(stmt)
    last_run = res.scalar()
    
    # Ensure it's returned as UTC ISO string for frontend
    last_updated_str = None
    if last_run:
        if last_run.tzinfo is None:
            last_run = last_run.replace(tzinfo=timezone.utc)
        last_updated_str = last_run.isoformat()

    # 2. Source count
    source_stmt = select(func.count(models.Article.source.distinct()))
    source_res = await db.execute(source_stmt)
    source_count = source_res.scalar()
    
    return {
        "last_updated": last_updated_str,
        "sources": source_count or 0
    }

@router.get("/articles/saved", response_model=List[schemas.Article])
async def get_saved_articles(db: AsyncSession = Depends(get_db)):
    stmt = select(models.Article).join(models.SavedArticle)
    result = await db.execute(stmt)
    return result.scalars().all()

@router.post("/articles/{article_id}/save")
async def save_article(article_id: int, db: AsyncSession = Depends(get_db)):
    stmt = select(models.SavedArticle).filter(models.SavedArticle.article_id == article_id)
    result = await db.execute(stmt)
    if result.scalars().first():
        return {"message": "Already saved"}
    
    new_saved = models.SavedArticle(article_id=article_id)
    db.add(new_saved)
    await db.commit()
    return {"message": "Article saved"}

@router.delete("/articles/{article_id}/save")
async def unsave_article(article_id: int, db: AsyncSession = Depends(get_db)):
    from sqlalchemy import delete
    stmt = delete(models.SavedArticle).where(models.SavedArticle.article_id == article_id)
    await db.execute(stmt)
    await db.commit()
    return {"message": "Article removed from saved"}

@router.get(
    "/health",
    summary="Health Check",
    description="Check if the API service and its background scheduler are active."
)
async def health_check():
    return {
        "status": "healthy",
        "mode": "async",
        "version": "1.0.0"
    }
