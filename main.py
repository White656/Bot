import asyncio
import logging

from package.milvus import MilvusClient

# Конфигурируем логирование
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Конфигурация
MILVUS_HOST = 'localhost'
MILVUS_PORT = '19530'
COLLECTION_NAME = 'pdf_embeddings'
DIMENSION = 1536


async def main():
    # Настройка Milvus
    milvus_client = MilvusClient(host=MILVUS_HOST, port=MILVUS_PORT)
    result = milvus_client.get_all_vectors(collection_name=COLLECTION_NAME)
    for item in result:
        print(item)
    # milvus_client.drop_collection('pdf_embeddings')
    # milvus_client.create_collection('pdf_embeddings', DIMENSION)


if __name__ == '__main__':
    asyncio.run(main())
