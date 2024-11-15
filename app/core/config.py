from urllib import parse

from pydantic import BaseSettings, SecretStr, Field


class Settings(BaseSettings):
    class Config:
        env_file = '.env'
        json_encoders = {
            SecretStr: lambda v: v.get_secret_value() if v else None,
        }


class Application(Settings):
    name: str = 'Auth Service for Movies Applications'
    address: str
    host: str = '127.0.0.1'
    port: int = 8000
    debug: bool = False

    class Config(Settings.Config):
        env_prefix = 'APP_'


class Token(Settings):
    test: str | None
    alive_hours: int = 4
    refresh_alive_hours: int = 24 * 7
    secret: str = 'some_secret_word'

    class Config(Settings.Config):
        env_prefix = 'TOKEN_'


class Redis(Settings):
    host: str = '127.0.0.1'
    port: int = 6379
    pool_minsize: int = 10
    pool_maxsize: int = 20
    password: str | None = None

    class Config(Settings.Config):
        env_prefix = 'REDIS_'


class Database(Settings):
    name: str
    user: str
    password: str
    host: str = '127.0.0.1'
    port: int = 5432

    @property
    def connection_string(self) -> str:
        return f'postgresql://{self.user}:{parse.quote(self.password)}@{self.host}:{self.port}/{self.name}'

    class Config(Settings.Config):
        env_prefix = 'DB_'


class Logger(Settings):
    log_level: str = 'DEBUG'
    force: bool = True
    enable_additional_debug: bool = True

    class Config(Settings.Config):
        env_prefix = 'LOG_'


class Limiter(Settings):
    rate_limit_per_minute: int = 5

    class Config(Settings.Config):
        env_prefix = 'RATE_'


class Tracer(Settings):
    enable: bool = True
    host: str
    port: int

    class Config(Settings.Config):
        env_prefix = 'TRACER_'


class OAuthClient(Settings):
    yandex_client_id: str | None = None
    yandex_client_secret: str | None = None

    mail_client_id: str | None = None
    mail_client_secret: str | None = None

    vk_client_id: str | None = None
    vk_client_secret: str | None = None

    class Config(Settings.Config):
        env_prefix = 'OAUTH_'


class Captcha(Settings):
    max_count: int = Field(default=1, description='Максимальное количество попыток на решение одной каптчи')
    blocking_time: int = Field(default=60, description='Блокировка пользователя по времени (сек.)')

    class Config(Settings.Config):
        env_prefix = 'CAPTCHA_'


class Envs(Settings):
    app: Application = Application()
    db: Database = Database()
    redis: Redis = Redis()
    token: Token = Token()
    logger: Logger = Logger()
    limiter: Limiter = Limiter()
    oauth: OAuthClient = OAuthClient()
    tracer: Tracer = Tracer()
    captcha: Captcha = Captcha()


envs = Envs()
