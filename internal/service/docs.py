from typing import Dict, Any

import sqlalchemy as sa
from sqlalchemy.orm import selectinload
from internal.dto.docs import DocsCreate, DocsRead
from internal.entity.docs import Docs, MilvusDocs
from internal.service.service import Service
from package.minio.main import MinioClient


class DocsService(Service[Docs]):
    async def transaction_to_minio(self, minio_client: MinioClient, dto: DocsCreate, bucket: str, file) -> Docs:
        """
        Handles the process of saving a transaction in PostgreSQL and uploading a file
        to an MinIO bucket. This involves creating a model instance using the input data,
        storing it in the database, uploading the file, and rolling back the MinIO upload
        if database commit fails.

        Parameters:
            minio_client (MinioClient): The client used for interacting with the MinIO storage service.
            dto (DocsCreate): The data transfer object containing the fields necessary for creating the database entry.
            bucket (str): The name of the MinIO bucket where the file will be uploaded.
            file: The file object that is to be uploaded to MinIO.

        Raises:
            Exception: Propagates any exceptions that occur during the transaction and rollback processes.

        Returns:
            instance: The created database object that successfully corresponds to the input data and uploaded file.
        """
        instance = self.model(**dto.dict())
        self.session.add(instance)

        # Сначала пытаемся загрузить в MinIO
        minio_client.upload_file_to_bucket(
            bucket_name=bucket,
            file_io=file,
            object_name=instance.name,
        )

        try:
            # Если успешно загрузили в MinIO, фиксируем транзакцию в Postgres
            await self.session.commit()
        except Exception as e:
            # Если commit в Postgres не удался, удаляем уже загруженный файл
            minio_client.delete_file_from_bucket(bucket, instance.name)
            raise e  # Перебрасываем исключение
        return instance

    async def create_docs_and_milvus(self, dto: DocsCreate, milvus_ids: list[int]) -> dict[str, Any]:
        """
        Creates a record in the `Docs` table and a related record in the
        `MilvusDocs` table within a single transactional context. All operations
        are committed atomically, ensuring data consistency. In case of an
        exception, the entire transaction is rolled back.

        Args:
            dto (DocsCreate): Data transfer object containing attributes for the
                `Docs` model.
            milvus_ids (list[int]): Identifier to associate the `Docs` record with a
                `MilvusDocs` record.

        Raises:
            Exception: Any exceptions that occur during execution, resulting in a
                rollback of the transaction.

        Returns:
            DocsCreate: Instance of the newly created `Docs` record.
        """

        # Создаём запись в таблице Docs
        instance = self.model(**dto.dict())
        self.session.add(instance)
        await self.session.commit()
        instance_set = [
            MilvusDocs(docs_id=instance.id, milvus_id=pk) for pk in milvus_ids
        ]
        self.session.add_all(instance_set)
        await self.session.commit()

        # Ожидание фиксации в рамках транзакции (автоматически сделает commit в конце контекста)

        return DocsRead.model_validate(instance).model_dump()


class MilvusDocsService(Service[MilvusDocs]):

    async def get_one_or_none(self, milvus_id: int, *where, **filter_by):
        """
        Retrieve a single record based on the given conditions or return None if no matching record is found.

        The method executes a database query using SQLAlchemy to select a record from the model
        based on the milvus_id, optional filtering conditions, and optional filtering parameters.
        It allows for a flexible query construction using where clauses and filter_by conditions.

        Args:
            milvus_id (int): The unique identifier to filter the record by.
            *where: Additional positional filtering conditions to apply to the query.
            **filter_by: Additional named parameters for filtering the query.

        Returns:
            The selected scalar record if it exists, otherwise None.
        """
        return await self.session.scalar(
            sa.select(self.model).options(selectinload(MilvusDocs.docs)).filter_by(
                milvus_id=milvus_id, **filter_by,
            ).where(*where),
        )
