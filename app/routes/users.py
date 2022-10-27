import datetime
import uuid

from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity
from spectree import Response

from core.constants import ROLES
from core.swagger import api
from internal.crud.utils import retrieve_object
from internal.users import user_crud, check_credentials, get_login_history
from models import User, Role
from routes.core import responses
from schemas.core import GetMultiQueryParam
from schemas.login_history import UserLoginHistoryList
from schemas.users import UserBare, UserFull, UserList, UserCreate, UserUpdate, SetUserRole
from utils.required import role_required
from utils.db import db_session_manager

users = Blueprint(name='users', import_name=__name__, url_prefix='/users')
route_tags = ['Users']


@users.get('')
@api.validate(query=GetMultiQueryParam, resp=Response(HTTP_200=UserList, **responses), tags=route_tags)
@role_required([ROLES.administrator.value])
def get_users():
    """
    Получение списка пользователей доступных в системе
    """
    with db_session_manager() as session:
        users_result, count = user_crud.get_multi(session)
        result = [UserBare.from_orm(i) for i in users_result]

    return UserList(data=result).dict()


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
    with db_session_manager() as session:
        history = get_login_history(session, user_id)

    return UserLoginHistoryList(data=history).dict()


@users.route('/login-history', methods=['GET'])
@api.validate(**history_params)
@role_required([ROLES.user.value])
def get_user_login_history():
    """
    Получение истории посещений автора запроса к этому роуту
    """
    user_id = get_jwt_identity()

    with db_session_manager() as session:
        history = get_login_history(session, user_id)

    return UserLoginHistoryList(data=history).dict()


@users.post('')
@api.validate(json=UserCreate, resp=Response(HTTP_200=UserFull, **responses), tags=route_tags)
@role_required([ROLES.administrator.value])
def create_user():
    """
    Создание нового пользователя
    """
    data = UserCreate(**request.json)
    with db_session_manager() as session:
        retrieve_object(session.query(Role), Role, data.role_id)

        check_credentials(session, data.login, data.email)

        result_user = user_crud.create(session, data)

        result = UserFull.from_orm(result_user)

        return result.dict()


@users.put('')
@api.validate(json=UserUpdate, resp=Response(HTTP_200=UserFull, **responses), tags=route_tags)
@role_required([ROLES.administrator.value])
def update_user(user_id: uuid.UUID):
    """
    Обновление информации о пользователе
    """
    data = UserUpdate(**request.json)

    with db_session_manager() as session:
        check_credentials(session, data.login, data.email, exclue_user_id=user_id)
        user = user_crud.get(session, user_id)

        result_user = user_crud.update(session, user, data)

        result = UserFull.from_orm(result_user)

        return result.dict()


@users.put('/info')
@api.validate(json=UserUpdate, resp=Response(HTTP_200=UserFull, **responses), tags=route_tags)
@role_required([ROLES.user.value])
def update_user_info():
    """
    Обновление информации пользователя о самом себе
    """
    data = UserUpdate(**request.json)
    user_id = get_jwt_identity()

    with db_session_manager() as session:
        check_credentials(session, data.login, data.email, exclue_user_id=user_id)
        user = user_crud.get(session, user_id)

        result_user = user_crud.update(session, user, data)

        result = UserFull.from_orm(result_user)

        return result.dict()


@users.put('/<user_id>/roles')
@api.validate(json=SetUserRole, resp=Response(HTTP_200=UserFull, **responses), tags=route_tags)
@role_required([ROLES.administrator.value])
def set_user_role(user_id: uuid.UUID):
    """
    Установка роли для пользователя
    """
    data = SetUserRole(**request.json)
    with db_session_manager() as session:
        role_query = session.query(Role).where(Role.id != ROLES.root.value)
        retrieve_object(role_query, Role, data.role_id)

        user = user_crud.get(session, user_id)
        user.role_id = data.role_id

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
