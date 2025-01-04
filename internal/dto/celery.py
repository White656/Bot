from typing import Any

from pydantic import BaseModel


class CeleryTaskInfo(BaseModel):
    id: str
    status: Any
    result: Any


class TaskRunInfo(BaseModel):
    id: str
    filename: str
    filesize: float | int
