import datetime
import logging

import jwt
from pydantic import ValidationError

from core.config import envs
from core.exceptions.default_messages import ExceptionMessages
from core.exceptions.exceptions import NotAuthorized
from core.logger import get_logger
from schemas.auth import UserInfo, Token, RefreshTokenInfoIn, TokenInfo, UserInfoJWT
from utils.trace import trace_request

logger = get_logger(__name__)


class JWTGenerator:
    """
    Синглтон для работы с jwt
    """
    JWT_SECRET = envs.token.secret
    DEFAULT_ALGORITHM = 'HS256'
    TOKEN_ALIVE_HOURS = datetime.timedelta(hours=envs.token.alive_hours)
    REFRESH_TOKEN_ALIVE_HOURS = datetime.timedelta(hours=envs.token.refresh_alive_hours)

    logger = logging.getLogger('JWTGenerator')

    TEST_TOKEN = envs.token.test

    @classmethod
    def _encode_jwt(cls, data: dict) -> str:
        return jwt.encode(data, key=cls.JWT_SECRET, algorithm=cls.DEFAULT_ALGORITHM)

    @classmethod
    def _decode_jwt(cls, token: str) -> dict:
        return jwt.decode(token, cls.JWT_SECRET, algorithms=[cls.DEFAULT_ALGORITHM])

    @classmethod
    @trace_request('create_jwt_token', logger)
    def create_jwt(cls, user: UserInfo, refresh_token: str | None = None) -> tuple[Token, Token]:
        """
        Создаёт jwt токены из данных пользователя

        :param user: информация о пользователе
        :param refresh_token: refresh-токен
        :return: кортеж из access и refresh-токенов
        """
        user = UserInfoJWT(**user.dict())
        created_at = datetime.datetime.utcnow()
        expired_at = created_at + cls.TOKEN_ALIVE_HOURS
        refresh_expired_at = (created_at + cls.REFRESH_TOKEN_ALIVE_HOURS)

        if not refresh_token:
            refresh_info = RefreshTokenInfoIn(user_id=user.id, exp=refresh_expired_at).dict()
            refresh_token = cls._encode_jwt(refresh_info)

        token_info = TokenInfo(user=user, exp=expired_at, iat=created_at)

        token = cls._encode_jwt(token_info.dict(by_alias=True))

        return token, refresh_token

    @classmethod
    def parse_jwt(cls, token: Token) -> TokenInfo | None:
        """
        Получает информацию из jwt токена
        """
        decoded_jwt = None
        try:
            decoded_jwt = cls._decode_jwt(token)
            user_info = TokenInfo(**decoded_jwt)

            return user_info
        except (jwt.InvalidTokenError, jwt.exceptions.InvalidSignatureError) as e:
            cls.logger.debug(f'Failed to decode token: "{token}"; {str(e)}')
        except ValidationError as e:
            cls.logger.debug(f'Got some unparsed dict from token "{decoded_jwt}"; {str(e)}')

        return None

    @classmethod
    @trace_request('validate_jwt_token', logger)
    def validate_jwt(cls, token: Token) -> UserInfoJWT:
        """
        Проверяет jwt токен на валидность и возвращает информацию о пользователе

        :raises NotAuthorized
        """
        user_info = cls.parse_jwt(token)

        if not user_info:
            raise NotAuthorized(ExceptionMessages.incorrect_token())

        expired_at = datetime.datetime.fromtimestamp(
            user_info.token_expired_at,
            tz=datetime.timezone.utc
        ).replace(tzinfo=None)

        current_time = datetime.datetime.utcnow()
        if expired_at < current_time:
            raise NotAuthorized(ExceptionMessages.expired_token())

        return UserInfoJWT(**user_info.user.dict())
