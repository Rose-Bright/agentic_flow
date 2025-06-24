"""
Redis client for caching and session management
"""

import json
from typing import Any, Optional, Dict, Union
import asyncio

import redis.asyncio as redis
from redis.asyncio import ConnectionPool

from src.core.config import get_settings
from src.core.logging import get_logger

logger = get_logger(__name__)


class RedisClient:
    """Async Redis client wrapper"""
    
    def __init__(self):
        self._pool: Optional[ConnectionPool] = None
        self._client: Optional[redis.Redis] = None
    
    async def initialize(self):
        """Initialize Redis connection"""
        settings = get_settings()
        
        self._pool = ConnectionPool.from_url(
            settings.redis_url,
            max_connections=settings.redis_max_connections,
            decode_responses=True
        )
        
        self._client = redis.Redis(connection_pool=self._pool)
        
        # Test connection
        try:
            await self._client.ping()
            logger.info("Redis connection established successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    async def close(self):
        """Close Redis connection"""
        if self._client:
            await self._client.close()
        if self._pool:
            await self._pool.disconnect()
    
    async def get(self, key: str) -> Optional[str]:
        """Get value by key"""
        if not self._client:
            raise RuntimeError("Redis client not initialized")
        
        try:
            return await self._client.get(key)
        except Exception as e:
            logger.error(f"Failed to get key {key}: {e}")
            return None
    
    async def set(self, key: str, value: str, ttl: Optional[int] = None) -> bool:
        """Set key-value pair with optional TTL"""
        if not self._client:
            raise RuntimeError("Redis client not initialized")
        
        try:
            result = await self._client.set(key, value, ex=ttl)
            return bool(result)
        except Exception as e:
            logger.error(f"Failed to set key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key"""
        if not self._client:
            raise RuntimeError("Redis client not initialized")
        
        try:
            result = await self._client.delete(key)
            return bool(result)
        except Exception as e:
            logger.error(f"Failed to delete key {key}: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        if not self._client:
            raise RuntimeError("Redis client not initialized")
        
        try:
            result = await self._client.exists(key)
            return bool(result)
        except Exception as e:
            logger.error(f"Failed to check key {key}: {e}")
            return False
    
    async def expire(self, key: str, ttl: int) -> bool:
        """Set expiration time for key"""
        if not self._client:
            raise RuntimeError("Redis client not initialized")
        
        try:
            result = await self._client.expire(key, ttl)
            return bool(result)
        except Exception as e:
            logger.error(f"Failed to set expiration for key {key}: {e}")
            return False
    
    async def hget(self, key: str, field: str) -> Optional[str]:
        """Get hash field value"""
        if not self._client:
            raise RuntimeError("Redis client not initialized")
        
        try:
            return await self._client.hget(key, field)
        except Exception as e:
            logger.error(f"Failed to get hash field {key}:{field}: {e}")
            return None
    
    async def hset(self, key: str, field: str, value: str) -> bool:
        """Set hash field value"""
        if not self._client:
            raise RuntimeError("Redis client not initialized")
        
        try:
            result = await self._client.hset(key, field, value)
            return bool(result)
        except Exception as e:
            logger.error(f"Failed to set hash field {key}:{field}: {e}")
            return False
    
    async def hgetall(self, key: str) -> Dict[str, str]:
        """Get all hash fields"""
        if not self._client:
            raise RuntimeError("Redis client not initialized")
        
        try:
            return await self._client.hgetall(key)
        except Exception as e:
            logger.error(f"Failed to get hash {key}: {e}")
            return {}


# Global Redis client instance
redis_client = RedisClient()


class CacheManager:
    """High-level cache management"""
    
    def __init__(self, client: RedisClient = None):
        self.client = client or redis_client
        self.default_ttl = get_settings().cache_ttl_seconds
    
    async def get_json(self, key: str) -> Optional[Dict[str, Any]]:
        """Get JSON value from cache"""
        value = await self.client.get(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                logger.error(f"Failed to decode JSON from cache key: {key}")
        return None
    
    async def set_json(self, key: str, value: Dict[str, Any], 
                      ttl: Optional[int] = None) -> bool:
        """Set JSON value in cache"""
        try:
            json_value = json.dumps(value, default=str)
            return await self.client.set(key, json_value, ttl or self.default_ttl)
        except Exception as e:
            logger.error(f"Failed to set JSON cache key {key}: {e}")
            return False
    
    async def get_conversation_context(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Get conversation context from cache"""
        key = f"conversation:{conversation_id}:context"
        return await self.get_json(key)
    
    async def set_conversation_context(self, conversation_id: str, 
                                     context: Dict[str, Any]) -> bool:
        """Set conversation context in cache"""
        key = f"conversation:{conversation_id}:context"
        return await self.set_json(key, context)
    
    async def get_agent_state(self, conversation_id: str, agent_type: str) -> Optional[Dict[str, Any]]:
        """Get agent state from cache"""
        key = f"conversation:{conversation_id}:agent:{agent_type}:state"
        return await self.get_json(key)
    
    async def set_agent_state(self, conversation_id: str, agent_type: str, 
                             state: Dict[str, Any]) -> bool:
        """Set agent state in cache"""
        key = f"conversation:{conversation_id}:agent:{agent_type}:state"
        return await self.set_json(key, state)
    
    async def invalidate_conversation(self, conversation_id: str) -> None:
        """Invalidate all cache entries for a conversation"""
        patterns = [
            f"conversation:{conversation_id}:*"
        ]
        
        for pattern in patterns:
            # Note: In production, consider using Redis SCAN for large datasets
            if self.client._client:
                keys = await self.client._client.keys(pattern)
                if keys:
                    await self.client._client.delete(*keys)


# Global cache manager instance
cache_manager = CacheManager()