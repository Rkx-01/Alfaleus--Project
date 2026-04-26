import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.services.collector import fetch_google_news
from app.models.base import AsyncSessionLocal
from app.models.news import Article
from sqlalchemy import select

logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler()

async def run_news_digest_pipeline():
    logger.info("Starting news collection pipeline...")
    articles_data = await fetch_google_news()
    
    async with AsyncSessionLocal() as db:
        for data in articles_data:
            stmt = select(Article).filter(Article.url == data["url"])
            result = await db.execute(stmt)
            if not result.scalars().first():
                new_article = Article(
                    title=data["title"],
                    url=data["url"],
                    source=data["source"]
                )
                db.add(new_article)
        await db.commit()
    logger.info("Collection complete.")

def setup_scheduler():
    scheduler.add_job(run_news_digest_pipeline, 'interval', minutes=30)
    scheduler.start()
