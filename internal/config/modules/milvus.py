# Фабрика для MinioClient
from internal.config import settings
from package.milvus import MilvusClient
from package.milvus.main import MilvusClient

milvus_client = MilvusClient(host=settings.MILVUS_HOST, port=settings.MILVUS_PORT)


def get_milvus_client() -> MilvusClient:
    return milvus_client
