import datetime

from pydantic import Field

from schemas.core import IdMixin, ListModel, Model


class RolePermissionsCreate(Model):
    permissions: list[str]


class RoleUpdate(Model):
    name: str = Field(..., max_length=256)
    description: str = Field(None, max_length=512)


class RoleCreate(RoleUpdate, RolePermissionsCreate):
    pass


class RoleBare(RoleUpdate, IdMixin):
    deleted_at: datetime.datetime | None

    class Config(Model.Config):
        orm_mode = True


class RoleFull(RoleBare, RolePermissionsCreate):
    pass


class RoleList(ListModel):
    data: list[RoleBare]
