from flask import Blueprint
from flask_pydantic_spec import Response

from core.crud.utils import retrieve_object
from core.swagger import api
from internal.users import user_crud, user_login_history_crud
from models import User, UserLoginHistory
from schemas.core import GetMultiQueryParam
from schemas.login_history import UserLoginHistoryBare, UserLoginHistoryList
from schemas.users import UserBare, UserFull, UserList
from utils.db import db_session_manager

users = Blueprint(name='users', import_name=__name__, url_prefix='/users')


@users.route('', methods=['GET'])
@api.validate(query=GetMultiQueryParam, resp=Response(HTTP_200=UserList, HTTP_403=None), tags=['Users'])
def get_users() -> UserList:
    """
    Получение списка пользователей доступных в системе
    """

    with db_session_manager() as session:
        users_result, count = user_crud.get_multi(session)
        result = [UserBare.from_orm(i) for i in users_result]

    return UserList(data=result).dict()


@users.route('/<user_id>', methods=['GET'])
@api.validate(resp=Response(HTTP_200=UserFull, HTTP_403=None), tags=['Users'])
def get_user(user_id: str) -> UserFull:
    """
    Получение информации о конкретном пользователе
    """
    with db_session_manager() as session:
        user = user_crud.get(session, user_id)
        return UserFull.from_orm(user).dict()


@users.route('/<user_id>/login-history', methods=['GET'])
@api.validate(resp=Response(HTTP_200=UserLoginHistoryList, HTTP_403=None), tags=['Users'])
def get_user_login_history(user_id: str) -> UserLoginHistoryList:
    """
    Получение информации о конкретном пользователе
    """
    with db_session_manager() as session:
        retrieve_object(session.query(User), User, user_id)

        query = session.query(UserLoginHistory).where(UserLoginHistory.user_id == user_id)
        login_history, count = user_login_history_crud.get_multi(session, query=query)

        result = [UserLoginHistoryBare.from_orm(i) for i in login_history]

    return UserLoginHistoryList(data=result).dict()
