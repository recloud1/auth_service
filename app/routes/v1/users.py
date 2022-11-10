import datetime
import uuid
from io import BytesIO

import qrcode
from flask import Blueprint, request, send_file
from flask_jwt_extended import get_jwt_identity, jwt_required
from spectree import Response

from core.constants import ROLES
from core.swagger import api
from internal.cache import redis_cache
from internal.crud.utils import retrieve_object
from internal.users import user_crud, check_credentials, get_login_history, connect_two_auth_link, \
    check_connect_two_auth_link
from models import User, Role
from routes.core import responses
from schemas.core import GetMultiQueryParam, StatusResponse
from schemas.login_history import UserLoginHistoryList
from schemas.users import UserBare, UserFull, UserList, UserCreate, UserUpdate, SetUserRole, TwoAuthLinkCodeIn
from utils.db import db_session_manager
from utils.required import role_required

users = Blueprint(name='users', import_name=__name__, url_prefix='/v1/users')
route_tags = ['Users']


@users.get('')
@api.validate(resp=Response(HTTP_200=UserList, **responses), tags=route_tags)
@role_required([ROLES.administrator.value])
def get_users(query: GetMultiQueryParam):
    """
    Получение списка пользователей доступных в системе
    """
    with db_session_manager() as session:
        users_result, count = user_crud.get_multi(
            session,
            rows_per_page=query.rows_per_page,
            page=query.page
        )
        result = [UserBare.from_orm(i) for i in users_result]

    return UserList(
        data=result,
        page=query.page,
        rows_per_page=query.rows_per_page,
        rows_number=count
    ).dict()


@users.get('/<user_id>')
@api.validate(resp=Response(HTTP_200=UserFull, **responses), tags=route_tags)
@role_required([ROLES.administrator.value])
def get_user(user_id: str):
    """
    Получение информации о конкретном пользователе
    """
    with db_session_manager() as session:
        user = user_crud.get(session, user_id)
        return UserFull.from_orm(user).dict()


history_params = {
    'query': GetMultiQueryParam,
    'resp': Response(HTTP_200=UserLoginHistoryList, **responses),
    'tags': route_tags,
}


@users.route('/<user_id>/login-history', methods=['GET'])
@api.validate(**history_params)
@role_required([ROLES.administrator.value])
def get_user_login_histories(user_id: uuid.UUID):
    """
    Получение истории посещений конкретного пользователя
    """
    query_params = GetMultiQueryParam(**request.values)
    with db_session_manager() as session:
        history = get_login_history(session, user_id, query_params)

    return UserLoginHistoryList(
        data=history,
        page=query_params.page,
        rows_per_page=query_params.rows_per_page
    ).dict()


@users.route('/login-history', methods=['GET'])
@api.validate(**history_params)
@role_required([ROLES.user.value])
def get_user_login_history():
    """
    Получение истории посещений автора запроса к этому роуту
    """
    query_params = GetMultiQueryParam(**request.values)
    user_id = get_jwt_identity()

    with db_session_manager() as session:
        history = get_login_history(session, user_id, query_params)

    return UserLoginHistoryList(
        data=history,
        page=query_params.page,
        rows_per_page=query_params.rows_per_page
    ).dict()


@users.post('')
@api.validate(resp=Response(HTTP_200=UserFull, **responses), tags=route_tags)
@role_required([ROLES.administrator.value])
def create_user(json: UserCreate):
    """
    Создание нового пользователя
    """
    with db_session_manager() as session:
        retrieve_object(session.query(Role), Role, json.role_id)

        check_credentials(session, json.login, json.email)

        result_user = user_crud.create(session, json)

        result = UserFull.from_orm(result_user)

        return result.dict()


@users.put('/<user_id>')
@api.validate(resp=Response(HTTP_200=UserFull, **responses), tags=route_tags)
@role_required([ROLES.administrator.value])
def update_user(user_id: uuid.UUID, json: UserUpdate):
    """
    Обновление информации о пользователе
    """
    with db_session_manager() as session:
        check_credentials(session, json.login, json.email, exclude_user_id=user_id)
        user = user_crud.get(session, user_id)

        result_user = user_crud.update(session, user, json)

        result = UserFull.from_orm(result_user)

        return result.dict()


@users.put('/info')
@api.validate(resp=Response(HTTP_200=UserFull, **responses), tags=route_tags)
@role_required([ROLES.user.value])
def update_user_info(json: UserUpdate):
    """
    Обновление информации пользователя о самом себе
    """
    user_id = get_jwt_identity()

    with db_session_manager() as session:
        check_credentials(session, json.login, json.email, exclude_user_id=user_id)
        user = user_crud.get(session, user_id)

        result_user = user_crud.update(session, user, json)

        result = UserFull.from_orm(result_user)

        return result.dict()


@users.post('/<user_id>/two-auth/sync')
@jwt_required()
def connect_two_auth(user_id: uuid.UUID):
    """
    Использование двухфакторной аутентификации пользователя
    """
    with db_session_manager() as session:
        link = connect_two_auth_link(session, redis_cache, user_id)

    qr = qrcode.make(link)

    img_io = BytesIO()
    qr.save(img_io, 'PNG')
    img_io.seek(0)

    return send_file(img_io, mimetype='image/png')


@users.post('/<user_id>/two-auth/check')
@api.validate(resp=Response(HTTP_200=StatusResponse, **responses), tags=route_tags)
@jwt_required()
def check_connect_two_auth(user_id: uuid.UUID, json: TwoAuthLinkCodeIn):
    """
    Проверка введеного кода для подключения двухфакторной аутентификации пользоавтелем
    """
    with db_session_manager() as session:
        user = user_crud.get(session, user_id)
        check_connect_two_auth_link(json.code, redis_cache, user)

        if not user.is_use_additional_auth:
            user.is_use_additional_auth = True
            session.flush()

    return StatusResponse()


@users.put('/<user_id>/roles')
@api.validate(resp=Response(HTTP_200=UserFull, **responses), tags=route_tags)
@role_required([ROLES.administrator.value])
def set_user_role(user_id: uuid.UUID, json: SetUserRole):
    """
    Установка роли для пользователя
    """
    with db_session_manager() as session:
        role_query = session.query(Role).where(Role.id != ROLES.root.value)
        retrieve_object(role_query, Role, json.role_id)

        user = user_crud.get(session, user_id)
        user.role_id = json.role_id

        session.flush()
        session.refresh(user)

        return UserFull.from_orm(user).dict()


@users.delete('/<user_id>')
@api.validate(resp=Response(HTTP_200=UserFull, **responses), tags=route_tags)
@role_required([ROLES.administrator.value])
def block_user(user_id: uuid.UUID):
    """
    Блокировка пользователя
    """
    with db_session_manager() as session:
        user_query = session.query(User).where(User.role_id != ROLES.root.value)

        user = user_crud.get(session, user_id, query=user_query)
        user.deleted_at = datetime.datetime.utcnow()

        session.flush()
        session.refresh(user)

        return UserFull.from_orm(user).dict()
