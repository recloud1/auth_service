import random
from typing import TypeVar, Protocol, Any

from core.config import envs
from internal.cache import redis_cache
from services.cache import RedisCache

Number = TypeVar('Number', int, float)


class Captcha(Protocol):
    def generate(self) -> tuple[str, Any]:
        """ Генерация captcha """

    def validate(self, value: str, result: str) -> bool:
        """ Валидация captcha """


class MathCaptcha(Captcha):
    def __init__(self, member_count: int = 3):
        self.member_count = member_count

    def generate(self) -> tuple[str, Number]:
        operators = random.choices(self._default_operators(), k=self.member_count - 1)
        numbers = random.choices(self._default_numbers(), k=self.member_count)

        problem = [f'{val}{operators[i] if i < len(operators) else ""}' for i, val in enumerate(numbers)]

        problem = ''.join(problem).replace(' ', '')
        problem_result = eval(problem)

        return problem, problem_result

    def validate(self, value: str, result: str):
        return eval(value) == result

    def _default_operators(self) -> list[str]:
        """ Операторы используемые при генерации математического примера """
        return ['+', '-', '/', '*']

    def _default_numbers(self) -> list[Number]:
        """ Числа, используемые в формировании математического примера """
        return [i for i in range(10, 100)]


class CaptchaService:
    def __init__(self, captcha: Captcha, cache: RedisCache, max_count: int = 1, blocking_time: int = 60):
        self.captcha = captcha
        self.cache = cache
        self.max_count = max_count
        self.blocking_time = blocking_time

    def generate_problem(self, key: str) -> str:
        """
        Генерация проблемы и запись ответа в кэш под переданным ключом
        """
        problem, result = self.captcha.generate()

        self.cache.add(key=key, value=str(result), ttl=self.blocking_time)

        return problem

    def check_value(self, key: str, value: str) -> bool:
        """
        Проверка полученном от пользователя ответа с тем, что лежит в кэше
        """
        result = self.cache.get(key)

        if result is None:
            return True

        if value != result:
            return False

        return True

    def unblock(self, key: str) -> str:
        value = self.cache.pop(key)

        return value


captcha_service = CaptchaService(
    captcha=MathCaptcha(),
    cache=redis_cache,
    max_count=envs.captcha.max_count,
    blocking_time=envs.captcha.blocking_time
)
