from pydantic import Field
from pydantic_settings import BaseSettings


class OpenAI(BaseSettings):
    token: str = Field(..., description='OpenAI API Bearer token.')

    class Config:
        env_prefix = 'openai_'
        env_file = ".env"
        env_file_encoding = 'utf-8'


class Settings(BaseSettings):
    openai: OpenAI = OpenAI()

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'


settings = Settings()
