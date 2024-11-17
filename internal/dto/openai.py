from typing import List, Literal
from pydantic import BaseModel, Field


class Message(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str


class OpenAIRequest(BaseModel):
    model: str = Field(default="gpt-4", description="Название модели")


class OpenAIConversation(OpenAIRequest):
    messages: List[Message] = Field(..., description="Список сообщений для запроса")
    max_tokens: int = Field(default=4096, description="Максимальное количество токенов для ответа")
    temperature: float = Field(default=0.2, description="Параметр креативности")
    top_p: float = Field(default=0.9, description="Альтернативный параметр креативности")
    frequency_penalty: float = Field(default=0, description="Пенальти за частое повторение")
    presence_penalty: float = Field(default=0, description="Пенальти за новые темы")


class OpenAIEmbeddings(OpenAIRequest):
    input: str = Field(..., description="Текст, по которому будет получена векторная модель.")
