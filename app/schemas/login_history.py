from schemas.core import Model, IdMixin, ListModel


class UserLoginHistoryCreate(Model):
    pass


class UserLoginHistoryBare(UserLoginHistoryCreate, IdMixin):
    class Config(Model.Config):
        orm_mode = True


class UserLoginHistoryList(ListModel):
    data: list[UserLoginHistoryBare]
