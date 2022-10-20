import datetime
from typing import Callable, Type

from sqlalchemy import Column, DateTime, MetaData, func
from sqlalchemy.orm import DeclarativeMeta, declarative_base


class BaseModelClass:
    """
    Класс необходимый для возможного расширения возможностей всех моделей SQLAlchemy
    """
    pass


Base: DeclarativeMeta | Type[BaseModelClass] = declarative_base(cls=BaseModelClass)

# noinspection PyUnresolvedReferences
metadata: MetaData = Base.metadata
metadata.naming_convention = {
    "ix": 'ix_%(column_0_label)s',
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}


def fresh_timestamp() -> Callable[[], datetime.datetime]:
    """Небольшой хелпер для работы с timestamp на уровне ОРМа"""
    return func.timezone('UTC', func.now())


class TimestampMixin(object):
    created_at = Column(DateTime, default=fresh_timestamp())
    updated_at = Column(DateTime, default=fresh_timestamp(), onupdate=fresh_timestamp())
    deleted_at = Column(DateTime)
