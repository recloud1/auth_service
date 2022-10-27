from redis.client import Redis

from core.config import envs
from services.blocked_jwt import BlockedJWTStorage
from services.cache import RedisCache

blocked_jwt_storage = BlockedJWTStorage(
    RedisCache(Redis(host=envs.redis.host, port=envs.redis.port, password=envs.redis.password)),
    envs.token.refresh_alive_hours
)
