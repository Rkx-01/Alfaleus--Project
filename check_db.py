import asyncio
from sqlalchemy import text
from app.models.base import engine

async def check():
    async with engine.begin() as conn:
        res1 = await conn.execute(text("SELECT COUNT(*) FROM articles"))
        res2 = await conn.execute(text("SELECT COUNT(*) FROM clusters"))
        print(f"Articles count: {res1.scalar()}")
        print(f"Clusters count: {res2.scalar()}")

asyncio.run(check())
