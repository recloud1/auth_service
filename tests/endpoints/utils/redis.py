from redis.client import Redis


def clear_cache(redis_client: Redis):
    redis_client.flushall()
