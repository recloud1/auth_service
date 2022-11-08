from http import HTTPStatus
from typing import Optional, Tuple

from aiohttp import ClientResponse

from core.constants import ApiRoutes, RequestMethods
from core.settings import test_settings


async def api_request(
        request_client,
        method: RequestMethods,
        route: ApiRoutes,
        route_detail: str = '',
        query_params: dict | None = None,
        data: dict | None = None,
        headers: dict | None = None,
        with_check: bool = True
) -> Tuple[ClientResponse, dict]:
    async with request_client.request(
            method=method,
            url=f'http://{test_settings.api.host}:{test_settings.api.port}/{route}{route_detail}',
            params=query_params,
            json=data,
            headers=headers,
    ) as response:

        if with_check:
            assert response.status == HTTPStatus.OK

        data = await response.json()

        return response, data
