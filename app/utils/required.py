from functools import wraps
from typing import Any

from flask import current_app, request
from flask_jwt_extended import verify_jwt_in_request
from flask_jwt_extended.view_decorators import LocationType

from core.constants import ROLES
from core.exceptions.default_messages import expired_token_msg
from core.exceptions.exceptions import NoPermissionException
from internal.cache import blocked_jwt_storage
from schemas.auth import TokenInfo
from utils.auth import get_token_from_headers


def role_required(
        roles: list[str],
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

            access_token = get_token_from_headers(request.headers)
            is_blocked = blocked_jwt_storage.have(access_token)

            if is_blocked:
                raise NoPermissionException(expired_token_msg)

            if not has_access and not has_root_access:
                raise NoPermissionException()

            return current_app.ensure_sync(fn)(*args, **kwargs)

        return decorator

    return wrapper
