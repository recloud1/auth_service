"""
Для упрощения работы со стандартными операциями для сущностей,
здесь представлены удобные обёртки на получение, создание, обновление и удаление в рамках одной сущности
"""
import enum
from typing import TypeVar, Union, Generic, Type, List, Optional, Set, Dict, Any, Tuple

import pydantic
from sqlalchemy.orm import Session, Query
from sqlalchemy.orm.strategy_options import loader_option

from core.crud.utils import retrieve_object, pagination
from models import Base

ModelType: Base = TypeVar("ModelType")
CreateSchemaType = TypeVar("CreateSchemaType", bound=pydantic.BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=pydantic.BaseModel)
Id = Union[str, int]


class ExcludePolicyEnum(enum.Enum):
    default = 'default'
    exclude_none = 'exclude_none'
    exclude_unset = 'exclude_unset'


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(
            self,
            model: Type[ModelType],
            get_options: List[loader_option] = None,
            get_multi_options: List[loader_option] = None,
    ):
        """
        CRUD обёртка со стандартными методами

        :param model: sqlalchemy модель
        :param get_options: опции при запросах единичной модели
        :param get_multi_options: опции при запросах списка

        """
        self.get_multi_options = get_multi_options if get_multi_options else []
        self.get_options = get_options if get_options else []
        self.model = model

    def get(self, session: Session, id: Id, query: Optional[Query] = None) -> Optional[ModelType]:
        """
        Получение единичного объекта из базы данных
        :param session: сессия бд
        :param id: идентификатор объекта в бд
        :param query: специфичный sqlalchemy запрос для получения объекта (при необходимости)
        :raises ObjectNotExists: при отсутствии объекта в бд
        :return:
        """
        if query is None:
            query = session.query(self.model)

        query = query.options(*self.get_options)

        db_object = retrieve_object(query, self.model, id)
        return db_object

    def get_multi(
            self, session: Session, offset: int = 0, limit: Optional[int] = None,
            query: Optional[Query] = None
    ) -> List[ModelType]:
        """
        Получение списка объектов установленного типа
        :param session: сессия бд
        :param offset: offset в бд
        :param limit: предельное кол-во извлекаемых записей
        :param query: кастомный запрос
        :return: результирующий список объектов
        """

        if query is None:
            query = session.query(self.model)

        query = query.options(*self.get_options)

        query = query.offset(offset)
        if limit is not None:
            query = query.limit(limit)

        db_objects = query.all()
        return db_objects

    # noinspection PyMethodMayBeStatic
    def _get_input_data(
            self,
            obj_in: Union[CreateSchemaType, UpdateSchemaType],
            exclude_fields: Set[str] = None,
            cast_policy: ExcludePolicyEnum = ExcludePolicyEnum.default
    ) -> dict:
        if exclude_fields is None:
            exclude_fields = set()

        policy = {cast_policy.value: True} if cast_policy != ExcludePolicyEnum.default else {}

        data = obj_in.dict(exclude=exclude_fields, **policy)

        return data

    def create(
            self, session: Session,
            obj_in: CreateSchemaType,
            exclude_fields: Set[str] = None,
            cast_policy: ExcludePolicyEnum = ExcludePolicyEnum.default
    ) -> ModelType:
        """
        Создание указанной сущности в базе данных
        :param session: сессия бд
        :param obj_in: данные для создания объекта
        :param exclude_fields: исключить указанные поля из входной модели
        :param cast_policy: вариант сериализации модели
        :return:
        """

        data = self._get_input_data(obj_in, exclude_fields, cast_policy)
        db_obj: ModelType = self.model(**data)

        session.add(db_obj)
        session.flush()

        return db_obj

    def update(
            self,
            session: Session,
            db_obj: ModelType,
            obj_in: Union[UpdateSchemaType, Dict[str, Any]],
            exclude_fields: Set[str] = None,
            cast_policy: ExcludePolicyEnum = ExcludePolicyEnum.exclude_unset
    ) -> ModelType:
        """
        Обновление указанной сущности в базе данных
        :param session: сессия бд
        :param obj_in: данные для обновления объекта
        :param exclude_fields: исключить указанные поля из входной модели
        :param cast_policy: вариант сериализации модели
        :return: результирующий объект в базе данных
        """

        if isinstance(obj_in, dict):
            data = obj_in
        else:
            data = self._get_input_data(obj_in, exclude_fields, cast_policy)

        for field in data:
            setattr(db_obj, field, data[field])

        session.add(db_obj)
        session.flush()
        session.refresh(db_obj)
        return db_obj

    def delete(self, session: Session, *, id: int) -> ModelType:
        """
        Удаление сущности из базы данных
        :param session: сессия бд
        :param id: идентификатор объекта
        :return: результирующий объект в базе данных
        """
        obj = session.query(self.model).get(id)
        session.delete(obj)

        session.flush()
        return obj


class CRUDPaginated(CRUDBase):
    """
    Пагинация в выдаче CRUD'a
    """

    def get_multi(
            self,
            session: Session,
            page: int = 1,
            rows_per_page: int = 100,
            with_count: bool = True,
            with_deleted: bool = False,
            query: Optional[Query] = None
    ) -> Tuple[List[ModelType], Optional[int]]:
        """
        Получение списка объектов установленного типа c пагинацией
        :param session: сессия бд
        :param page: страница с отсчётом от 1
        :param rows_per_page: кол-во записей
        :param query: кастомный запрос
        :return: результирующий список объектов и их кол-во
        """
        if query is None:
            query = session.query(self.model)

        query = query.options(*self.get_multi_options)

        values, count = pagination(query, page, rows_per_page)

        return values, count
