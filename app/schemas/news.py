from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class ArticleBase(BaseModel):
    title: str
    description: Optional[str] = None
    content: Optional[str] = None
    url: str
    source: str
    category: Optional[str] = "General"
    published_at: datetime
    image_url: Optional[str] = None
    sentiment: Optional[float] = 0.0

class ArticleCreate(ArticleBase):
    pass

class Article(ArticleBase):
    id: str
    summary: Optional[str] = None
    cluster_ids: List[str] = []

    class Config:
        from_attributes = True
