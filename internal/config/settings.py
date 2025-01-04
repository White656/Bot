from typing import ClassVar, Optional

from pydantic import Field, PostgresDsn, field_validator, RedisDsn
from pydantic_core.core_schema import ValidationInfo
from pydantic_settings import BaseSettings

buckets = {
    'pdf': 'pdf-bucket',
}

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB


class Settings(BaseSettings):
    API: str = '/api'
    DOCS: str = '/docs'
    STARTUP: str = 'startup'
    SHUTDOWN: str = 'shutdown'
    COLLECTION_NAME: str = 'pdf_embeddings'

    NAME: str = 'Atlas Backend'
    VERSION: str = '0.1.0'
    DESCRIPTION: str = 'Atlas Backend'
    SWAGGER_UI_PARAMETERS: ClassVar[dict] = {'filter': True, 'displayRequestDuration': True}
    APP_CORS_ORIGINS: None = None

    # Настройки базы данныхMutable default '[]' is not allowed. Use 'default_factory
    DB_HOST: str = Field(..., alias='DB_DOCKER_IP', description='Хост для подключения к базе данных.')
    DB_PORT: int = Field(..., description='Порт для подключения к базе данных.')
    DB_USER: str = Field(..., description='Имя пользователя для доступа к базе данных.')
    DB_PASSWORD: str = Field(..., description='Пароль для доступа к базе данных.')
    DB_NAME: str = Field(..., description='Имя базы данных.')
    DB_URI: Optional[PostgresDsn] = Field(None, description='URI для подключения к базе данных.')

    # Настройки Minio
    MINIO_HOST: str = Field('localhost', alias='MINIO_DOCKER_IP', description='Minio host for set connection.')
    MINIO_PORT: int = Field(5432, description='Default port for MinIO S3 server connection.')
    MINIO_ACCESS_KEY: str = Field(..., description='Minio access token.')
    MINIO_SECRET_KEY: str = Field(..., description='Minio secret token.')
    # Настройки OpenAI
    OPENAI_TOKEN: str = Field(..., description='OpenAI API Bearer token.')

    # Настройки Milvus
    MILVUS_HOST: str = Field('127.0.0.1', alias='MILVUS_DOCKER_IP', description='Milvus host for set connection.')
    MILVUS_PORT: int = Field(9091, alias='MILVUS_GRPC_PORT', description='Milvus port for set connection.')

    # Настройки Redis
    REDIS_HOST: str = Field('127.0.0.1', alias='REDIS_DOCKER_IP', description='Redis host for set connection.')
    REDIS_PORT: int = Field(..., description='Redis port for set connection.')
    REDIS_NAME: str = Field(..., description='Redis name for set connection.')

    # Настройки Celery
    CELERY_RESULT_BACKEND: RedisDsn | str | None = Field(None, description='Celery result backend URL.')
    CELERY_BROKER_URL: RedisDsn | str | None = Field(None, description='Celery broker URL.')

    @field_validator('DB_URI', mode='before')
    @classmethod
    def assemble_db_connection(
            cls, value: str | None, values: ValidationInfo,  # noqa: WPS110
    ) -> str | PostgresDsn:
        if isinstance(value, str):
            return value

        return PostgresDsn.build(
            scheme='postgresql+asyncpg',
            username=values.data.get('DB_USER'),
            password=values.data.get('DB_PASSWORD'),
            host=values.data.get('DB_HOST'),
            port=values.data.get('DB_PORT'),
            path=str(values.data.get('DB_NAME')),
        )

    @field_validator('CELERY_RESULT_BACKEND', 'CELERY_BROKER_URL', mode='before')
    @classmethod
    def assemble_celery_connection(cls, value: str | None, values: ValidationInfo) -> str | RedisDsn:
        return RedisDsn.build(
            scheme='redis',
            host=values.data.get('REDIS_HOST'),
            port=values.data.get('REDIS_PORT'),
            path=str(values.data.get('REDIS_NAME')),
        )

    @property
    def migrations_url(self) -> str:
        # Преобразовать объект PostgresDsn в строку
        return str(self.DB_URI)

    class Config(object):
        env_file = '.env'
        env_file_encoding = 'utf-8'
        extra = 'ignore'


settings = Settings()
