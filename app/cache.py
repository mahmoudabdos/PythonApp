import redis
import json
from typing import Any

# Initialize Redis client
redis_client = redis.Redis(host='redis', port=6379, db=0)

def get_from_cache(key: str) -> Any:
    """Get value from Redis cache"""
    value = redis_client.get(key)
    if value:
        return json.loads(value)
    return None

def set_in_cache(key: str, value: Any, expire: int = 3600) -> None:
    """Set value in Redis cache with expiration time in seconds"""
    redis_client.setex(key, expire, json.dumps(value))

def delete_from_cache(key: str) -> None:
    """Delete value from Redis cache"""
    redis_client.delete(key) 