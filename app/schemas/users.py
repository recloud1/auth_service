from typing import List

from schemas.core import IdMixin, ListModel, Model


class UserCreate(Model):
    pass


class UserUpdate(UserCreate):
    pass


class UserBare(UserUpdate, IdMixin):
    class Config(Model.Config):
        orm_mode = True


class UserFull(UserBare):
    pass


class UserList(ListModel):
    data: List[UserBare]
