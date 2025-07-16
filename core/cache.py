import json
import hashlib
from django.conf import settings
from django.core.cache import cache

# Try to use Redis if configured, otherwise fall back to Django's default cache
try:
    import redis
    if hasattr(settings, 'REDIS_URL'):
        redis_client = redis.Redis.from_url(settings.REDIS_URL)
    else:
        redis_client = None
except (ImportError, AttributeError):
    redis_client = None

class UniversityCache:
    CACHE_TTL = 3600  # 1 hour
    
    @staticmethod
    def get_universities():
        """Get cached universities"""
        cache_key = "universities:all"
        cached = cache.get(cache_key)
        if cached:
            return json.loads(cached)
        return None
    
    @staticmethod
    def set_universities(universities_data):
        """Cache universities data"""
        cache_key = "universities:all"
        cache.set(cache_key, json.dumps(universities_data), UniversityCache.CACHE_TTL)
    
    @staticmethod
    def get_campus_suggestions(lat, lng, radius):
        """Get cached campus suggestions"""
        cache_key = f"campus_suggestions:{lat:.4f}:{lng:.4f}:{radius}"
        return cache.get(cache_key)
    
    @staticmethod
    def set_campus_suggestions(lat, lng, radius, suggestions):
        """Cache campus suggestions"""
        cache_key = f"campus_suggestions:{lat:.4f}:{lng:.4f}:{radius}"
        cache.set(cache_key, json.dumps(suggestions), 1800)  # 30 minutes
    
    @staticmethod
    def invalidate_university(university_id: int):
        """Invalidate cache for a specific university"""
        cache.delete(f"university_{university_id}")
        cache.delete("universities:all")
        # logger.info(f"Cache invalidated for university {university_id}") # Original code had this line commented out
    
    @staticmethod
    def invalidate_all():
        """Invalidate all university-related cache"""
        cache.delete("universities:all")
        # Note: Pattern-based cache clearing would require Redis SCAN
        # For now, we'll clear the most common keys
        # logger.info("All university cache invalidated") # Original code had this line commented out

class ContentCache:
    CACHE_TTL = 900  # 15 minutes
    
    @staticmethod
    def get_smart_content(user_type, params_hash):
        """Get cached smart content"""
        cache_key = f"smart_content:{user_type}:{params_hash}"
        return cache.get(cache_key)
    
    @staticmethod
    def set_smart_content(user_type, params_hash, content):
        """Cache smart content"""
        cache_key = f"smart_content:{user_type}:{params_hash}"
        cache.set(cache_key, json.dumps(content), ContentCache.CACHE_TTL)
    
    @staticmethod
    def generate_params_hash(params):
        """Generate hash for parameters"""
        param_string = json.dumps(params, sort_keys=True)
        return hashlib.md5(param_string.encode()).hexdigest()

class LocationCache:
    CACHE_TTL = 1800  # 30 minutes
    
    @staticmethod
    def get_user_location(user_id):
        """Get cached user location"""
        cache_key = f"user_location:{user_id}"
        return cache.get(cache_key)
    
    @staticmethod
    def set_user_location(user_id, location_data):
        """Cache user location"""
        cache_key = f"user_location:{user_id}"
        cache.set(cache_key, json.dumps(location_data), LocationCache.CACHE_TTL)
    
    @staticmethod
    def invalidate_user_location(user_id):
        """Invalidate user location cache"""
        cache_key = f"user_location:{user_id}"
        cache.delete(cache_key) 