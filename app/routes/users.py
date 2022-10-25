import uuid

from flask import Blueprint, request
from spectree import Response

from core.constants import ROLES
from core.crud.utils import retrieve_object
from core.swagger import api
from internal.users import user_crud, user_login_history_crud, check_credentials
from models import User, UserLoginHistory, Role
from routes.core import responses
from schemas.login_history import UserLoginHistoryBare, UserLoginHistoryList
from schemas.users import UserBare, UserFull, UserList, UserCreate
from utils.auth import role_required
from utils.db import db_session_manager

users = Blueprint(name='users', import_name=__name__, url_prefix='/users')
route_tags = ['Users']


@users.get('')
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
def get_user(user_id: str):
    """
    Получение информации о конкретном пользователе
    """
    with db_session_manager() as session:
        user = user_crud.get(session, user_id)
        return UserFull.from_orm(user).dict()


@users.route('/<user_id>/login-history', methods=['GET'])
@api.validate(resp=Response(HTTP_200=UserLoginHistoryList, **responses), tags=route_tags)
def get_user_login_history(user_id: uuid.UUID):
    """
    Получение истории посещений конкретного пользователя
    """
    with db_session_manager() as session:
        retrieve_object(session.query(User), User, user_id)

        query = session.query(UserLoginHistory).where(UserLoginHistory.user_id == user_id)
        login_history, count = user_login_history_crud.get_multi(session, query=query)

        result = [UserLoginHistoryBare.from_orm(i) for i in login_history]

    return UserLoginHistoryList(data=result).dict()


@users.post('')
# @api.validate(json=UserCreate, resp=Response(HTTP_200=UserFull, **responses), tags=route_tags)
def create_user():
    """
    Создание нового пользователя
    """
    data = UserCreate(**request.json)
    with db_session_manager() as session:
        retrieve_object(session.query(Role), Role, data.role_id)

        # if not able_to_grant_role(session, author.role_id, data.role_id):
        #     raise NoPermissionException("Невозможно выдать роль с большим набором привилегий")

        check_credentials(session, data.login, data.email)

        result_user = user_crud.create(session, data)

        result = UserFull.from_orm(result_user)

        return result.dict()
