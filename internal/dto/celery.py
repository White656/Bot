from typing import Any

from internal.dto.base import AbstractModel


class CeleryTaskInfo(AbstractModel):
    id: str
    status: Any
    result: Any


class TaskRunInfo(AbstractModel):
    id: str
    filename: str
    filesize: float | int
