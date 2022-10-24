import uuid

from flask import Blueprint, request
from spectree import Response

from core.exceptions import ObjectAlreadyExists
from core.swagger import api
from internal.roles import role_crud
from models import Role
from routes.core import responses
from schemas.core import GetMultiQueryParam
from schemas.roles import RoleList, RoleBare, RoleFull, RoleCreate, RoleUpdate
from utils.db import db_session_manager

roles = Blueprint(name='roles', import_name=__name__, url_prefix='/roles')
route_tags = ['Roles']


@roles.get('')
@api.validate(query=GetMultiQueryParam, resp=Response(HTTP_200=RoleList, **responses), tags=route_tags)
def get_roles():
    """
    Получение списка ролей доступных в системе
    """

    with db_session_manager() as session:
        roles_result, count = role_crud.get_multi(session)
        result = [RoleBare.from_orm(i) for i in roles_result]

    return RoleList(data=result).dict()


@roles.get('/<role_id>')
@api.validate(resp=Response(HTTP_200=RoleFull, **responses), tags=route_tags)
def get_role(role_id: str):
    """
    Получение информации о конкретном роли
    """
    with db_session_manager() as session:
        role = role_crud.get(session, role_id)
        return RoleFull.from_orm(role).dict()


@roles.post('')
@api.validate(json=RoleCreate, resp=Response(HTTP_200=RoleFull, **responses), tags=route_tags)
def create_role():
    """
    Создание новой роли
    """
    data = RoleCreate(**request.json)

    with db_session_manager() as session:
        exists_query = session.query(Role).where(Role.name == data.name)
        exists = session.scalar(exists_query)

        if exists:
            raise ObjectAlreadyExists('Данная роль уже существует')

        result_role = role_crud.create(session, data)

        result = RoleFull.from_orm(result_role)

        return result.dict()


@roles.put('/<role_id>')
@api.validate(json=RoleUpdate, resp=Response(HTTP_200=RoleFull, **responses), tags=route_tags)
def update_role(role_id: uuid.UUID):
    """
    Обновление информации о конкретной роли
    """
    data = RoleUpdate(**request.json)

    with db_session_manager() as session:
        exists_query = session.query(Role).where(Role.id != role_id, Role.name == data.name)
        exists_role = session.scalar(exists_query)

        if exists_role:
            raise ObjectAlreadyExists(f'Роль с таким наименованием уже существует')

        role = role_crud.get(session, role_id)
        role = role_crud.update(session, role, data)

        result = RoleFull.from_orm(role)

    return result.dict()
