from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship
from datetime import datetime
from app.models.base import Base

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
    content = Column(Text)
    url = Column(String, unique=True, index=True)
    source = Column(String)
    published_at = Column(DateTime, default=datetime.utcnow)
    summary = Column(Text)
    sentiment = Column(String)

class Cluster(Base):
    __tablename__ = "clusters"
    id = Column(Integer, primary_key=True, index=True)
    topic_name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    articles = relationship("Article", secondary=article_cluster_mapping)

class Subscription(Base):
    __tablename__ = "subscriptions"
    id = Column(Integer, primary_key=True, index=True)
    category = Column(String, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
