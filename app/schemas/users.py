from typing import List

from schemas.core import IdMixin, ListModel, Model


class UserCreate(Model):
    login: str
    email: str
    password: str
    role_id: str


class UserUpdate(UserCreate):
    pass


class UserBare(UserUpdate, IdMixin):
    class Config(Model.Config):
        orm_mode = True


class UserFull(UserBare):
    pass


class UserList(ListModel):
    data: List[UserBare]
