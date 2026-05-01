import logging
import asyncio

logger = logging.getLogger(__name__)

try:
    from prisma import Prisma
    db = Prisma()
    logger.info("Prisma Client initialized.")
except Exception as e:
    logger.error(f"CRITICAL: Prisma Import Failed: {e}")
    db = None

async def check_db_health():
    if not db:
        return False, "Prisma client not initialized"
    
    try:
        if not db.is_connected():
            logger.info("Attempting diagnostic connection...")
            await db.connect()
        
        # Try a simple count query
        count = await db.article.count()
        return True, f"Connected! Article count: {count}"
    except Exception as e:
        logger.error(f"Database Health Check Failed: {e}")
        return False, str(e)
