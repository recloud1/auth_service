from typing import List

from schemas.core import IdMixin, Model, ListModel


class RoleCreate(Model):
    pass


class RoleUpdate(RoleCreate):
    pass


class RoleBare(RoleUpdate, IdMixin):
    pass


class RoleFull(RoleBare):
    pass


class RoleList(ListModel):
    data: List[RoleBare]
