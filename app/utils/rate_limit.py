import datetime
from functools import wraps
from http import HTTPStatus
from typing import Any

from flask import jsonify
from flask_jwt_extended import get_jwt, verify_jwt_in_request

from core.config import envs

from redis.client import Redis


class Bucket:
    """Leaking bucket rate limiting decorator"""

    def __init__(self):
        self.pipeline = Redis(host=envs.redis.host, port=envs.redis.port, password=envs.redis.password).pipeline()

    def rate_limit(self, func) -> Any:

        @wraps(func)
        def decorator(*args, **kwargs):
            verify_jwt_in_request()
            uuid = get_jwt()["sub"]
            key = f'{uuid}:{datetime.datetime.now().minute}'
            self.pipeline.incr(key, 1)
            self.pipeline.expire(key, 59)
            request_num = self.pipeline.execute()[0]
            rate_limit = envs.limiter.rate_limit_per_minute
            if request_num > rate_limit:
                response = jsonify(message={HTTPStatus.TOO_MANY_REQUESTS: "Too Many Requests"})
                response.status_code = HTTPStatus.TOO_MANY_REQUESTS
                return response
            return func(*args, **kwargs)

        return decorator


bucket = Bucket()
