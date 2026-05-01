from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class ArticleBase(BaseModel):
    title: str = Field(..., description="The headline of the news article", example="AI Revolutionizes News Consumption")
    content: str = Field(..., description="The full body content of the article")
    url: str = Field(..., description="Original URL of the article", example="https://example.com/news/1")
    source: str = Field(..., description="The name of the publishing source", example="TechCrunch")
    published_at: Optional[datetime] = Field(None, description="The ISO timestamp of publication")
    summary: Optional[str] = Field(None, description="AI-generated 2-line summary of the article")
    sentiment: Optional[str] = Field(None, description="Sentiment analysis result: positive / neutral / negative", example="positive")

class ArticleCreate(ArticleBase):
    pass

class Article(ArticleBase):
    id: int = Field(..., description="Database unique identifier")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "title": "AI Revolutionizes News Consumption",
                "content": "Full article content goes here...",
                "url": "https://example.com/news/1",
                "source": "TechCrunch",
                "published_at": "2026-04-25T13:00:00Z",
                "summary": "AI is changing how we read news.\nIt's making summaries faster and better.",
                "sentiment": "positive"
            }
        }

class ClusterBase(BaseModel):
    topic_name: str = Field(..., description="The AI-generated name for the news topic", example="Artificial Intelligence / Future")

class ClusterCreate(ClusterBase):
    pass

class Cluster(ClusterBase):
    id: int = Field(..., description="Database unique identifier for the cluster")
    articles: List[Article] = Field(default=[], description="List of articles belonging to this topic cluster")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "topic_name": "Artificial Intelligence / Future",
                "articles": [
                    {
                        "id": 1,
                        "title": "AI Revolutionizes News Consumption",
                        "content": "...",
                        "url": "https://example.com/news/1",
                        "source": "TechCrunch",
                        "published_at": "2026-04-25T13:00:00Z",
                        "summary": "AI is changing how we read news.",
                        "sentiment": "positive"
                    }
                ]
            }
        }
