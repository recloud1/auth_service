import calendar
import datetime
import uuid
from typing import Optional, Any

from pydantic import Field, validator, BaseModel, root_validator

from schemas.core import Model


class UserInfo(Model):
    """
    Данные используемые при аутентификации пользователя
    """
    id: uuid.UUID
    role_id: uuid.UUID
    updated_at: datetime.datetime

    login: str

    # email: EmailStr
    # last_name: str
    # first_name: str
    # middle_name: Optional[str]

    # role: RoleUpdate

    class Config:
        orm_mode = True


class UserInfoJWT(Model):
    """
    Данные, хранящиеся в JWT токене
    """
    id: uuid.UUID = Field(..., alias='id')
    role_id: uuid.UUID
    updated_at: datetime.datetime = Field(..., alias='upd')


class UserInfoJWTUnix(UserInfoJWT):
    updated_at: float | datetime.datetime = Field(..., alias='upd')

    @validator('updated_at', pre=True)
    def validate_updated_at(cls, value):
        return timestamp_to_unix(value)


class LoginOut(Model):
    token: str = Field(..., description='JWT токен пользователя')
    user: UserInfo


Token = str


def timestamp_to_unix(value: datetime.datetime | float | int | Any) -> float:
    """
    Проверка значение на возможность трансляции к временной метке.

    Необходимо для кейсов с JWT, когда нам нужно все временные метки перевести к UNIX времени в секундах

    :raises ValueError при несоответствии типов
    """
    if type(value) == datetime.datetime:
        value: datetime.datetime
        return calendar.timegm(value.utctimetuple())
    elif type(value) == float or type(value) == int:
        return value
    else:
        raise ValueError("Only timestamps allowed")


class RefreshTokenInfoIn(BaseModel):
    """
    Информация, содержащаяся в JWT refresh токене

    Используется для добавления информации в токен
    """
    user_id: int
    expired_at: float | datetime.datetime = Field(..., alias='exp')
    last_user_update: float | datetime.datetime = Field(..., alias='upd')
    type: str = Field('refresh', const=True, alias='typ')

    @validator('expired_at', pre=True)
    def validate_expired_at(cls, value):
        return timestamp_to_unix(value)

    @validator('last_user_update', pre=True)
    def validate_last_user_update(cls, value):
        return timestamp_to_unix(value)


class RefreshTokenInfoOut(BaseModel):
    """
    Информация, содержащаяся в JWT refresh токене

    Используется для получения информации из токена
    """
    user_id: int
    expired_at: datetime.datetime
    last_user_update: datetime.datetime
    type: str = Field('refresh', const=True, alias='typ')


class TokenInfo(BaseModel):
    """
    Дополнительная информация содержащаяся в JWT токене
    """
    sub: Optional[uuid.UUID]
    user: 'UserInfoJWT'
    token_expired_at: float | datetime.datetime = Field(..., alias='exp')
    token_created_at: float | datetime.datetime = Field(..., alias='iat')
    refresh_token: str

    @root_validator
    def set_sub(cls, values):
        values['sub'] = values['user'].id
        return values

    @validator('token_expired_at', pre=True)
    def validate_token_expired_at(cls, value):
        return timestamp_to_unix(value)

    @validator('token_created_at', pre=True)
    def validate_token_created_at(cls, value):
        return timestamp_to_unix(value)
