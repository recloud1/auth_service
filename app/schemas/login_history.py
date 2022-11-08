from uuid import UUID

from schemas.core import Model, IdMixin, ListModel


class UserLoginHistoryCreate(Model):
    user_id: UUID
    ip: str | None = None
    fingerprint: str | None = None


class UserLoginHistoryBare(UserLoginHistoryCreate, IdMixin):
    class Config(Model.Config):
        orm_mode = True


class UserLoginHistoryList(ListModel):
    data: list[UserLoginHistoryBare]
