from pydantic import Field
from pydantic_settings import BaseSettings

token = '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'


class OpenAI(BaseSettings):
    url: str = Field('https://api.openai.com/v1', description='OpenAI API endpoint.')
    token: str = Field(token, description='OpenAI API Bearer token.')
    model: str = Field('gpt-4o-mini', description='OpenAI model name.')
    temperature: float = Field(0.6, description='OpenAI temperature.')
    max_tokens: int = Field(4096, description='Maximum tokens.')

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
