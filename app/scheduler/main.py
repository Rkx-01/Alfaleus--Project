import logging
import asyncio
from typing import List
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.services.collector import collect_all_news
from app.services.processor import cluster_articles, generate_summary, get_sentiment
from app.models.base import AsyncSessionLocal
from app.models.news import Article, Cluster, SystemStatus
from app.utils.config import settings

logger = logging.getLogger(__name__)

async def run_news_digest_pipeline():
    """
    Optimized News Pipeline:
    - Async DB queries
    - Avoids N+1 queries
    - Batch summarization
    """
    logger.info("Starting optimized news pipeline...")
    
    async with AsyncSessionLocal() as db:
        try:
            # 1. Fetch & Store
            raw_articles = await collect_all_news()
            added_count = 0
            for data in raw_articles:
                stmt = select(Article).filter(Article.url == data.url)
                result = await db.execute(stmt)
                if not result.scalars().first():
                    db.add(Article(**data.model_dump()))
                    added_count += 1
            await db.commit()
            logger.info(f"Persisted {added_count} new articles.")

            # 2. Batch Summarization
            stmt = select(Article).filter(Article.summary == None)
            result = await db.execute(stmt)
            to_summarize = result.scalars().all()
            
            if to_summarize:
                tasks = [generate_summary(a.content or a.title) for a in to_summarize]
                summaries = await asyncio.gather(*tasks, return_exceptions=True)
                for article, summary in zip(to_summarize, summaries):
                    if isinstance(summary, Exception):
                        logger.warning(f"Summarization failed for {article.id}: {summary}")
                        continue
                    article.summary = summary
                    article.sentiment = get_sentiment(article.summary or article.title)
                await db.commit()
                logger.info(f"Generated {len(to_summarize)} summaries in batch.")

            # 3. Clustering & Mapping
            stmt = select(Article).options(selectinload(Article.clusters)).filter(~Article.clusters.any())
            result = await db.execute(stmt)
            unclustered = result.scalars().all()
            
            if unclustered:
                clusters_data = await cluster_articles(unclustered)
                for c_data in clusters_data:
                    if len(c_data["articles"]) >= 1:
                        new_cluster = Cluster(
                            topic_name=c_data["topic_name"],
                            category=c_data["category"]
                        )
                        db.add(new_cluster)
                        for article in c_data["articles"]:
                            article.clusters.append(new_cluster)
                await db.commit()
                logger.info(f"Created {len(clusters_data)} clusters.")

            # 4. Update System Status
            from datetime import datetime, timezone
            status_stmt = select(SystemStatus).filter(SystemStatus.id == 1)
            status_res = await db.execute(status_stmt)
            status = status_res.scalars().first()
            if not status:
                status = SystemStatus(id=1, last_run_at=datetime.now(timezone.utc))
                db.add(status)
            else:
                status.last_run_at = datetime.now(timezone.utc)
            await db.commit()

        except Exception as e:
            await db.rollback()
            logger.error(f"Pipeline failed: {e}", exc_info=True)

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
    logger.info("Scheduler initialized.")
