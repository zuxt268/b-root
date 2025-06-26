import redis
import os
import time
from flask import g, current_app


def get_redis():
    if "redis" not in g:
        try:
            redis_host = os.getenv("REDIS_HOST", "localhost")
            redis_port = int(os.getenv("REDIS_PORT", "6379"))
            
            g.redis = redis.Redis(
                host=redis_host,
                port=redis_port,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            
            # Test connection
            g.redis.ping()
            
        except (redis.ConnectionError, redis.TimeoutError, ValueError) as e:
            current_app.logger.error(f"Redis connection failed: {e}")
            # Return a mock Redis client for development
            g.redis = MockRedis()
            
    return g.redis


class MockRedis:
    """Mock Redis client for development when Redis is not available"""
    
    def __init__(self):
        self._data = {}
        self._expires = {}
    
    def _is_expired(self, key):
        """Check if a key has expired"""
        if key in self._expires:
            if time.time() > self._expires[key]:
                # Key has expired, remove it
                self._data.pop(key, None)
                self._expires.pop(key, None)
                return True
        return False
    
    def get(self, key):
        if self._is_expired(key):
            return None
        return self._data.get(key)
    
    def set(self, key, value, ex=None):
        self._data[key] = value
        if ex is not None:
            # Set expiration time
            self._expires[key] = time.time() + ex
        else:
            # Remove expiration if no ex parameter
            self._expires.pop(key, None)
        return True
    
    def delete(self, key):
        deleted = key in self._data
        self._data.pop(key, None)
        self._expires.pop(key, None)
        return deleted
    
    def incr(self, key):
        if self._is_expired(key):
            current_value = 0
        else:
            current_value = int(self._data.get(key, 0))
        new_value = current_value + 1
        self._data[key] = str(new_value)
        return new_value
    
    def expire(self, key, seconds):
        if key in self._data and not self._is_expired(key):
            self._expires[key] = time.time() + seconds
            return True
        return False
    
    def ping(self):
        return True
    
    def close(self):
        # Mock close method for Flask teardown compatibility
        pass
