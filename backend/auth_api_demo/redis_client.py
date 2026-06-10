import logging

import redis

from .config import settings

logger = logging.getLogger(__name__)

# Initialize Client
if settings.REDIS_URL:
    # Use full URL connection (useful for Upstash, Heroku, Render, etc.)
    redis_client = redis.Redis.from_url(
        settings.REDIS_URL, decode_responses=True, socket_connect_timeout=3.0
    )
else:
    # Fallback to host/port
    redis_client = redis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=settings.REDIS_DB,
        decode_responses=True,  # Automatically decode bytes to strings
        socket_connect_timeout=1.5,
    )

try:
    redis_client.ping()
    logger.info("Successfully connected to Redis server.")
except Exception as e:
    logger.error(f"Failed to connect to Redis: {e}")
    raise
