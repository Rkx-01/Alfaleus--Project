from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.base import get_db
from app.models import news as models

router = APIRouter()

@router.get("/digest")
async def get_digest(category: str = "All", db: AsyncSession = Depends(get_db)):
    stmt = select(models.Cluster).join(models.Cluster.articles)
    if category != "All":
        stmt = stmt.filter(models.Article.source == category)
    result = await db.execute(stmt)
    return result.scalars().unique().all()
