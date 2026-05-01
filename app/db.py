import logging

logger = logging.getLogger(__name__)

# Initialize Prisma with a safety wrapper
try:
    from prisma import Prisma
    db = Prisma()
    logger.info("Prisma Client initialized successfully.")
except Exception as e:
    logger.error(f"CRITICAL: Could not load Prisma Client: {e}")
    db = None
