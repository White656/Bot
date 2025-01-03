from typing import Any
import orjson

from pydantic import BaseModel

from internal.dto.base import orjson_dumps


class BaseMixing(BaseModel):
    class Config:
        # Заменяем стандартную работу с json на более быструю
        json_loads = orjson.loads
        json_dumps = orjson_dumps


class CeleryTaskInfo(BaseMixing):
    id: str
    status: Any
    result: Any


class TaskRunInfo(BaseMixing):
    id: str
    filename: str
    filesize: float | int
