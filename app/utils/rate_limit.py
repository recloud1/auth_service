import datetime
from functools import wraps
from http import HTTPStatus
from typing import Any

from flask import jsonify, request
from flask_jwt_extended import get_jwt, verify_jwt_in_request
from redis.client import Redis

from core.config import envs
from core.exceptions.default_messages import ExceptionMessages
from internal.captcha import captcha_service
from utils.auth import get_ip_address_from_request


class Bucket:
    """ Leaking bucket rate limiting decorator """

    def __init__(self, with_captcha: bool = True):
        self.pipeline = Redis(
            host=envs.redis.host,
            port=envs.redis.port,
            password=envs.redis.password
        ).pipeline()
        self.with_captcha = with_captcha

    def rate_limit(self, func) -> Any:

        @wraps(func)
        def decorator(*args, **kwargs):
            verify_jwt_in_request()
            uuid = get_jwt()['sub']
            ip_addr = get_ip_address_from_request(request)

            key = f'{uuid}:{datetime.datetime.now().minute}'
            self.pipeline.incr(key, 1)
            self.pipeline.expire(key, 59)

            request_num = self.pipeline.execute()[0]
            rate_limit = envs.limiter.rate_limit_per_minute

            if request_num > rate_limit:
                if self.with_captcha:
                    request_num -= 1
                    captcha_service.generate_problem(key=ip_addr)

                response = jsonify(
                    message={HTTPStatus.TOO_MANY_REQUESTS: ExceptionMessages.too_many_requests()}
                )
                response.status_code = HTTPStatus.TOO_MANY_REQUESTS
                return response
            return func(*args, **kwargs)

        return decorator


bucket = Bucket()
