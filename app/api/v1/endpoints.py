from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.base import get_db
from app.models import news as models

router = APIRouter()

@router.get("/articles", response_model=List[dict])
async def get_articles(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.Article).limit(20))
    articles = result.scalars().all()
    return [{"id": a.id, "title": a.title, "source": a.source} for a in articles]

@router.get("/articles/{article_id}")
async def get_article(article_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.Article).filter(models.Article.id == article_id))
    article = result.scalars().first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return article
