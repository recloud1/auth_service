from pydantic import BaseSettings


class Settings(BaseSettings):
    class Config(BaseSettings.Config):
        env_file = '../.env'
        env_prefix = 'TEST_'


class SettingsIntegration(Settings):
    host: str
    port: int


class TestApiSettings(SettingsIntegration):
    class Config(Settings.Config):
        env_prefix = 'TEST_API_'


class TestPostgresSettings(SettingsIntegration):
    name: str | None = 'test_postgres'
    password: str | None = '123qwe'

    class Config(Settings.Config):
        env_prefix = 'TEST_POSTGRES_'


class TestRedisSettings(SettingsIntegration):
    password: str | None = '123qwe'
    pool_minsize: int | None = 10
    pool_maxsize: int | None = 20

    class Config(Settings.Config):
        env_prefix = 'TEST_REDIS_'


class TestSettings(Settings):
    elastic: TestPostgresSettings = TestPostgresSettings()
    redis: TestRedisSettings = TestRedisSettings()
    api: TestApiSettings = TestApiSettings()


test_settings = TestSettings()
