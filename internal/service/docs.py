import logging

from internal.dto.docs import DocsCreate
from internal.entity.docs import Docs
from internal.service.service import Service
from package.minio.main import MinioClient


class DocsService(Service[Docs]):
    async def transaction_to_minio(self, minio_client: MinioClient, dto: DocsCreate, bucket: str, file):
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
