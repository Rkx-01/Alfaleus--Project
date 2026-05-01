import logging
import asyncio
from datetime import datetime, timezone
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.services.collector import collect_all_news
from app.services.processor import cluster_articles, generate_summary, get_sentiment
from app.db import db as prisma
from app.utils.config import settings

logger = logging.getLogger(__name__)

async def run_news_digest_pipeline():
    """
    Stabilized News Pipeline for MongoDB + Prisma
    """
    logger.info("📡 Starting news collection pipeline...")
    
    try:
        # 1. Fetch & Store
        raw_articles = await collect_all_news()
        logger.info(f"📥 Fetched {len(raw_articles)} articles from raw sources.")
        
        if not raw_articles:
            logger.warning("⚠️ No articles found in sources. Exiting pipeline.")
            return

        added_count = 0
        for data in raw_articles:
            try:
                await prisma.article.upsert(
                    where={"url": data.url},
                    data={
                        "create": {
                            "title": data.title,
                            "url": data.url,
                            "source": data.source,
                            "category": data.category or "General",
                            "content": data.content,
                            "publishedAt": data.published_at
                        },
                        "update": {
                            "title": data.title 
                        }
                    }
                )
                added_count += 1
            except Exception as e:
                logger.error(f"Error upserting article {data.url}: {e}")

        logger.info(f"✅ Database updated: {added_count} articles processed.")

        # 2. AI Summarization
        to_summarize = await prisma.article.find_many(
            where={"summary": None},
            take=30 # Limit to avoid hitting LLM rate limits
        )
        
        if to_summarize:
            logger.info(f"🤖 Summarizing {len(to_summarize)} new articles using AI...")
            tasks = [generate_summary(a.content or a.title) for a in to_summarize]
            summaries = await asyncio.gather(*tasks, return_exceptions=True)
            
            for article, summary in zip(to_summarize, summaries):
                if isinstance(summary, Exception) or not summary:
                    continue
                
                sentiment = get_sentiment(summary)
                await prisma.article.update(
                    where={"id": article.id},
                    data={"summary": summary, "sentiment": sentiment}
                )
            logger.info("✨ Summarization complete.")

        # 3. Intelligent Clustering
        # In MongoDB, we'll fetch articles and filter in Python to find unclustered ones
        # This is safer than relying on complex MongoDB 'isEmpty' filters in Prisma
        all_articles = await prisma.article.find_many(
            where={"summary": {"not": None}},
            order={"createdAt": "desc"},
            take=100
        )
        
        unclustered = [a for a in all_articles if not a.clusterIds]
        
        if len(unclustered) < 3:
            logger.info(f"ℹ️ Only {len(unclustered)} unclustered articles. Waiting for more data before clustering.")
        else:
            logger.info(f"🧩 Clustering {len(unclustered)} articles into topics...")
            clusters_data = await cluster_articles(unclustered)
            
            for c_data in clusters_data:
                if len(c_data["articles"]) >= 1:
                    await prisma.cluster.create(
                        data={
                            "topicName": c_data["topic_name"],
                            "category": c_data["category"],
                            "articles": {
                                "connect": [{"id": a.id} for a in c_data["articles"]]
                            }
                        }
                    )
            logger.info(f"📁 Created {len(clusters_data)} new trending topics.")

        # 4. Status Update
        status = await prisma.systemstatus.find_first()
        if not status:
            await prisma.systemstatus.create(data={"lastRunAt": datetime.now(timezone.utc)})
        else:
            await prisma.systemstatus.update(
                where={"id": status.id},
                data={"lastRunAt": datetime.now(timezone.utc)}
            )

    except Exception as e:
        logger.error(f"❌ Pipeline Failed: {e}", exc_info=True)

scheduler = AsyncIOScheduler()

def setup_scheduler():
    # Only add job if it doesn't exist
    if not scheduler.get_job("news_pipeline_job"):
        scheduler.add_job(
            run_news_digest_pipeline, 
            "interval", 
            minutes=settings.COLLECT_INTERVAL_MINUTES,
            id="news_pipeline_job"
        )
    if not scheduler.running:
        scheduler.start()
        logger.info("⏰ Scheduler started.")
