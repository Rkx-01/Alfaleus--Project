import logging
import os
from motor.motor_asyncio import AsyncIOMotorClient

logger = logging.getLogger(__name__)

class Database:
    client: AsyncIOMotorClient = None
    db = None

    async def connect(self):
        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            logger.error("DATABASE_URL not found!")
            return
        
        try:
            self.client = AsyncIOMotorClient(db_url)
            # Force the database name to 'InsightMatrix'
            self.db = self.client["InsightMatrix"]
            # Test connection
            await self.client.admin.command('ping')
            logger.info("Successfully connected to MongoDB via Motor!")
        except Exception as e:
            logger.error(f"Motor connection failed: {e}")

    async def disconnect(self):
        if self.client:
            self.client.close()
            logger.info("Motor connection closed.")

db_manager = Database()

# Helper for health check
async def check_db_health():
    if not db_manager.client:
        return False, "Motor client not initialized"
    try:
        await db_manager.client.admin.command('ping')
        return True, "Motor is healthy"
    except Exception as e:
        return False, str(e)
