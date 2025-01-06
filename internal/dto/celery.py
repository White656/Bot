from pydantic import BaseModel


class TaskRunInfo(BaseModel):
    id: str
    filename: str
    filesize: float | int
