from typing import Any

from redis.client import Redis


class RedisCache:
    def __init__(self, client: Redis):
        self.client = client

    def add(self, key: str, value: str, ttl: int | None = None):
        """
        Добавляет токен в заблокированные.

        Блокируется как основной jwt токен, так и refresh токен
        """
        if ttl:
            self.client.setex(name=key, value=value, time=ttl)
        else:
            self.client.set(name=key, value=value)

    def get(self, key: str) -> Any | None:
        """
        Получение данных по ключу
        """
        return self.client.get(key)

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
