from flask import Blueprint, request
from flask_pydantic_spec import Response
from sqlalchemy import or_

from core.crud.utils import retrieve_object
from core.swagger import api
from internal.users import user_crud, user_login_history_crud
from models import User, UserLoginHistory, Role
from schemas.core import GetMultiQueryParam
from schemas.login_history import UserLoginHistoryBare, UserLoginHistoryList
from schemas.users import UserBare, UserFull, UserList, UserCreate
from utils.db import db_session_manager

users = Blueprint(name='users', import_name=__name__, url_prefix='/users')
route_tags = ['Users']


@users.route('', methods=['GET'])
@api.validate(query=GetMultiQueryParam, resp=Response(HTTP_200=UserList), tags=route_tags)
def get_users():
    """
    Получение списка пользователей доступных в системе
    """

    with db_session_manager() as session:
        users_result, count = user_crud.get_multi(session)
        result = [UserBare.from_orm(i) for i in users_result]

    return UserList(data=result).dict()


@users.route('/<user_id>', methods=['GET'])
@api.validate(resp=Response(HTTP_200=UserFull, HTTP_403=None), tags=route_tags)
def get_user(user_id: str):
    """
    Получение информации о конкретном пользователе
    """
    with db_session_manager() as session:
        user = user_crud.get(session, user_id)
        return UserFull.from_orm(user).dict()


@users.route('/<user_id>/login-history', methods=['GET'])
@api.validate(resp=Response(HTTP_200=UserLoginHistoryList, HTTP_403=None), tags=route_tags)
def get_user_login_history(user_id: str):
    """
    Получение информации о конкретном пользователе
    """
    with db_session_manager() as session:
        retrieve_object(session.query(User), User, user_id)

        query = session.query(UserLoginHistory).where(UserLoginHistory.user_id == user_id)
        login_history, count = user_login_history_crud.get_multi(session, query=query)

        result = [UserLoginHistoryBare.from_orm(i) for i in login_history]

    return UserLoginHistoryList(data=result).dict()


@users.route('', methods=['POST'])
@api.validate(body=UserCreate, resp=Response(HTTP_200=UserFull, HTTP_403=None), tags=route_tags)
def create_user():
    data = UserCreate(**request.json)
    with db_session_manager() as session:
        retrieve_object(session.query(Role), Role, data.role_id)

        # if not await able_to_grant_role(session, author.role_id, data.role_id):
        #     raise NoPermissionException("Невозможно выдать роль с большим набором привилегий")

        exists_user_query = session.query(User).where(or_(User.login == data.login, User.email == data.email))
        exists_user = session.scalar(exists_user_query)

        if exists_user:
            raise ValueError()

        # todo: hash password
        result_user = user_crud.create(session, data)

    result = UserFull.from_orm(result_user)

    return result.dict()
