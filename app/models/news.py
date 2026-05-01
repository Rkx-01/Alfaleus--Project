from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.models.base import Base

# Association Table for Many-to-Many relationship
article_cluster_mapping = Table(
    "article_cluster_mapping",
    Base.metadata,
    Column("article_id", Integer, ForeignKey("articles.id"), primary_key=True),
    Column("cluster_id", Integer, ForeignKey("clusters.id"), primary_key=True)
)

class Article(Base):
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    url = Column(String, unique=True, index=True, nullable=False)
    source = Column(String, index=True)
    published_at = Column(DateTime(timezone=True), index=True)
    summary = Column(Text)
    sentiment = Column(String, index=True) # positive / neutral / negative
    
    # Relationship to clusters via the mapping table
    clusters = relationship(
        "Cluster", 
        secondary=article_cluster_mapping, 
        back_populates="articles"
    )

class Cluster(Base):
    __tablename__ = "clusters"

    id = Column(Integer, primary_key=True, index=True)
    topic_name = Column(String, nullable=False, index=True)
    category = Column(String, index=True) # Broad category (Sports, Politics, etc.)
    
    # Relationship back to articles
    articles = relationship(
        "Article", 
        secondary=article_cluster_mapping, 
        back_populates="clusters"
    )

class Subscription(Base):
    __tablename__ = "subscriptions"
    id = Column(Integer, primary_key=True, index=True)
    category = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class SystemStatus(Base):
    __tablename__ = "system_status"
    id = Column(Integer, primary_key=True)
    last_run_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class SavedArticle(Base):
    __tablename__ = "saved_articles"
    id = Column(Integer, primary_key=True, index=True)
    article_id = Column(Integer, ForeignKey("articles.id"), unique=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    article = relationship("Article")
