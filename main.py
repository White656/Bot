import asyncio

from pydantic import SecretStr

from package.milvus import MilvusClient
from package.openai import PromptManager
from package.openai.client import ChatGPTClient
from internal.config import settings
from package.pdf import PDFProcessor
from markdown_pdf import MarkdownPdf

import logging

# Конфигурируем логирование
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Конфигурация
MILVUS_HOST = "localhost"
MILVUS_PORT = "19530"
COLLECTION_NAME = "pdf_embeddings"
DIMENSION = 1536


async def process_pdf(client, milvus_client, pdf_path):
    """
    Обрабатываем PDF, создаем эмбеддинги, проверяем их в Milvus, записываем новые.
    """
    pdf = MarkdownPdf(toc_level=3)
    long_text = ''
    texts = ''

    # Обрабатываем PDF
    with open(pdf_path, 'rb') as pdf_file:
        pdf_processor = PDFProcessor(pdf_file)
        pdf_processor.process_pdf(start_page=0, end_page=pdf_processor.pages)
        for page_content in pdf_processor.extract():
            long_text += f"{page_content}\n"

    # Разбиваем текст на чанкиr
    chunks = client.split_text_into_chunks(long_text, chunk_size=client.max_tokens)
    print(f"Количество чанков: {len(chunks)}")

    # Список для хранения уникальных эмбеддингов
    new_embeddings = []
    embedding = client.create_embeddings(chunks)
    results = milvus_client.search_vectors(COLLECTION_NAME, query_vector=embedding, limit=1)
    for item in results:
        print('id:', item['id'], 'distance', item['distance'])
    # for i, chunk in enumerate(chunks):
    #     print(f"--------- Page {i + 1} ----------")
    #     response = await client.send_message(chunk)
    #     texts += response
    #
    # # Вставляем все новые эмбеддинги разом
    # if new_embeddings:
    #     milvus_client.insert_vectors(COLLECTION_NAME, new_embeddings)
    #     print(f"Вставлено {len(new_embeddings)} новых эмбеддингов")
    #
    # pdf.add_section(Section(texts, toc=False))
    # pdf.save("results/Хобл.pdf")

    print("PDF с результатами сохранён.")


async def main():
    # Настройка PromptManager и OpenAI клиента
    manager_prompt = PromptManager()
    system_prompt = manager_prompt.get_prompt("summary")

    api_key = SecretStr(settings.OPENAI_TOKEN)
    client = ChatGPTClient(
        api_key,
        model_name="gpt-4o-mini",
        embeddings_model_name="text-embedding-ada-002",
        system_prompt=system_prompt,
    )

    # Настройка Milvus
    milvus_client = MilvusClient(host=MILVUS_HOST, port=MILVUS_PORT)

    # Обработка PDF
    pdf_path = "files/Хобл.pdf"
    await process_pdf(client, milvus_client, pdf_path)


if __name__ == "__main__":
    asyncio.run(main())
