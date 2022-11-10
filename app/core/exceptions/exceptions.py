from typing import Collection

from core.exceptions.default_messages import ExceptionMessages
from models import Base


class NotAuthorized(Exception):
    """
    Пользователь не авторизован в системе
    """
    pass


class NoPermissionException(Exception):
    """
    У пользователя нет прав на выполнение запроса
    """

    def __init__(self, message=ExceptionMessages.no_permission(), *args):
        super().__init__(message, *args)


class ObjectNotExists(Exception):
    """
    Запрашиваемый объект не найден.

    Хэндлер для логических сущностей и ручных проверок.
    У ORM'a отдельная иерархия ошибок

    **проброс данного исключения не предусматривает выполнение** ``session.rollback``, **его необходимо выполнять вручную**
    (актуально для синхронных функций)
    """

    def __init__(
            self,
            mess: str = ExceptionMessages.object_not_exists(),
            model: Base = None,
            ids: Collection[int] = None,
            *args
    ):
        super().__init__(mess, *args)
        self.ids = ids if ids is not None else []
        self.model = model


class ObjectAlreadyExists(Exception):
    """
    Объект(ы) с такими атрибутами уже существует

    **проброс данного исключения не предусматривает выполнение** ``session.rollback``, **его необходимо выполнять вручную**
    (актуально для синхронных функций)
    """

    def __init__(self, message: str = ExceptionMessages.object_already_exists()):
        super().__init__(message)


class LogicException(Exception):
    def __init__(self, message=ExceptionMessages.logic(), *args):
        super().__init__(message, *args)


def generate_entity_not_exists_exception(model, id) -> ObjectNotExists:
    repr_name = getattr(model, '__repr_name__', 'Object')
    return ObjectNotExists(
        mess=f'{repr_name() if callable(repr_name) else repr_name}'
             f' с идентификатором {id} не найден',
        model=model, ids=[id]
    )
