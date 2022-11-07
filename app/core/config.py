from urllib import parse

from pydantic import BaseSettings, SecretStr


class Settings(BaseSettings):
    class Config:
        env_file = '.env'
        json_encoders = {
            SecretStr: lambda v: v.get_secret_value() if v else None,
        }


class Application(Settings):
    name: str = 'Auth Service for Movies Applications'
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


class Tracer(Settings):
    host: str
    port: int

    class Config(Settings.Config):
        env_prefix = 'TRACER_'


class Envs(Settings):
    app: Application = Application()
    db: Database = Database()
    redis: Redis = Redis()
    token: Token = Token()
    logger: Logger = Logger()
    tracer: Tracer = Tracer()


envs = Envs()
