from pydantic import Field, PostgresDsn
from typing import Optional, Any, Dict
from pydantic import field_validator
from pydantic_core.core_schema import ValidationInfo
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Настройки базы данных
    DB_HOST: str = Field(..., description='Хост для подключения к базе данных.')
    DB_PORT: int = Field(..., description='Порт для подключения к базе данных.')
    DB_USER: str = Field(..., description='Имя пользователя для доступа к базе данных.')
    DB_PASSWORD: str = Field(..., description='Пароль для доступа к базе данных.')
    DB_NAME: str = Field(..., description='Имя базы данных.')
    DB_URI: Optional[PostgresDsn] = Field(None, description='URI для подключения к базе данных.')

    # Настройки Minio
    MINIO_HOST: str = Field('localhost', description='Minio host for set connection.')
    MINIO_PORT: int = Field(5432, description='Default port for MinIO S3 server connection.')
    MINIO_ACCESS_TOKEN: str = Field(..., description='Minio access token.')
    MINIO_SECRET_TOKEN: str = Field(..., description='Minio secret token.')

    # Настройки OpenAI
    OPENAI_TOKEN: str = Field(..., description='OpenAI API Bearer token.')

    # Метод для сборки URI базы данных
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
            path=f"/{values.data.get('DB_NAME')}",
        )

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'


settings = Settings()
