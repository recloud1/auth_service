import datetime

from flask import Blueprint, redirect, request
from flask_jwt_extended import jwt_required
from spectree import Response
from sqlalchemy.orm import joinedload

from core.constants import ROLES
from core.exceptions import ObjectNotExists, LogicException
from core.swagger import api
from internal.cache import blocked_jwt_storage
from internal.oauth.clients import social_clients
from internal.users import user_social_account_crud, user_crud, user_login_history_crud, check_credentials
from models import UserSocialAccount, User
from routes.core import responses
from schemas.auth import UserInfo, LoginOut
from schemas.login_history import UserLoginHistoryCreate
from schemas.oauth import OAuthClientIn, OAuthClientCallbackIn, OAuthUserCreate, \
    OAuthAccountCreate
from schemas.users import RegisterUserIn, UserFull
from services.jwt_generator import JWTGenerator
from utils.auth import get_token_from_headers
from utils.db import db_session_manager

oauth = Blueprint(name='oauth', import_name=__name__, url_prefix='/v1/oauth')
route_tags = ['OAuth']


@oauth.get('/login')
@api.validate(tags=route_tags)
def oauth_client_login(query: OAuthClientIn):
    """
    Генерация ссылки (для аутентификации во внешнем поставщике) и последующий редирект
    """
    client = social_clients.get(query.name)
    url = client.generate_redirect_url()
    return redirect(url)


@oauth.get('/callback')
@api.validate(resp=Response(HTTP_200=LoginOut, **responses), tags=route_tags)
def oauth_client_callback(query: OAuthClientCallbackIn):
    """
    Callback для внешнего поставщика (необходимо указать адрес с этим роутом внешнему поставщику).

    Здесь также генерируется токен текущего сервиса после того, как ответит внешний поставщик
    """
    client = social_clients.get(query.name)

    data, user_info = client.callback(query.code, query.state)

    with db_session_manager() as session:
        account_query = session.query(UserSocialAccount).options(joinedload(UserSocialAccount.user)).where(
            UserSocialAccount.social_id == user_info.client_id,
            UserSocialAccount.user.has(User.login == user_info.login)
        )

        account = session.scalar(account_query)
        if not account:
            user = user_crud.create(session, OAuthUserCreate(login=user_info.login, role_id=ROLES.user.value))
            account = user_social_account_crud.create(
                session,
                OAuthAccountCreate(
                    user_id=user.id,
                    social_id=user_info.client_id,
                    social_name=query.name
                )
            )
        else:
            user = account.user

        user_model = UserInfo.from_orm(user)
        access, refresh = JWTGenerator.create_jwt(user_model)

        user_login_history_crud.create(session, UserLoginHistoryCreate(user_id=user.id))

    return LoginOut(token=access, refresh_token=refresh, user=user_model).dict()


@oauth.post('/deactivate')
@api.validate(resp=Response(HTTP_200=UserFull, **responses), tags=route_tags)
@jwt_required()
def oauth_deactivate_account(json: RegisterUserIn):
    """
    Деактивация OAuth-аккаунта пользователя в системе авторизации
    """
    access_token = get_token_from_headers(request.headers)
    user_info = JWTGenerator.validate_jwt(access_token)
    json.role_id = ROLES.user.value

    with db_session_manager() as session:
        user = user_crud.get(session, user_info.id)
        account_query = session.query(UserSocialAccount).where(
            UserSocialAccount.user_id == user.id,
            UserSocialAccount.deleted_at == None
        )
        account: UserSocialAccount = session.scalar(account_query)

        if not account:
            raise ObjectNotExists('Аккаунт для социальных сетей не найден')

        account.deleted_at = datetime.datetime.utcnow()
        session.flush()

        check_credentials(session, json.login, json.email)
        user = user_crud.update(session, user, json)
        result = UserFull.from_orm(user)

    try:
        blocked_jwt_storage.add(access_token)
    except ValueError as e:
        raise LogicException(message=str(e))

    return result.dict()
