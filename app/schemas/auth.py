import calendar
import datetime
import uuid
from typing import Any

from pydantic import Field, validator, BaseModel, root_validator

from schemas.core import Model
from utils.auth import generate_password_hash


class UserInfo(Model):
    """
    Данные используемые при аутентификации пользователя
    """
    id: uuid.UUID
    login: str

    role_id: uuid.UUID
    role_name: str | None

    class Config:
        orm_mode = True


class UserInfoJWT(Model):
    """
    Данные, хранящиеся в JWT токене
    """
    id: uuid.UUID = Field(..., alias='id')
    role_id: uuid.UUID
    role_name: str | None


class LoginOut(Model):
    token: str = Field(..., description='JWT токен пользователя')
    refresh_token: str = Field(..., description='Refresh-токен пользователя')
    user: UserInfo


class ChangePassword(Model):
    password: str = Field(..., min_length=6)

    @validator('password')
    def hash_password(cls, val: str):
        if val:
            password_hash = generate_password_hash(val)
            return password_hash


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
    user_id: uuid.UUID
    expired_at: float | datetime.datetime = Field(..., alias='exp')
    type: str = Field('refresh', const=True, alias='typ')

    @validator('expired_at', pre=True)
    def validate_expired_at(cls, value):
        return timestamp_to_unix(value)


class RefreshTokenInfoOut(BaseModel):
    """
    Информация, содержащаяся в JWT refresh токене

    Используется для получения информации из токена
    """
    user_id: uuid.UUID
    expired_at: datetime.datetime
    type: str = Field('refresh', const=True, alias='typ')


class TokenInfo(BaseModel):
    """
    Дополнительная информация содержащаяся в JWT токене
    """
    sub: uuid.UUID | None
    user: 'UserInfoJWT'
    token_expired_at: float | datetime.datetime = Field(..., alias='exp')
    token_created_at: float | datetime.datetime = Field(..., alias='iat')

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


class TokenIn(Model):
    token: str = Field(..., description='Refresh-токен пользователя')
