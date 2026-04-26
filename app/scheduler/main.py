import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.services.collector import fetch_google_news
from app.models.base import AsyncSessionLocal
from app.models.news import Article

logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler()

async def run_news_digest_pipeline():
    logger.info("Starting news collection pipeline...")
    articles_data = await fetch_google_news()
    
    async with AsyncSessionLocal() as db:
        for data in articles_data:
            # Basic duplication check logic
            pass
        await db.commit()

def setup_scheduler():
    scheduler.add_job(run_news_digest_pipeline, 'interval', minutes=30)
    scheduler.start()
    logger.info("Scheduler started.")
