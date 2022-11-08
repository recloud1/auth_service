from http import HTTPStatus
from typing import Any

import pytest
from pydantic import BaseModel

from src.auth.requests import register_user, login, logout, generate_access_token, change_password, validate_token


class DataTestExpected(BaseModel):
    status: int | None
    value: Any | None


class DataTest(BaseModel):
    value: Any
    expected: DataTestExpected
    description: str | None
    params: Any | None


register_test_data = [
    DataTest(
        value={},
        expected=DataTestExpected(status=HTTPStatus.OK),
    ),
    DataTest(
        value={'password': '123'},
        expected=DataTestExpected(status=HTTPStatus.UNPROCESSABLE_ENTITY),
        description='Слишком короткий пароль'
    ),
    DataTest(
        value={'login': '123'},
        expected=DataTestExpected(status=HTTPStatus.UNPROCESSABLE_ENTITY),
        description='Слишком короткий логин'
    ),
]


@pytest.mark.asyncio
@pytest.mark.parametrize('test_data', register_test_data)
async def test_register_user(request_client, test_data):
    response, data = await register_user(request_client, **test_data.value)

    assert response.status == test_data.expected.status


@pytest.mark.asyncio
async def test_login_user(request_client):
    password = '123qwe'
    _, data = await register_user(request_client, password=password, with_check=True)

    response, data = await login(request_client, user_login=data.get('login'), password=password)

    assert response.status == HTTPStatus.OK
    assert data.get('token'), data.get('refresh_token')


@pytest.mark.asyncio
async def test_login_user(request_client):
    password = '123qwe'
    _, register_data = await register_user(request_client, password=password, with_check=True)

    response, data = await login(request_client, user_login=register_data.get('login'), password=password)

    assert response.status == HTTPStatus.OK
    assert register_data.get('id') == data.get('user').get('id')
    assert data.get('token'), data.get('refresh_token')


@pytest.mark.asyncio
async def test_login_user_with_wrong_password_failed(request_client):
    _, register_data = await register_user(request_client, password='123qwe', with_check=True)

    response, data = await login(request_client, user_login=register_data.get('login'), password='123qwe1')

    assert response.status == HTTPStatus.UNAUTHORIZED


@pytest.mark.asyncio
async def test_logout_user(request_client):
    password = '123qwe'
    _, register_data = await register_user(request_client, password=password, with_check=True)
    _, login_data = await login(request_client, user_login=register_data.get('login'), password=password)

    response, data = await logout(
        request_client,
        token=login_data.get('token'),
        refresh_token=login_data.get('refresh_token')
    )

    assert response.status == HTTPStatus.OK


@pytest.mark.asyncio
async def test_logout_user_with_wrong_token_failed(request_client):
    password = '123qwe'
    _, register_data = await register_user(request_client, password=password, with_check=True)
    _, login_data = await login(request_client, user_login=register_data.get('login'), password=password)

    response, data = await logout(
        request_client,
        token=login_data.get('token')[:-1] + 'a',
        refresh_token=login_data.get('refresh_token')[:-1] + 'a'
    )

    assert response.status == HTTPStatus.UNAUTHORIZED


@pytest.mark.asyncio
async def test_generate_access_token(request_client):
    password = '123qwe'
    _, register_data = await register_user(request_client, password=password, with_check=True)
    _, login_data = await login(request_client, user_login=register_data.get('login'), password=password)
    token = login_data.get('token')
    refresh_token = login_data.get('refresh_token')

    response, data = await generate_access_token(
        request_client,
        token=token,
        refresh_token=refresh_token
    )

    assert response.status == HTTPStatus.OK


@pytest.mark.asyncio
async def test_change_password(request_client):
    password = '123qwe'
    _, register_data = await register_user(request_client, password=password, with_check=True)
    user_login = register_data.get('login')
    _, login_data = await login(request_client, user_login=user_login, password=password)
    token = login_data.get('token')

    response, data = await change_password(
        request_client,
        token=token,
        password='123qwe1'
    )

    login_status, _ = await login(request_client, user_login=register_data.get('login'), password=password)
    assert response.status == HTTPStatus.OK
    assert login_status.status == HTTPStatus.UNAUTHORIZED


@pytest.mark.asyncio
async def test_validate_token(request_client):
    password = '123qwe'
    _, register_data = await register_user(request_client, password=password, with_check=True)
    _, login_data = await login(request_client, user_login=register_data.get('login'), password=password)
    token = login_data.get('token')

    response, data = await validate_token(request_client, token=token)

    assert response.status == HTTPStatus.OK
    assert data.get('id') == login_data.get('user').get('id')


@pytest.mark.asyncio
async def test_validate_token_with_wrong_token_failed(request_client):
    password = '123qwe'
    _, register_data = await register_user(request_client, password=password, with_check=True)
    _, login_data = await login(request_client, user_login=register_data.get('login'), password=password)
    token = login_data.get('token')[:-1] + 'b'

    response, data = await validate_token(request_client, token=token)

    assert response.status == HTTPStatus.UNAUTHORIZED


@pytest.mark.asyncio
async def test_rate_limiter(request_client):
    password = '123qwe'
    _, register_data = await register_user(request_client, password=password, with_check=True)
    _, login_data = await login(request_client, user_login=register_data.get('login'), password=password)
    token = login_data.get('token')

    await validate_token(request_client, token=token)
    await validate_token(request_client, token=token)
    await validate_token(request_client, token=token)
    await validate_token(request_client, token=token)
    response, data = await validate_token(request_client, token=token)

    assert response.status == HTTPStatus.OK

    response, data = await validate_token(request_client, token=token)

    assert response.status == HTTPStatus.TOO_MANY_REQUESTS
