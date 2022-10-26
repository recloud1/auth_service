from typing import Optional

from redis.client import Redis


class RedisCache:
    def __init__(self, client: Redis):
        self.client = client

    def add(self, key: str, value: str, ttl: Optional[int]):
        """
        Добавляет токен в заблокированные.

        Блокируется как основной jwt токен, так и refresh токен
        """
        self.client.setex(name=key, value=value, time=ttl)

    def close(self) -> None:
        """
        Закрыть соединение с кэшем
        """
        self.client.close()

    def have(self, value: str) -> bool:
        """
        """
        is_stored = self.client.exists(value)

        return bool(is_stored)

    def clear(self):
        self.client.flushall()