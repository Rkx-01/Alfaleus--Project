import asyncio
from sqlalchemy import text
from app.models.base import engine

async def drop():
    async with engine.begin() as conn:
        await conn.execute(text("DROP TABLE IF EXISTS article_cluster_mapping CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS articles CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS clusters CASCADE"))

asyncio.run(drop())
