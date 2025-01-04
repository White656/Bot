import orjson

# Используем pydantic для упрощения работы при перегонке данных из json в объекты
from pydantic import BaseModel, field_serializer, field_validator


class AbstractModel(BaseModel):
    # Сериализация (to JSON)
    @field_serializer('*')  # '*' означает, что это для всех полей
    def serialize_with_orjson(self, value):
        return orjson.dumps(value).decode("utf-8")

    # Десериализация (from JSON)
    @field_validator('*', mode="before")  # 'before' применяется к входящим данным
    def deserialize_with_orjson(cls, value):
        return orjson.loads(value) if isinstance(value, str) else value
