import datetime
import os
from functools import wraps
from http import HTTPStatus
from typing import Any

from flask import jsonify
from flask_jwt_extended import get_jwt

from core.config import envs

from redis.client import Redis

RATE_LIMIT = int(os.getenv('RATE_LIMIT_PER_MINUTE', 5))


class Bucket:
    """Leaking bucket rate limiting decorator"""

    def __init__(self):
        self.pipeline = Redis(host=envs.redis.host, port=envs.redis.port, password=envs.redis.password).pipeline()

    def rate_limit(self, func) -> Any:

        @wraps(func)
        def decorator(*args, **kwargs):
            uuid = get_jwt()["sub"]
            key = f'{uuid}:{datetime.datetime.now().minute}'
            self.pipeline.incr(key, 1)
            self.pipeline.expire(key, 59)
            request_num = self.pipeline.execute()[0]
            if request_num > RATE_LIMIT:
                response = jsonify(message={HTTPStatus.TOO_MANY_REQUESTS: "Too Many Requests"})
                response.status_code = HTTPStatus.TOO_MANY_REQUESTS
                return response
            return func(*args, **kwargs)

        return decorator


bucket = Bucket()
