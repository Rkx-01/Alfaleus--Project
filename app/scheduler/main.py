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
    Optimized News Pipeline for MongoDB + Prisma
    """
    logger.info("Starting NoSQL news pipeline...")
    
    try:
        # 1. Fetch & Store (Upsert by URL)
        raw_articles = await collect_all_news()
        added_count = 0
        for data in raw_articles:
            # Upsert ensures no duplicates by URL
            await prisma.article.upsert(
                where={"url": data.url},
                data={
                    "create": {
                        "title": data.title,
                        "url": data.url,
                        "source": data.source,
                        "category": data.category,
                        "content": data.content,
                        "publishedAt": data.published_at
                    },
                    "update": {
                        "title": data.title # Minor update if exists
                    }
                }
            )
            added_count += 1
        logger.info(f"Processed {added_count} articles (Upsert).")

        # 2. Batch Summarization
        to_summarize = await prisma.article.find_many(
            where={"summary": None}
        )
        
        if to_summarize:
            tasks = [generate_summary(a.content or a.title) for a in to_summarize]
            summaries = await asyncio.gather(*tasks, return_exceptions=True)
            for article, summary in zip(to_summarize, summaries):
                if isinstance(summary, Exception):
                    logger.warning(f"Summarization failed for {article.id}: {summary}")
                    continue
                
                sentiment = get_sentiment(summary or article.title)
                await prisma.article.update(
                    where={"id": article.id},
                    data={
                        "summary": summary,
                        "sentiment": sentiment
                    }
                )
            logger.info(f"Generated {len(to_summarize)} summaries.")

        # 3. Clustering
        # Find articles that are not in any cluster
        unclustered = await prisma.article.find_many(
            where={"clusterIds": {"isEmpty": True}}
        )
        
        if unclustered:
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
            logger.info(f"Created {len(clusters_data)} NoSQL clusters.")

        # 4. Update System Status
        # MongoDB uses string IDs. We'll use a fixed ID for the status record if possible,
        # or just find the first one.
        status = await prisma.systemstatus.find_first()
        if not status:
            await prisma.systemstatus.create(data={"lastRunAt": datetime.now(timezone.utc)})
        else:
            await prisma.systemstatus.update(
                where={"id": status.id},
                data={"lastRunAt": datetime.now(timezone.utc)}
            )

    except Exception as e:
        logger.error(f"NoSQL Pipeline failed: {e}", exc_info=True)

scheduler = AsyncIOScheduler()

def setup_scheduler():
    scheduler.add_job(
        run_news_digest_pipeline, 
        "interval", 
        minutes=settings.COLLECT_INTERVAL_MINUTES,
        id="news_pipeline_job",
        replace_existing=True
    )
    scheduler.start()
    logger.info("Scheduler initialized with MongoDB support.")
