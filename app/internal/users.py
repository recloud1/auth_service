from uuid import UUID

from pyotp import TOTP, random_base32
from sqlalchemy import or_
from sqlalchemy.orm import joinedload, Session

from core.config import envs
from core.exceptions.default_messages import two_auth_already_exists_msg, two_auth_code_not_valid_msg
from core.exceptions.exceptions import ObjectAlreadyExists, LogicException
from internal.crud.base import CRUDPaginated
from internal.crud.utils import retrieve_object
from models import User, UserLoginHistory, UserSocialAccount
from schemas.core import GetMultiQueryParam
from schemas.login_history import UserLoginHistoryBare
from services.cache import RedisCache


class UserCrud(CRUDPaginated):
    pass


user_crud = UserCrud(model=User, get_options=[joinedload(User.role)])

user_login_history_crud = CRUDPaginated(model=UserLoginHistory)

user_social_account_crud = CRUDPaginated(
    model=UserSocialAccount,
    get_options=[joinedload(UserSocialAccount.user)]
)


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
        raise ObjectAlreadyExists()


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


def connect_two_auth_link(session: Session, cache: RedisCache, user_id: UUID) -> str:
    secret = random_base32()
    totp = TOTP(secret)
    user_key = str(user_id)

    user = user_crud.get(session, user_id)
    user_secret = cache.get(user_key)

    if user.is_use_additional_auth and user_secret:
        raise LogicException(two_auth_already_exists_msg)

    cache.add(user_key, secret)

    provisioning_url = totp.provisioning_uri(name=str(user.id), issuer_name=envs.app.name)

    return provisioning_url


def check_connect_two_auth_link(code: str, cache: RedisCache, user: User) -> bool:
    secret = cache.get(str(user.id))
    totp = TOTP(secret)

    if not totp.verify(code):
        raise LogicException(two_auth_code_not_valid_msg)

    return True
