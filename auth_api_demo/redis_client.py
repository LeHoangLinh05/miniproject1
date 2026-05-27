import os
import logging
import threading
import time
import fnmatch
import redis

logger = logging.getLogger("auth_api_demo")

class MockRedis:
    """
    An in-memory, thread-safe mock implementation of Redis.
    Mimics basic operations used for blacklisting and activity tracking.
    """
    def __init__(self):
        self._store = {}
        self._expires = {}
        self._lock = threading.Lock()
        logger.warning("Redis server not available. Falling back to in-memory MockRedis.")

    def _is_expired(self, key: str) -> bool:
        if key not in self._store:
            return True
        expiry = self._expires.get(key)
        if expiry is not None and time.time() > expiry:
            # Clean up expired key
            self._store.pop(key, None)
            self._expires.pop(key, None)
            return True
        return False

    def get(self, key: str):
        with self._lock:
            if self._is_expired(key):
                return None
            return self._store.get(key)

    def set(self, key: str, value: str, ex: int = None):
        with self._lock:
            self._store[key] = str(value)
            if ex is not None:
                self._expires[key] = time.time() + ex
            else:
                self._expires.pop(key, None)
            return True

    def delete(self, *keys: str):
        count = 0
        with self._lock:
            for key in keys:
                if key in self._store:
                    self._store.pop(key, None)
                    self._expires.pop(key, None)
                    count += 1
        return count

    def exists(self, key: str):
        with self._lock:
            return 1 if not self._is_expired(key) else 0

    def ttl(self, key: str):
        with self._lock:
            if self._is_expired(key):
                return -2
            expiry = self._expires.get(key)
            if expiry is None:
                return -1
            remaining = int(expiry - time.time())
            return max(0, remaining)

    def keys(self, pattern: str = "*"):
        with self._lock:
            active_keys = []
            # Check expiration of all keys first to clean up
            for key in list(self._store.keys()):
                if not self._is_expired(key):
                    if fnmatch.fnmatch(key, pattern):
                        active_keys.append(key)
            return active_keys

    def expire(self, key: str, ex: int):
        with self._lock:
            if self._is_expired(key):
                return 0
            self._expires[key] = time.time() + ex
            return 1

# Configuration
REDIS_HOST = os.getenv("REDIS_HOST", "127.0.0.1")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))

# Initialize Client
try:
    # Try to connect to real Redis
    redis_client = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        db=REDIS_DB,
        decode_responses=True,  # Automatically decode bytes to strings
        socket_connect_timeout=1.5
    )
    redis_client.ping()
    logger.info(f"Successfully connected to Redis at {REDIS_HOST}:{REDIS_PORT}")
except Exception as e:
    redis_client = MockRedis()
