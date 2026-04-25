import asyncio
import logging
from app.models.base import Base, engine
from app.models.news import Article, Cluster

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def init_db():
    logger.info("Initializing database...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database initialized successfully.")

if __name__ == "__main__":
    asyncio.run(init_db())
