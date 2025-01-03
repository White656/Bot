from pydantic import BaseModel


class DocsCreate(BaseModel):
    """
    DTO (Data Transfer Object) для создания объекта Docs.
    Поля заполняются автоматически после обработки файла.
    """
    name: str  # Имя файла
    checksum: int  # Контрольная сумма файла
    s3_briefly: str  # Путь в хранилище S3

    class Config:
        orm_mode = True
