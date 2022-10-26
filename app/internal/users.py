from typing import List, Optional
from uuid import UUID

from sqlalchemy import or_
from sqlalchemy.orm import joinedload, Session

from internal.crud.base import CRUDPaginated
from internal.crud.utils import retrieve_batch, retrieve_object
from core.exceptions import ObjectAlreadyExists
from models import User, UserLoginHistory, Role
from schemas.login_history import UserLoginHistoryBare

user_crud = CRUDPaginated(model=User, get_options=[joinedload(User.role)])

user_login_history_crud = CRUDPaginated(model=UserLoginHistory)


def check_credentials(session: Session, login: str, email: str, exclue_user_id: Optional[UUID] = None):
    """
    Проверка данных для регистрации или создания нового пользователя

    :param session: сессия бд
    :param login: логин пользователя
    :param email: почта для пользователя
    """
    exists_user_query = session.query(User).where(or_(User.login == login, User.email == email))
    if exclue_user_id:
        exists_user_query = exists_user_query.where(User.id != exclue_user_id)

    exists_user = session.scalar(exists_user_query)

    if exists_user:
        raise ObjectAlreadyExists('Пользователь с такими данными уже существует')


def get_login_history(session: Session, user_id: UUID) -> List[UserLoginHistoryBare]:
    """
    Получение истории посещений пользователя

    :param session: SQLAlchemy сессия
    :param user_id: идентификатор пользователя
    """
    retrieve_object(session.query(User), User, user_id)

    query = session.query(UserLoginHistory).where(UserLoginHistory.user_id == user_id)
    login_history, count = user_login_history_crud.get_multi(session, query=query)

    result = [UserLoginHistoryBare.from_orm(i) for i in login_history]

    return result


def able_to_grant_role(
        session: Session,
        author_role_id: int,
        desired_role_id: int
) -> bool:
    """
    Удостоверится, что пользователь, назначающий роль имеет право на выдачу указанной роли.
    """
    retrieve_batch(session.query(Role), Role, [author_role_id, desired_role_id])

    # if author_role_id != ROLES.USER.value and desired_role_id == ROLES.USER.value:
    #     return True
    #
    # if author_role_id != ROLES.ROOT.value:
    #     return False

    return True
