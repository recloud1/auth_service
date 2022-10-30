from uuid import UUID

from core.exceptions import ObjectAlreadyExists
from sqlalchemy import or_
from sqlalchemy.orm import joinedload, Session

from internal.crud.base import CRUDPaginated
from internal.crud.utils import retrieve_object
from models import User, UserLoginHistory
from schemas.core import GetMultiQueryParam
from schemas.login_history import UserLoginHistoryBare

user_crud = CRUDPaginated(model=User, get_options=[joinedload(User.role)])

user_login_history_crud = CRUDPaginated(model=UserLoginHistory)


def check_credentials(session: Session, login: str, email: str, exclude_user_id: UUID | None = None):
    """
    Проверка данных для регистрации или создания нового пользователя

    :param session: сессия бд
    :param login: логин пользователя
    :param email: почта для пользователя
    :param exclude_user_id:
    """
    exists_user_query = session.query(User).where(or_(User.login == login, User.email == email))
    if exclude_user_id:
        exists_user_query = exists_user_query.where(User.id != exclude_user_id)

    exists_user = session.scalar(exists_user_query)

    if exists_user:
        raise ObjectAlreadyExists('Пользователь с такими данными уже существует')


def get_login_history(
        session: Session,
        user_id: UUID,
        query_params: GetMultiQueryParam
) -> list[UserLoginHistoryBare]:
    """
    Получение истории посещений пользователя

    :param session: SQLAlchemy сессия
    :param user_id: идентификатор пользователя
    :param query_params: параметры пагинации
    """
    retrieve_object(session.query(User), User, user_id)

    query = session.query(UserLoginHistory).where(UserLoginHistory.user_id == user_id)
    login_history, count = user_login_history_crud.get_multi(
        session,
        query=query,
        page=query_params.page,
        rows_per_page=query_params.rows_per_page
    )

    result = [UserLoginHistoryBare.from_orm(i) for i in login_history]

    return result
