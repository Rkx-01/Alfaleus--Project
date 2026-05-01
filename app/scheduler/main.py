import logging
import asyncio
from datetime import datetime, timezone
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.services.collector import collect_all_news
from app.services.processor import cluster_articles, generate_summary, get_sentiment
from app.db import db_manager
from app.utils.config import settings
from bson import ObjectId

logger = logging.getLogger(__name__)

async def run_news_digest_pipeline():
    """
    Stabilized News Pipeline using Motor (Direct MongoDB)
    """
    logger.info("📡 Starting news collection pipeline (Motor)...")
    
    if db_manager.db is None:
        logger.error("Database not connected. Skipping pipeline.")
        return

    try:
        # 1. Fetch
        raw_articles = await collect_all_news()
        logger.info(f"📥 Fetched {len(raw_articles)} articles.")
        
        # 2. Store (Upsert)
        article_ids = []
        for data in raw_articles:
            try:
                # Use update_one with upsert=True for URL uniqueness
                result = await db_manager.db.articles.update_one(
                    {"url": data.url},
                    {"$setOnInsert": {
                        "title": data.title,
                        "url": data.url,
                        "source": data.source,
                        "category": data.category or "General",
                        "content": data.content,
                        "publishedAt": data.published_at,
                        "summary": None,
                        "clusterIds": []
                    }},
                    upsert=True
                )
                # Find the ID (whether created or existed)
                doc = await db_manager.db.articles.find_one({"url": data.url})
                if doc: article_ids.append(doc["_id"])
            except Exception as e:
                logger.error(f"Error upserting {data.url}: {e}")

        # 3. AI Summarization
        to_summarize = await db_manager.db.articles.find({"summary": None}).limit(20).to_list(length=20)
        
        if to_summarize:
            logger.info(f"🤖 AI is summarizing {len(to_summarize)} articles...")
            tasks = [generate_summary(a.get("content") or a.get("title")) for a in to_summarize]
            summaries = await asyncio.gather(*tasks, return_exceptions=True)
            
            for article, summary in zip(to_summarize, summaries):
                if isinstance(summary, Exception) or not summary: continue
                sentiment = get_sentiment(summary)
                await db_manager.db.articles.update_one(
                    {"_id": article["_id"]},
                    {"$set": {"summary": summary, "sentiment": sentiment}}
                )

        # 4. Intelligent Clustering
        # Simplified: Find articles with summaries but no clusters
        all_articles = await db_manager.db.articles.find(
            {"summary": {"$ne": None}, "clusterIds": {"$size": 0}}
        ).sort("createdAt", -1).limit(100).to_list(length=100)
        
        if all_articles:
            # We need to adapt cluster_articles to handle dicts instead of Prisma models
            from app.services.processor import cluster_articles_motor
            clusters_data = await cluster_articles_motor(all_articles)
            
            for c_data in clusters_data:
                if len(c_data["articles"]) >= 1:
                    new_cluster = {
                        "topicName": c_data["topic_name"],
                        "category": c_data["category"],
                        "createdAt": datetime.now(timezone.utc),
                        "articleIds": [a["_id"] for a in c_data["articles"]]
                    }
                    c_result = await db_manager.db.clusters.insert_one(new_cluster)
                    # Update articles with the new cluster ID
                    await db_manager.db.articles.update_many(
                        {"_id": {"$in": [a["_id"] for a in c_data["articles"]]}},
                        {"$push": {"clusterIds": str(c_result.inserted_id)}}
                    )
            logger.info(f"📁 Created {len(clusters_data)} new topics.")

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
        logger.info("⏰ Scheduler started (Motor Mode).")
