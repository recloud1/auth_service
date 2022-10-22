import uuid
from typing import List, Optional, TypeVar

from pydantic import BaseModel, Field


class Model(BaseModel):
    """Промежуточная модель pydantic'а для унифицирования конфигов и удобного администрирования"""

    class Config:
        allow_population_by_field_name = True


ListElement = TypeVar('ListElement', bound=Model)


class IdMixin(Model):
    """
    Миксин с полем Id для объектов.

    По своей сути крайне бесполезен, **однако** с помощью него можно задать порядок сортировки полей,
    сделав id первым полем в возвращаемых json объектах.

    Указывать первым справа, т.е. ``class YourModel(YourBaseModel, IdMixin)``
    """
    id: uuid.UUID


class ListModel(Model):
    """
    Формат выдачи для всех списков объектов (multiple get)
    """
    rows_per_page: Optional[int]
    page: Optional[int]
    rows_number: Optional[int]
    show_deleted: bool = False
    data: List[ListElement]
    sort_by: str = 'id'
    descending: bool = False


class ErrorSchema(Model):
    """
    Формат данных для ошибок, возвращаемых сервисом
    """
    detail: str


class StatusResponse(BaseModel):
    """
    Формат ответа для запросов, в которых не требуется отдавать данные
    """
    status: str = 'ok'
    warning: Optional[str] = None
    warning_info: List[dict] = Field(default_factory=list)


class GetMultiQueryParam(BaseModel):
    rows_per_page: int = Field(25, ge=0, le=100)
    page: int = Field(1, ge=1)
    rows_number: Optional[int]
    show_deleted: bool = False
    sort_by: str = 'id'
    descending: bool = False

