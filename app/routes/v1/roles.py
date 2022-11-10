import datetime
import uuid

from flask import Blueprint
from spectree import Response

from core.constants import ROLES
from core.exceptions.exceptions import ObjectAlreadyExists, LogicException
from core.swagger import api
from internal.roles import role_crud
from models import Role, User
from routes.core import responses
from schemas.core import GetMultiQueryParam
from schemas.roles import RoleList, RoleBare, RoleFull, RoleCreate, RoleUpdate
from utils.required import role_required
from utils.db import db_session_manager

roles = Blueprint(name='roles', import_name=__name__, url_prefix='/v1/roles')
route_tags = ['Roles']


@roles.get('')
@api.validate(resp=Response(HTTP_200=RoleList, **responses), tags=route_tags)
@role_required([ROLES.administrator.value])
def get_roles(query: GetMultiQueryParam):
    """
    Получение списка ролей доступных в системе
    """
    with db_session_manager() as session:
        roles_result, count = role_crud.get_multi(
            session,
            page=query.page,
            rows_per_page=query.rows_per_page
        )
        result = [RoleBare.from_orm(i) for i in roles_result]

    return RoleList(data=result, page=query.page, rows_per_page=query.rows_per_page).dict()


@roles.get('/<role_id>')
@api.validate(resp=Response(HTTP_200=RoleFull, **responses), tags=route_tags)
@role_required([ROLES.administrator.value])
def get_role(role_id: str):
    """
    Получение информации о конкретном роли
    """
    with db_session_manager() as session:
        role = role_crud.get(session, role_id)
        return RoleFull.from_orm(role).dict()


@roles.post('')
@api.validate(resp=Response(HTTP_200=RoleFull, **responses), tags=route_tags)
@role_required([ROLES.administrator.value])
def create_role(json: RoleCreate):
    """
    Создание новой роли
    """
    with db_session_manager() as session:
        exists_query = session.query(Role).where(Role.name == json.name)
        exists = session.scalar(exists_query)

        if exists:
            raise ObjectAlreadyExists()

        result_role = role_crud.create(session, json)

        result = RoleFull.from_orm(result_role)

        return result.dict()


@roles.put('/<role_id>')
@api.validate(json=RoleUpdate, resp=Response(HTTP_200=RoleFull, **responses), tags=route_tags)
@role_required([ROLES.administrator.value])
def update_role(role_id: uuid.UUID, json: RoleUpdate):
    """
    Обновление информации о конкретной роли
    """
    with db_session_manager() as session:
        exists_query = session.query(Role).where(Role.id != role_id, Role.name == json.name)
        exists_role = session.scalar(exists_query)

        if exists_role:
            raise ObjectAlreadyExists()

        role = role_crud.get(session, role_id)
        role = role_crud.update(session, role, json)

        result = RoleFull.from_orm(role)

    return result.dict()


@roles.delete('/<role_id>')
@api.validate(resp=Response(HTTP_200=RoleFull, **responses), tags=route_tags)
@role_required([ROLES.administrator.value])
def delete_role(role_id: uuid.UUID):
    """
    Обновление информации о конкретной роли
    """
    with db_session_manager() as session:
        role = role_crud.get(session, role_id)

        is_role_used_query = session.query(User).where(User.role_id == role_id, User.deleted_at is None)
        is_role_used = session.scalar(is_role_used_query)
        if is_role_used:
            raise LogicException('Данную роль невозможно удалить, так как она назначена на пользователя')

        role.deleted_at = datetime.datetime.utcnow()

        session.flush(role)
        session.refresh(role)

        return RoleFull.from_orm(role).dict()
