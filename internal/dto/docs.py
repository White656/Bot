from uuid import UUID

from pydantic import BaseModel


class DocsRead(BaseModel):
    id: UUID
    name: str
    s3_briefly: str

    class Config:
        from_attributes = True


class DocsCreate(BaseModel):
    """
    Represents a model for creating documentation files with a name and an S3 path.

    The class is designed to handle file metadata, including its name and S3
    storage path. It extends the BaseModel to provide model-related functionality
    and supports configuration settings to allow creating instances from
    class attributes.
    """
    name: str  # Имя файла
    s3_briefly: str  # Путь в хранилище S3

    class Config:
        from_attributes = True


class MilvusDocsCreate(BaseModel):
    """
    Represents a model for mapping Milvus IDs to document IDs.

    This class is designed to facilitate the integration and mapping between
    Milvus, a high-performance vector database, and document storage systems. Each
    instance of this class links a unique ID used in Milvus to a corresponding
    document ID. It ensures that both identifiers are consistently paired and can
    be utilized for further operations like querying or storage manipulation.

    Attributes:
        milvus_id (int): The unique identifier associated with an entry in the
            Milvus database.
        docs_id (int): The unique identifier associated with a document in the
            document storage system.

    Config:
        from_attributes (bool): Determines whether an instance of the class can
            be created from attributes directly. This is primarily used to enable
            flexibility in the data parsing and instantiation process.
    """
    milvus_id: int
    docs_id: int

    class Config:
        from_attributes = True
