import os
import logging
import threading
import time
import fnmatch
import redis

logger = logging.getLogger("auth_api_demo")


# Configuration
REDIS_URL = os.getenv("REDIS_URL")
REDIS_HOST = os.getenv("REDIS_HOST", "127.0.0.1")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))

# Initialize Client
try:
    # Try to connect to Redis
    if REDIS_URL:
        # Use full URL connection (useful for Upstash, Heroku, Render, etc.)
        redis_client = redis.Redis.from_url(
            REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=3.0
        )
    else:
        # Fallback to host/port
        redis_client = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            decode_responses=True,  # Automatically decode bytes to strings
            socket_connect_timeout=1.5
        )
    redis_client.ping()
    logger.info("Successfully connected to Redis server.")
except Exception as e:
    logger.error(f"Failed to connect to Redis: {e}")
    redis_client = MockRedis()
