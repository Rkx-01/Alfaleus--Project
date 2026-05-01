import logging

logger = logging.getLogger(__name__)

# Initialize Prisma globally with extreme safety
try:
    from prisma import Prisma
    db = Prisma()
except Exception as e:
    logger.error(f"CRITICAL: Prisma client could not be loaded: {e}")
    db = None
