import asyncio

import aiohttp
import pytest
import pytest_asyncio

from endpoints.core.settings import test_settings

# Переопределение event_loop - не нужно использовать как фикстуру напрямую
from redis.client import Redis


@pytest.fixture(scope='session')
def event_loop():
    return asyncio.get_event_loop()


@pytest_asyncio.fixture(scope='session')
async def request_client():
    session = aiohttp.ClientSession()

    yield session

    await session.close()


@pytest_asyncio.fixture
def redis_client():
    redis = Redis(
        host=test_settings.redis.host,
        port=test_settings.redis.port,
        password=test_settings.redis.password
    )
    redis.flushall()

    yield redis

    redis.close()
