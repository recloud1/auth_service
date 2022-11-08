from functools import wraps
from logging import Logger

from flask import request
from opentelemetry import trace

from core.config import envs
from core.constants import REQUEST_HEADER_ID


def trace_request(tracer_name: str, logger: Logger):
    def wrapper(func):
        @wraps(func)
        def decorator(*args, **kwargs):
            request_id = request.headers.get(REQUEST_HEADER_ID) if not envs.app.debug else 'root'
            logger.debug(f'Tracing request_id: {request_id}')

            tracer = trace.get_tracer(tracer_name)

            span = tracer.start_span(
                tracer_name,
                attributes={'http.request_id': request_id},
                context=request.headers.get('environ')
            )
            result = func(*args, **kwargs)
            span.end()

            return result

        return decorator

    return wrapper
