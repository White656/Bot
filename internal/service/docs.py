import logging

from internal.dto.docs import DocsCreate
from internal.entity.docs import Docs
from internal.service.service import Service
from package.minio.main import MinioClient


class DocsService(Service[Docs]):
    async def transaction_to_minio(self, minio_client: MinioClient, dto: DocsCreate, bucket: str, file):
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
