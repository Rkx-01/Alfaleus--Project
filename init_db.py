import asyncio
from app.models.base import Base, engine
from app.models.news import Article, Cluster

async def init():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

asyncio.run(init())
