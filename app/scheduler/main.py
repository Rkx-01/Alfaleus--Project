import logging
import asyncio
from datetime import datetime, timezone
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.services.collector import collect_all_news
from app.services.processor import cluster_articles_motor, generate_summary, get_sentiment
from app.db import db_manager
from app.utils.config import settings
from bson import ObjectId

logger = logging.getLogger(__name__)

async def run_news_digest_pipeline():
    logger.info("📡 Starting news collection pipeline (Motor Deep Dive Fix)...")
    
    if db_manager.db is None:
        await db_manager.connect()
    
    if db_manager.db is None:
        logger.error("Database still not connected. Aborting.")
        return

    try:
        # 1. Fetch
        raw_articles = await collect_all_news()
        if not raw_articles:
            logger.warning("No articles fetched from any source.")
            return
            
        logger.info(f"📥 Fetched {len(raw_articles)} articles.")
        
        # 2. Store (Upsert)
        for data in raw_articles:
            try:
                await db_manager.db.articles.update_one(
                    {"url": data.url},
                    {"$set": {
                        "title": data.title,
                        "url": data.url,
                        "source": data.source,
                        "category": data.category or "General",
                        "content": data.content,
                        "publishedAt": data.published_at,
                        "updatedAt": datetime.now(timezone.utc)
                    }},
                    upsert=True
                )
            except Exception as e:
                logger.error(f"Error upserting {data.url}: {e}")

        # 3. Create Immediate Topics (Safety fallback for UI)
        # We find articles with no clusters and create topics for them
        unclustered = await db_manager.db.articles.find({"clusterIds": {"$size": 0}}).limit(20).to_list(length=20)
        
        for article in unclustered:
            try:
                # Create a simple 1-article topic immediately
                new_cluster = {
                    "topicName": article["title"][:60],
                    "category": article.get("category", "General"),
                    "createdAt": datetime.now(timezone.utc),
                    "articleIds": [article["_id"]]
                }
                c_result = await db_manager.db.clusters.insert_one(new_cluster)
                await db_manager.db.articles.update_one(
                    {"_id": article["_id"]},
                    {"$push": {"clusterIds": str(c_result.inserted_id)}}
                )
            except: continue

        logger.info("📁 Immediate topics created for UI population.")

    except Exception as e:
        logger.error(f"❌ Pipeline Failed: {e}", exc_info=True)

scheduler = AsyncIOScheduler()

def setup_scheduler():
    if not scheduler.get_job("news_pipeline_job"):
        scheduler.add_job(
            run_news_digest_pipeline, 
            "interval", 
            minutes=settings.COLLECT_INTERVAL_MINUTES,
            id="news_pipeline_job",
            next_run_time=datetime.now()
        )
    if not scheduler.running:
        scheduler.start()
        logger.info("⏰ Scheduler started (Deep Dive Fix).")
