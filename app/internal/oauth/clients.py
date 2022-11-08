import abc
import uuid
from typing import TypeVar

import requests

from core.config import envs
from core.oauth import OAUTH_CLIENT_NAMES
from internal.oauth.exceptions import OAuthException
from schemas.core import Model
from schemas.oauth import UserInfoModel, OAuthClientCallbackResult, UserInfoModelEmail

UserInfoModelType = TypeVar('UserInfoModelType', bound=Model)


class OAuthClient(abc.ABC):
    def __init__(
            self,
            name: OAUTH_CLIENT_NAMES,
            client_id: str,
            client_secret: str,
            base_url: str,
            user_info_base_url: str,
            user_info_uri: str | None = None,
            display: str | None = 'popup',
            authorize_uri: str = 'authorize',
            token_uri: str = 'token',
            response_type: str = 'code',
            grant_type: str = 'authorization_code',
            user_info_model: UserInfoModelType = UserInfoModel,
    ):
        """
        Основной класс для взаимодействия с OAuth-провайдерами

        :param name: наименование провайдера (внутренее)
        :param client_id: идентификатор, который выдал провайдер при регистрации текущего приложения
        :param client_secret: секретный ключ, который выдал провайдер при регистриации текущего приложения
        :param base_url: базовый URI провайдера
        :param user_info_base_url: базовый URL-адрес для получения информации о пользователе по токену
        :param user_info_uri: URI для получения информации о пользователе по токену
        :param authorize_uri: URI для аутентификации пользователя (без слэшей - просто название)
        :param token_uri: URI для получения токена от провайдера (без слэшей - просто наименование)
        :param response_type: тип ожидаемого ответа от провайдера
        :param grant_type: тип получения токена от провайдера
        :param user_info_model: модель получаемых от провайдера данных о пользователе
        """
        self.name = name
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = base_url
        self.user_info_base_url = user_info_base_url
        self.user_info_uri = user_info_uri
        self.display = display
        self.response_type = response_type
        self.grant_type = grant_type
        self.authorize_uri = authorize_uri
        self.token_uri = token_uri
        self.user_info_model = user_info_model

    def generate_redirect_url(self, state: str | None = None):
        """
        Генерация ссылки для редиректа пользователя на страницу аутентификации внешнего поставщика

        :return: ссылка в виде строки
        """
        query_params = self._generate_redirect_params()
        result = f'{self.base_url}/{self.authorize_uri}?{self._pack_query_params(query_params)}'

        return result

    def _generate_redirect_params(self, state: str | None = None) -> dict:
        query_params = {
            'client_id': self.client_id,
            'state': state or uuid.uuid4().hex,
            'display': self.display
        }

        return query_params

    def _pack_query_params(self, params: dict[str, str]):
        """
        Упаковка параметров GET запроса в единую строку
        """
        query = [f'{key}={value}' for key, value in params.items()]
        result = '&'.join(query)

        return result

    def callback(self, code: str, state: str | None) -> tuple[OAuthClientCallbackResult, UserInfoModelType]:
        """
        Обработка запроса от внешнего поставщика.

        Чаще всего обмен кода подтверждения на токен пользователя.
        """
        url = self._generate_token_url()
        data = self._pack_data_to_get_token(code)
        response = requests.post(url=url, data=data)
        response_data = response.json()

        result = OAuthClientCallbackResult(**response_data)

        if result.error:
            raise OAuthException(message=result.error_description)

        user_info = self.get_user_info(result.access_token, result)

        return result, user_info

    @abc.abstractmethod
    def get_user_info(
            self,
            token: str,
            callback_result: OAuthClientCallbackResult | None = None
    ) -> UserInfoModelType:
        """
        Получение информации о пользователе от провайдера по токену.

        :param token: токен пользователя, который выдал провайдер
        :return: данные о пользователе
        """
        pass

    def _generate_user_info_url(self) -> str:
        """
        Генерация адреса для запроса на получения информации о пользователе по токену

        :return: адрес в виде строки
        """
        result = f'{self.user_info_base_url}/{self.user_info_uri if self.user_info_uri else ""}'
        return result

    def _generate_token_url(self):
        """
        Генерация URL для запроса токена у поставщика

        :return: URL в виде строки
        """
        return f'{self.base_url}/{self.token_uri}'

    def _pack_data_to_get_token(self, code: str) -> dict:
        """
        Упоковка данных для запроса на получения токена от внешнего поставщика.

        :param code: код, который прилетел в callback
        """
        return {
            'grant_type': self.grant_type,
            'code': code,
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }


