from uuid import uuid4

from aiohttp import ClientSession

from core.constants import RequestMethods, ApiRoutes
from utils.requests import api_request


async def register_user(
        client: ClientSession,
        login: str = None,
        password: str = None,
        email: str = None,
        last_name: str = None,
        first_name: str = None,
        with_check: bool = False
):
    response, data = await api_request(
        client,
        RequestMethods.post,
        ApiRoutes.auth,
        route_detail='/register',
        with_check=with_check,
        data={
            'login': login or uuid4().hex,
            'password': password or '123qwe',
            'email': email or uuid4().hex + '@mail.ru',
            'first_name': first_name or 'first_name',
            'last_name': last_name or 'last_name',
        }
    )

    return response, data


async def login(
        client: ClientSession,
        user_login: str | None,
        password: str | None,
):
    response, data = await api_request(
        client,
        RequestMethods.post,
        ApiRoutes.auth,
        route_detail='/login',
        with_check=False,
        data={
            'login': user_login,
            'password': password,
        }
    )

    return response, data


async def logout(
        client: ClientSession,
        token: str,
        refresh_token: str,
):
    response, data = await api_request(
        client,
        RequestMethods.post,
        ApiRoutes.auth,
        route_detail='/logout',
        with_check=False,
        data={'token': refresh_token},
        headers={'Authorization': f'Bearer {token}'},
    )

    return response, data


async def generate_access_token(
        client: ClientSession,
        token: str,
        refresh_token: str
):
    response, data = await api_request(
        client,
        RequestMethods.post,
        ApiRoutes.auth,
        route_detail='/refresh-token',
        with_check=False,
        data={'token': refresh_token},
        headers={'Authorization': f'Bearer {token}'},
    )

    return response, data


async def change_password(
        client: ClientSession,
        token: str,
        password: str
):
    response, data = await api_request(
        client,
        RequestMethods.post,
        ApiRoutes.auth,
        route_detail='/change-password',
        with_check=False,
        data={'password': password},
        headers={'Authorization': f'Bearer {token}'},
    )

    return response, data


async def validate_token(
        client: ClientSession,
        token: str
):
    response, data = await api_request(
        client,
        RequestMethods.post,
        ApiRoutes.auth,
        route_detail='/validate-token',
        with_check=False,
        data={'token': token},
        headers={'Authorization': f'Bearer {token}'}
    )

    return response, data


async def repeat_requests(times: int, func, *args, **kwargs):
    """Make time call of func."""
    for i in range(times):
        await func(*args, **kwargs)
