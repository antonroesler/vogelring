"""
Simple in-memory cache utility for frequently accessed data
"""
import logging
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, Optional
from threading import Lock

logger = logging.getLogger(__name__)


class SimpleCache:
    """
    Simple in-memory cache with TTL support
    Optimized for single-process applications like the Raspberry Pi deployment
    """
    
    def __init__(self, default_ttl: timedelta = timedelta(minutes=5)):
        self.default_ttl = default_ttl
        self._cache: Dict[str, tuple[Any, datetime]] = {}
        self._lock = Lock()
    
    def get(self, key: str, fetch_func: Callable[[], Any], ttl: Optional[timedelta] = None) -> Any:
        """
        Get value from cache or fetch using provided function
        
        Args:
            key: Cache key
            fetch_func: Function to call if cache miss or expired
            ttl: Time to live for this entry (uses default if None)
        
        Returns:
            Cached or freshly fetched value
        """
        ttl = ttl or self.default_ttl
        now = datetime.now()
        
        with self._lock:
            if key in self._cache:
                value, timestamp = self._cache[key]
                if now - timestamp < ttl:
                    logger.debug(f"Cache hit for key: {key}")
                    return value
                else:
                    logger.debug(f"Cache expired for key: {key}")
            else:
                logger.debug(f"Cache miss for key: {key}")
            
            # Cache miss or expired, fetch new data
            try:
                value = fetch_func()
                self._cache[key] = (value, now)
                logger.debug(f"Cached new value for key: {key}")
                return value
            except Exception as e:
                logger.error(f"Error fetching data for cache key {key}: {e}")
                # Return stale data if available, otherwise re-raise
                if key in self._cache:
                    logger.warning(f"Returning stale data for key: {key}")
                    return self._cache[key][0]
                raise
    
    def set(self, key: str, value: Any, ttl: Optional[timedelta] = None) -> None:
        """
        Set value in cache
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live (uses default if None)
        """
        with self._lock:
            self._cache[key] = (value, datetime.now())
            logger.debug(f"Set cache value for key: {key}")
    
    def delete(self, key: str) -> bool:
        """
        Delete value from cache
        
        Args:
            key: Cache key to delete
        
        Returns:
            True if key existed and was deleted, False otherwise
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                logger.debug(f"Deleted cache key: {key}")
                return True
            return False
    
    def clear(self) -> None:
        """Clear all cached data"""
        with self._lock:
            count = len(self._cache)
            self._cache.clear()
            logger.info(f"Cleared {count} items from cache")
    
    def cleanup_expired(self) -> int:
        """
        Remove expired entries from cache
        
        Returns:
            Number of expired entries removed
        """
        now = datetime.now()
        expired_keys = []
        
        with self._lock:
            for key, (value, timestamp) in self._cache.items():
                if now - timestamp >= self.default_ttl:
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self._cache[key]
        
        if expired_keys:
            logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")
        
        return len(expired_keys)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics
        
        Returns:
            Dictionary with cache statistics
        """
        now = datetime.now()
        total_entries = len(self._cache)
        expired_entries = 0
        
        with self._lock:
            for key, (value, timestamp) in self._cache.items():
                if now - timestamp >= self.default_ttl:
                    expired_entries += 1
        
        return {
            'total_entries': total_entries,
            'active_entries': total_entries - expired_entries,
            'expired_entries': expired_entries,
            'default_ttl_minutes': self.default_ttl.total_seconds() / 60
        }


# Global cache instance for the application
app_cache = SimpleCache(default_ttl=timedelta(minutes=5))


def get_cached_data(key: str, fetch_func: Callable[[], Any], ttl: Optional[timedelta] = None) -> Any:
    """
    Convenience function to use the global cache instance
    
    Args:
        key: Cache key
        fetch_func: Function to call if cache miss or expired
        ttl: Time to live for this entry
    
    Returns:
        Cached or freshly fetched value
    """
    return app_cache.get(key, fetch_func, ttl)


def clear_cache():
    """Clear the global cache"""
    app_cache.clear()


def get_cache_stats() -> Dict[str, Any]:
    """Get statistics for the global cache"""
    return app_cache.get_stats()


def cached(ttl: int = 300):
    """
    Decorator for caching function results
    
    Args:
        ttl: Time to live in seconds (default: 5 minutes)
    
    Returns:
        Decorator function
    """
    def decorator(func: Callable):
        def wrapper(*args, **kwargs):
            # Create cache key from function name and arguments
            cache_key = f"{func.__name__}:{hash(str(args) + str(sorted(kwargs.items())))}"
            
            def fetch_func():
                return func(*args, **kwargs)
            
            return app_cache.get(cache_key, fetch_func, timedelta(seconds=ttl))
        
        return wrapper
    return decorator