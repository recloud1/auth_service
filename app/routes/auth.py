import jwt
from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from pydantic import ValidationError
from sqlalchemy import or_, func
from sqlalchemy.orm import joinedload

from core.constants import ROLES
from internal.cache import blocked_jwt_storage
from internal.crud.utils import retrieve_object
from core.exceptions import NotAuthorized, NoPermissionException, LogicException
from internal.users import check_credentials, user_crud
from models import User, Role, UserLoginHistory
from schemas.auth import LoginOut, UserInfo, RefreshTokenInfoOut, TokenIn, ChangePassword
from schemas.core import StatusResponse
from schemas.users import RegisterUserIn, UserFull, LoginUserIn
from services.jwt_generator import JWTGenerator
from utils.auth import verify_password, get_token_from_headers
from utils.db import db_session_manager

auth = Blueprint(name='auth', import_name=__name__, url_prefix='/auth')
route_tags = ['Auth']


@auth.post('/register')
def register():
    """
    Регистрация нового пользователя с ролью "Пользователь"
    """
    data = RegisterUserIn(**request.json)
    data.role_id = ROLES.user.value

    with db_session_manager() as session:
        check_credentials(session, data.login, data.email)
        user = user_crud.create(session, data)
        result = UserFull.from_orm(user)

        return result.dict()


@auth.post('/login')
def login():
    """
    Авторизует пользователя для получения JWT токена
    """
    data = LoginUserIn(**request.json)
    incorrect_data_exception = NotAuthorized('Неверный логин или пароль')

    with db_session_manager() as session:
        query = session.query(User).options(joinedload(User.role).selectinload(Role.permissions)).where(
            or_(
                func.lower(User.login) == func.lower(data.login),
                func.lower(User.email) == func.lower(data.login)
            )
        ).order_by(User.deleted_at.desc())
        user = session.scalar(query)

        if (not user) or (not verify_password(data.password, user.password)):
            raise incorrect_data_exception

        if user.deleted_at is not None:
            raise NoPermissionException(
                'Ваша учётная запись заблокирована.'
                ' О причинах вы можете узнать у тех. поддержки'
            )

        user_model = UserInfo.from_orm(user)
        access, refresh = JWTGenerator.create_jwt(user_model)

        # TODO: get ip from request
        session.add(UserLoginHistory(user_id=user.id, ip='', fingerprint=data.fingerprint))
        session.flush()

    return LoginOut(token=access, refresh_token=refresh, user=user_model).dict()


@auth.post('/logout')
@jwt_required()
def logout():
    """
    Блокировка токенов пользователя
    """
    data = TokenIn(**request.json)
    access_token = get_token_from_headers(request.headers)

    if not JWTGenerator.validate_jwt(access_token):
        raise NotAuthorized('Неверный токен авторизации')

    try:
        blocked_jwt_storage.add(data.token)
        blocked_jwt_storage.add(access_token)
    except ValueError as e:
        raise LogicException(message=str(e))

    return StatusResponse().dict()


@auth.post('/refresh-token')
def generate_access_token():
    """
    Получает новый jwt токен по refresh токену
    """
    data = TokenIn(**request.json)
    expired_exception = NotAuthorized('Ваш токен более недействителен, пожалуйста авторизуйтесь снова')

    try:
        info = RefreshTokenInfoOut(**JWTGenerator._decode_jwt(data.token))
    except (ValidationError, jwt.exceptions.DecodeError):
        raise LogicException('Неверный токен')
    except jwt.exceptions.InvalidSignatureError:
        raise expired_exception

    if blocked_jwt_storage.have(data.token):
        raise expired_exception

    with db_session_manager() as session:
        user = retrieve_object(session.query(User), model=User, id=info.user_id)

    user_model = UserInfo.from_orm(user)
    access, refresh = JWTGenerator.create_jwt(user_model, refresh_token=data.token)

    return LoginOut(token=access, refresh_token=refresh, user=user_model).dict()


@auth.post('/change-password')
@jwt_required()
def change_password():
    """
    Смена пароля пользователя
    """
    data = ChangePassword(**request.json)
    current_user_id = get_jwt_identity()

    with db_session_manager() as session:
        user = user_crud.get(session, current_user_id)

        user.password = data.password

        session.flush()

    return StatusResponse().dict()


@auth.post('/validate-token')
def validate_jwt_token():
    """
    Валидация JWT-токена, который прислал сервис (в рамках системы кинотеатра).

    Схема работы получается следующая:
    1. Пользователь делает запрос в какой-то сервис (например, хочет получить список фильмов)
    2. Сервис, который отдает список фильмов, берет токен пользователя и идет в текущий роут
    3. Если токен валидный - отдается базовая информация о пользователе, в противном случае кидается exception

    Необходимость данный схемы работы обусловлена следующим моментом: сервис, который получает токен, должен
    удостовериться, что этот токен (после того, как пользователь его получил) не был изменен.
    """
    data = TokenIn(**request.json)
    user_info = JWTGenerator.validate_jwt(data.token)

    return user_info.dict()
