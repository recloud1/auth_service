from uuid import UUID

from pydantic import Field, EmailStr

from schemas.core import Model


class OAuthClientIn(Model):
    name: str


class OAuthClientError(Model):
    error: str | None = Field(
        None,
        description='Код ошибки, если аутентификация или выдача токена у провайдера не удалась'
    )
    error_code: int | None = Field(None, description='Код ошибки')
    error_description: str | None = Field(
        None,
        description='Описание ошибки, если аутентификация или выдача токена у провайдера не удалась'
    )


class OAuthClientCallbackIn(OAuthClientError, OAuthClientIn):
    code: str | None = Field(None, description='Код подтверждения от OAuth-провайдера')
    state: str | None = Field(None, description='Строка состояния от OAuth-провайдера')


class OAuthClientCallbackResult(OAuthClientError):
    token_type: str | None = Field(None, description='Тип токена')
    access_token: str | None = Field(None, description='Токен доступа')
    expires_in: int | None = Field(None, description='Время жизни токена в секундах')
    refresh_token: str | None = Field(None, description='Refresh-токен пользователя')
    scope: str | None = Field(None, description='Права запрошенный текущим приложением')
    user_id: str | None = Field(None, description='Идентификатор пользователя')


class OAuthUserCreate(Model):
    login: str
    email: EmailStr | None
    role_id: UUID


class OAuthAccountCreate(Model):
    user_id: UUID
    social_id: str
    social_name: str


class OAuthAccountDeactivate(Model):
    email: str = Field(..., description='Новый email пользователя')
    password: str = Field(..., description='Новый email пользователя')


class UserInfoModel(Model):
    login: str
    client_id: str
    default_email: str | None


class UserInfoModelEmail(UserInfoModel):
    nickname: str = Field(..., alias='login')
