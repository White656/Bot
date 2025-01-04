import logging
from io import BytesIO

from markdown_pdf import MarkdownPdf, Section
from celery import Celery

from internal.config.gpt import get_gpt_client
from internal.config.milvus import get_milvus_client
from internal.config.minio import get_minio_client
from internal.config.settings import settings
from package.pdf import PDFProcessor

celery = Celery(__name__, broker=str(settings.CELERY_BROKER_URL), backend=str(settings.CELERY_RESULT_BACKEND))

minio_client = get_minio_client()
chatgpt_client = get_gpt_client()
milvus_client = get_milvus_client()


@celery.task(name='process_document')
def process_document(filename: str, bucket: str):
    pdf = MarkdownPdf(toc_level=3)
    texts = ''

    file, _ = minio_client.get_file_from_bucket(
        bucket_name=bucket,
        object_name=filename
    )
    file_stream = BytesIO(file)
    pdf_processor = PDFProcessor(file_stream)
    pdf_processor.process_pdf(start_page=0, end_page=pdf_processor.pages)
    long_text = '\n'.join(pdf_processor.extract())
    chunks = chatgpt_client.split_text_into_chunks(long_text, chunk_size=chatgpt_client.max_tokens)
    new_embeddings = []
    embedding = chatgpt_client.create_embeddings(chunks)

    milvus_client.create_collection(settings.COLLECTION_NAME, dim=1536)
    results = milvus_client.search_vectors(settings.COLLECTION_NAME, query_vector=embedding, limit=1)
    if not results or results[0]['distance'] < 0.9:
        new_embeddings.append(embedding)

        for i, chunk in enumerate(chunks):
            print(f'--------- Page {i + 1} ----------')
            response = chatgpt_client.send_message(chunk)
            texts += response

        milvus_client.insert_vectors(settings.COLLECTION_NAME, new_embeddings)
        print(f'Вставлено {len(new_embeddings)} новых эмбеддингов')
        pdf.add_section(Section(texts, toc=False))
        return 1
    else:
        for item in results:
            print('id:', item['id'], 'distance', item['distance'])
        return 2
