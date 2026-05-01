import logging
from prisma import Prisma

logger = logging.getLogger(__name__)

# Initialize Prisma globally
try:
    db = Prisma()
except Exception as e:
    logger.error(f"Failed to initialize Prisma client: {e}")
    db = None
