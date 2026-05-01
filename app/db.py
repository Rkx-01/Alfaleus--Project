import logging
import asyncio
import os

logger = logging.getLogger(__name__)

try:
    from prisma import Prisma
    # Explicitly pass the URL from environment to the client
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        db = Prisma(datasource={"url": db_url})
        logger.info("Prisma Client initialized with environment URL.")
    else:
        db = Prisma()
        logger.warning("DATABASE_URL not found in environment. Using default.")
except Exception as e:
    logger.error(f"CRITICAL: Prisma Import Failed: {e}")
    db = None

async def check_db_health():
    if not db:
        return False, "Prisma client not initialized"
    
    try:
        # Check if connected, if not, try connecting with a timeout
        if not db.is_connected():
            logger.info("Attempting diagnostic connection...")
            await asyncio.wait_for(db.connect(), timeout=10.0)
        
        count = await db.article.count()
        return True, f"Connected! Article count: {count}"
    except asyncio.TimeoutError:
        return False, "Connection timed out after 10 seconds."
    except Exception as e:
        logger.error(f"Database Health Check Failed: {e}")
        return False, str(e)
