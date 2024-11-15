import jwt
from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from pydantic import ValidationError
from spectree import Response
from sqlalchemy import or_, func
from sqlalchemy.orm import joinedload

from core.constants import ROLES
from core.exceptions.default_messages import ExceptionMessages
from core.exceptions.exceptions import NotAuthorized, NoPermissionException, LogicException
from core.swagger import api
from internal.cache import blocked_jwt_storage, redis_cache
from internal.crud.utils import retrieve_object
from internal.users import check_credentials, user_crud, check_connect_two_auth_link
from models import User, Role, UserLoginHistory
from routes.core import responses
from schemas.auth import LoginOut, UserInfo, RefreshTokenInfoOut, TokenIn, ChangePassword, UserInfoJWT
from schemas.core import StatusResponse
from schemas.users import RegisterUserIn, UserFull, LoginUserIn
from services.jwt_generator import JWTGenerator
from utils.auth import verify_password, get_token_from_headers
from utils.db import db_session_manager
from utils.rate_limit import bucket

auth = Blueprint(name='auth', import_name=__name__, url_prefix='/v1/auth')
route_tags = ['Auth']


@auth.post('register')
@api.validate(resp=Response(HTTP_200=UserFull, **responses), tags=route_tags)
def register(json: RegisterUserIn):
    """
    Регистрация нового пользователя с ролью "Пользователь"
    """
    json.role_id = ROLES.user.value

    with db_session_manager() as session:
        check_credentials(session, json.login, json.email)
        user = user_crud.create(session, json)
        result = UserFull.from_orm(user)

        return result.dict()


@auth.post('login')
@api.validate(resp=Response(HTTP_200=LoginOut, **responses), tags=route_tags)
def login(json: LoginUserIn):
    """
    Авторизует пользователя для получения JWT токена
    """
    with db_session_manager() as session:
        query = session.query(User).options(joinedload(User.role).selectinload(Role.permissions)).where(
            or_(
                func.lower(User.login) == func.lower(json.login),
                func.lower(User.email) == func.lower(json.login)
            )
        ).order_by(User.deleted_at.desc())
        user: User = session.scalar(query)

        if (not user) or (not verify_password(json.password, user.password)):
            raise NotAuthorized(ExceptionMessages.incorrect_data())

        if user.deleted_at is not None:
            raise NoPermissionException(ExceptionMessages.blocked_account())

        user_model = UserInfo.from_orm(user)
        access, refresh = JWTGenerator.create_jwt(user_model)

        if user.is_use_additional_auth:
            if not json.code:
                raise NotAuthorized(ExceptionMessages.two_auth_necessary())

            check_connect_two_auth_link(json.code, redis_cache, user)

        # TODO: get ip from request
        session.add(UserLoginHistory(user_id=user.id, ip='', fingerprint=json.fingerprint))
        session.flush()

    return LoginOut(token=access, refresh_token=refresh, user=user_model).dict()


@auth.post('logout')
@api.validate(resp=Response(HTTP_200=StatusResponse, **responses), tags=route_tags)
@jwt_required()
def logout(json: TokenIn):
    """
    Блокировка токенов пользователя
    """
    access_token = get_token_from_headers(request.headers)

    if not JWTGenerator.validate_jwt(access_token):
        raise NotAuthorized(ExceptionMessages.incorrect_token())

    try:
        blocked_jwt_storage.add(json.token)
        blocked_jwt_storage.add(access_token)
    except ValueError as e:
        raise LogicException(message=str(e))

    return StatusResponse().dict()


@auth.post('refresh-token')
@api.validate(resp=Response(HTTP_200=LoginOut, **responses), tags=route_tags)
def generate_access_token(json: TokenIn):
    """
    Получает новый jwt токен по refresh токену
    """
    expired_exception = NotAuthorized(ExceptionMessages.expired_token())

    try:
        info = RefreshTokenInfoOut(**JWTGenerator._decode_jwt(json.token))
    except (ValidationError, jwt.exceptions.DecodeError):
        raise LogicException(ExceptionMessages.incorrect_token())
    except jwt.exceptions.InvalidSignatureError:
        raise expired_exception

    if blocked_jwt_storage.have(json.token):
        raise expired_exception

    with db_session_manager() as session:
        user = retrieve_object(session.query(User), model=User, id=info.user_id)
        user_model = UserInfo.from_orm(user)

    access, refresh = JWTGenerator.create_jwt(user_model)

    return LoginOut(token=access, refresh_token=refresh, user=user_model).dict()


@auth.post('change-password')
@api.validate(json=ChangePassword, resp=Response(HTTP_200=StatusResponse, **responses), tags=route_tags)
@jwt_required()
def change_password(json: ChangePassword):
    """
    Смена пароля пользователя
    """
    current_user_id = get_jwt_identity()

    with db_session_manager() as session:
        user = user_crud.get(session, current_user_id)

        user.password = json.password

        session.flush()

    return StatusResponse().dict()


@auth.post('validate-token')
@api.validate(json=TokenIn, resp=Response(HTTP_200=UserInfoJWT, **responses), tags=route_tags)
@bucket.rate_limit
def validate_jwt_token(json: TokenIn):
    """
    Валидация JWT-токена, который прислал сервис (в рамках системы кинотеатра).

    Схема работы получается следующая:
    1. Пользователь делает запрос в какой-то сервис (например, хочет получить список фильмов)
    2. Сервис, который отдает список фильмов, берет токен пользователя и идет в текущий роут
    3. Если токен валидный - отдается базовая информация о пользователе, в противном случае кидается exception

    Необходимость данный схемы работы обусловлена следующим моментом: сервис, который получает токен, должен
    удостовериться, что этот токен (после того, как пользователь его получил) не был изменен.
    """
    if blocked_jwt_storage.have(json.token):
        raise NotAuthorized(ExceptionMessages.expired_token())

    user_info = JWTGenerator.validate_jwt(json.token)

    return user_info.dict()
