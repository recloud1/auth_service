from typing import Type, TypeVar, Collection, Dict, Optional, Tuple, List, Iterable
from uuid import UUID

from sqlalchemy.orm import Query

from core.exceptions import generate_entity_not_exists_exception, ObjectNotExists
from models import Base

RetrieveType = TypeVar('RetrieveType')

ID = TypeVar('ID', int, str, UUID)


def retrieve_object(
        query: Query,
        model: Type[RetrieveType],
        id: ID,
        raise_deleted: bool = False
) -> RetrieveType:
    """
    Запрашивает требуемый объект по идентификатору.

    При отсутствии объекта в бд, вызывает ошибку
    :param query: запрос, по которому будет получен объект
    :param model: класс запрашиваемого объекта
    :param id: идентификатор объекта в бд
    :param raise_deleted: выдавать ошибки для удалённых значений (по полю deleted_at)
    :raises ObjectNotExists
    """

    obj = query.filter(model.id == id).first()
    if obj is None:
        raise generate_entity_not_exists_exception(model, id)

    if raise_deleted and getattr(obj, 'deleted_at', None):
        raise generate_entity_not_exists_exception(model, id)

    return obj


def retrieve_batch(
        query: Query,
        model: Type[RetrieveType],
        ids: Collection[int | str]
) -> Dict[int | str, RetrieveType]:
    """
    Запрашивает набор объектов по идентификатором из базы данных

    :param query: запрос для получения сущностей
    :param model: запрашиваемая модель
    :param ids: список идентификаторов объектов для данной модели
    :raises ObjectNotExists при отсутствии одной из запрашиваемых записей
    :return: словарь из пар идентификатор:объект
    """
    objects = query.filter(model.id.in_(ids)).all()

    check_missing_entities(ids, objects, model)

    return {obj.id: obj for obj in objects}


SearchType = TypeVar('SearchType')
Count = int


def pagination(
        query: Query,
        page: int = 1,
        rows_per_page: Optional[int] = 25,
        ModelClass: Type[SearchType] = Base,
        with_count: bool = True,
        with_deleted: bool = False,
        hide_deleted: bool = False
) -> Tuple[List[SearchType], Count]:
    """
    Выполняет запрос с пагинацией.

    Явно указывать запрос им
    :param query: запрос по которому будет выполнен запрос
    :param page: страница
    :param rows_per_page: кол-во элементов на 1 странице выдачи
    :param hide_deleted: параметр явно фильтрующий по deleted_at
    :param ModelClass: класс для возвращаемых значений. Нужен для typehints
    :return: Список значений и предельное их кол-во
    """
    if with_deleted:
        query = query.execution_options(include_deleted=True)

    if hide_deleted:
        # noinspection PyComparisonWithNone
        query = query.filter(ModelClass.deleted_at == None)

    rows_number = query.count() if with_count else None

    if rows_per_page:
        query = query.limit(rows_per_page)

    final_query = query.offset((page - 1) * (rows_per_page or 0))
    return final_query.all(), rows_number


def check_missing_entities(ids: Iterable[str], objects: List[Base], model: Base):
    """
    Проверка на наличие несуществующих записей бд между запрашиваемыми идентификаторами и данными из БД

    :raises: ObjectNotExists при отсутствии 1 или более сущностей в БД
    """
    if len(set(ids)) != len(objects):
        retrieving_ids = set(ids)
        existing_ids = {i.id for i in objects}

        diff = retrieving_ids.symmetric_difference(existing_ids)

        repr_name = getattr(model, '__repr_name__', lambda: 'Object')

        raise ObjectNotExists(
            mess=f'{repr_name() if callable(repr_name) else repr_name}'
                 f' с идентификаторами {", ".join(map(str, diff))} не найдены',
            model=model, ids=list(diff)
        )
