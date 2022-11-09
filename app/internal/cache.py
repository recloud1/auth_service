from redis.client import Redis

from core.config import envs
from services.blocked_jwt import BlockedJWTStorage
from services.cache import RedisCache

redis = Redis(host=envs.redis.host, port=envs.redis.port, password=envs.redis.password)
redis_cache = RedisCache(redis)

blocked_jwt_storage = BlockedJWTStorage(redis_cache, envs.token.refresh_alive_hours)
