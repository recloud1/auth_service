import uuid

from pydantic import Field, EmailStr, validator

from schemas.core import IdMixin, ListModel, Model
from utils.auth import generate_password_hash


class UserCreate(Model):
    login: str
    email: str
    password: str = Field(..., min_length=6)
    role_id: uuid.UUID

    @validator('login')
    def validate_login(cls, v: str):
        if not v.isascii():
            raise ValueError('Логин может состоять только из символов латиницы')
        for letter in v:
            if letter.isspace():
                raise ValueError('В логине не должно быть пробелов')
        return v

    @validator('password')
    def hash_password(cls, val: str):
        if val:
            password_hash = generate_password_hash(val)
            return password_hash

    @validator('password', pre=True)
    def cast_empty_password_to_none(cls, val: str):
        return None if (val is None or len(val) == 0) else val


class UserUpdate(Model):
    login: str
    email: str


class UserBare(UserUpdate, IdMixin):
    class Config(Model.Config):
        orm_mode = True


class UserFull(UserBare):
    pass


class UserList(ListModel):
    data: list[UserBare]


class SetUserRole(Model):
    role_id: uuid.UUID


class RegisterUserIn(Model):
    login: str = Field(min_length=4)
    password: str = Field(min_length=6)
    email: EmailStr
    last_name: str
    first_name: str
    middle_name: str | None
    role_id: uuid.UUID | None

    @validator('login')
    def validate_login(cls, v: str):
        if not v.isascii():
            raise ValueError('Логин может состоять только из символов латиницы')
        for letter in v:
            if letter.isspace():
                raise ValueError('В логине не должно быть пробелов')
        return v

    @validator('password')
    def hash_password(cls, val: str):
        if val:
            password_hash = generate_password_hash(val)
            return password_hash

    @validator('password', pre=True)
    def cast_empty_password_to_none(cls, val: str):
        return None if (val is None or len(val) == 0) else val


class LoginUserIn(Model):
    login: str = Field(..., description='Почта или логин пользователя')
    password: str
    fingerprint: dict | None
