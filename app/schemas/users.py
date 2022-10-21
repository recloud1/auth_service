from typing import List

from schemas.core import IdMixin, Model, ListModel


class UserCreate(Model):
    pass


class UserUpdate(UserCreate):
    pass


class UserBare(UserUpdate, IdMixin):
    pass


class UserFull(UserBare):
    pass


class UserList(ListModel):
    data: List[UserBare]
