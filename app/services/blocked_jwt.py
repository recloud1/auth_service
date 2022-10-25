import datetime

from services.cache import RedisCache


class BlockedJWTStorage:
    """
    Класс для кэширования заблокированных JWT токенов
    """

    def __init__(
            self,
            cache: RedisCache,
            ttl: int = 3600 * 12,
    ):
        self.ttl = ttl
        self.cache = cache

    def close(self):
        self.cache.close()

    def have(self, token: str) -> bool:
        """
        Является ли токен заблокированным.

        **Токен обязательно должен быть проверен на валидность, перед использованием**
        """
        is_stored = self.cache.have(token)
        return is_stored

    def add(self, token: str):
        """
        Добавляет токен в заблокированные.

        Блокируется как основной jwt токен, так и refresh токен
        """
        value = datetime.datetime.utcnow().isoformat()
        self.cache.add(token, value, self.ttl)

    def clear(self):
        """
        Очищает хранилище токенов

        """
        self.cache.clear()


blocked_jwt_storage = None
