# Фабрика для MinioClient
from internal.config import settings
from package.minio.main import MinioClient

minio_client = MinioClient(
    endpoint=f"{settings.MINIO_HOST}:{settings.MINIO_PORT}",
    access_key=settings.MINIO_ACCESS_KEY,
    secret_key=settings.MINIO_SECRET_KEY,
)


def get_minio_client() -> MinioClient:
    return minio_client
