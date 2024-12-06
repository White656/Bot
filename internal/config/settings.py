from pydantic import Field
from pydantic_settings import BaseSettings


class Minio(BaseSettings):
    host: str = Field('localhost', description='Minio host for set connection.')
    port: int = Field(5432, description='Default port for set connection to MinIO S3 server.')
    access_token: str = Field(..., description='Minio access token.')
    secret_token: str = Field(..., description='Minio secret token.')

    class Config:
        env_prefix = 'minio_'
        env_file = '.env'
        env_file_encoding = 'utf-8'


class OpenAI(BaseSettings):
    token: str = Field(..., description='OpenAI API Bearer token.')

    class Config:
        env_prefix = 'openai_'
        env_file = ".env"
        env_file_encoding = 'utf-8'


class Settings(BaseSettings):
    openai: OpenAI = OpenAI()
    # minio: Minio = Minio()

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'


settings = Settings()
