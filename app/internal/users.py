from sqlalchemy import or_
from sqlalchemy.orm import joinedload, Session

from core.crud.base import CRUDPaginated
from core.crud.utils import retrieve_batch
from core.exceptions import ObjectAlreadyExists
from models import User, UserLoginHistory, Role

user_crud = CRUDPaginated(model=User, get_options=[joinedload(User.role)])

user_login_history_crud = CRUDPaginated(model=UserLoginHistory)


def check_credentials(session: Session, login: str, email: str):
    """
    Проверка данных для регистрации или создания нового пользователя

    :param session: сессия бд
    :param login: логин пользователя
    :param email: почта для пользователя
    """

    exists_user_query = session.query(User).where(or_(User.login == login, User.email == email))
    exists_user = session.scalar(exists_user_query)

    if exists_user:
        raise ObjectAlreadyExists('Пользователь с такими данными уже существует')


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