class OAuthYandex(OAuthClient):
    def get_user_info(
            self,
            token: str,
            callback_result: OAuthClientCallbackResult | None = None
    ) -> UserInfoModelType:
        query_params = {'format': 'json'}

        response = requests.get(
            url=self._generate_user_info_url(),
            params=query_params,
            headers={'Authorization': f'OAuth {token}'}
        )

        return UserInfoModel(**response.json())


class OAuthMail(OAuthClient):
    def __init__(
            self,
            name: OAUTH_CLIENT_NAMES,
            client_id: str,
            client_secret: str,
            base_url: str,
            user_info_base_url: str,
            user_info_uri: str | None = None,
            redirect_uri: str | None = None,
            *args,
            **kwargs
    ):
        self.redirect_uri = redirect_uri or f'{envs.app.address}/v1/oauth/callback?name={name}'
        super().__init__(
            name,
            client_id,
            client_secret,
            base_url,
            user_info_base_url,
            user_info_uri,
            *args,
            **kwargs
        )

    def get_user_info(
            self,
            token: str,
            callback_result: OAuthClientCallbackResult | None = None
    ) -> UserInfoModelType:
        response = requests.get(
            url=self._generate_user_info_url(),
            params={'access_token': token}
        )
        data = response.json()
        result = {
            **data,
            'login': data.get('nickname')
        }

        return UserInfoModelEmail(**result)

    def _generate_redirect_params(self, state: str | None = None) -> dict:
        result = super()._generate_redirect_params(state)
        result = {
            **result,
            'response_type': self.response_type,
            'redirect_uri': self.redirect_uri
        }

        return result

    def _pack_data_to_get_token(self, code: str) -> dict:
        result = super()._pack_data_to_get_token(code)

        result = {
            **result,
            'redirect_uri': self.redirect_uri
        }

        return result


class OAuthVK(OAuthMail):
    def __init__(
            self,
            name: OAUTH_CLIENT_NAMES,
            client_id: str,
            client_secret: str,
            base_url: str,
            user_info_base_url: str,
            api_version: str,
            *args,
            **kwargs
            ):
        self.api_version = api_version
        super().__init__(name, client_id, client_secret, base_url, user_info_base_url, *args, **kwargs)

    def _generate_redirect_params(self, state: str | None = None) -> dict:
        data = super()._generate_redirect_params(state)
        result = {
            **data,
            'v': self.api_version
        }

        return result

    def get_user_info(
            self,
            token: str,
            callback_result: OAuthClientCallbackResult | None = None
    ) -> UserInfoModelType:
        response = requests.get(
            url=self._generate_user_info_url(),
            params={'access_token': token, 'v': self.api_version, 'user_id': callback_result.user_id}
        )
        data = response.json().get('response')[0]

        return UserInfoModel(login=data.get('id'), client_id=self.client_id)


yandex_social_client = OAuthYandex(
    name=OAUTH_CLIENT_NAMES.yandex,
    client_id=envs.oauth.mail_client_id,
    client_secret=envs.oauth.mail_client_secret,
    base_url='https://oauth.yandex.ru',
    user_info_base_url='https://login.yandex.ru/info'
)

mail_base_url = 'https://oauth.mail.ru'
mail_social_client = OAuthMail(
    name=OAUTH_CLIENT_NAMES.mail,
    client_id=envs.oauth.mail_client_id,
    client_secret=envs.oauth.mail_client_secret,
    base_url=mail_base_url,
    authorize_uri='login',
    user_info_base_url=mail_base_url,
    user_info_uri='userinfo'
)

vk_social_client = OAuthVK(
    name=OAUTH_CLIENT_NAMES.vk,
    client_id=envs.oauth.vk_client_id,
    client_secret=envs.oauth.vk_client_secret,
    base_url='https://oauth.vk.com',
    token_uri='access_token',
    user_info_base_url='https://api.vk.com/method',
    user_info_uri='users.get',
    api_version='5.131',
)

social_clients = {
    OAUTH_CLIENT_NAMES.yandex: yandex_social_client,
    OAUTH_CLIENT_NAMES.mail: mail_social_client,
    OAUTH_CLIENT_NAMES.vk: vk_social_client,
}
