from functools import wraps
from typing import Any, List

from flask import current_app
from flask_jwt_extended import verify_jwt_in_request
from flask_jwt_extended.view_decorators import LocationType
from passlib.handlers.pbkdf2 import pbkdf2_sha512

from core.constants import ROLES
from core.exceptions import NoPermissionException
from schemas.auth import TokenInfo


def generate_password_hash(password: str) -> str:
    """
    Создаёт хэш пароля для хранения в БД
    """
    return pbkdf2_sha512.hash(password)


def verify_password(input_password: str, password_hash: str) -> bool:
    """
    Сравнивает полученный вариант пароля с захэшированным вариантом
    """
    return pbkdf2_sha512.verify(input_password, password_hash)


def role_required(
        roles: List[str],
        optional: bool = False,
        fresh: bool = False,
        refresh: bool = False,
        locations: LocationType = None,
        verify_type: bool = True,
) -> Any:
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            header, data = verify_jwt_in_request(optional, fresh, refresh, locations, verify_type)
            payload = TokenInfo(**data)

            role_id = str(payload.user.role_id)
            role_name = payload.user.role_name

            has_access = role_id in roles or role_name in roles
            has_root_access = role_id == ROLES.root.value or role_name == ROLES.root.name

            if not has_access and not has_root_access:
                raise NoPermissionException()

            return current_app.ensure_sync(fn)(*args, **kwargs)

        return decorator

    return wrapper

