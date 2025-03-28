import uuid
import asyncio
from io import BytesIO

from markdown_pdf import MarkdownPdf, Section
from celery import Celery

from internal.config import get_milvus_client, get_gpt_client, get_minio_client
from internal.config.settings import settings, buckets
from internal.dto.docs import DocsCreate, MilvusDocsRead
from internal.service.docs import DocsService, MilvusDocsService
from internal.service.utils import get_service
from package.celery.tasks import MyTaskWithSuccess
from package.pdf import PDFProcessor

celery = Celery(__name__, broker=str(settings.CELERY_BROKER_URL), backend=str(settings.CELERY_RESULT_BACKEND))

minio_client = get_minio_client()
chatgpt_client = get_gpt_client()
milvus_client = get_milvus_client()


def process_pdf_and_extract(file_stream: BytesIO, start_page: int = 0):
    """
    Process a PDF file and extract text.

    This function utilizes a PDF processing utility to extract text from a given
    PDF file stream. It initializes a PDFProcessor object with the provided file
    stream, processes the PDF starting from the specified page, and extracts the
    text content from all processed pages. The extracted text is returned as a
    single concatenated string with line breaks.

    Args:
        file_stream (BytesIO): A binary stream representing the PDF file.
        start_page (int): The page number to start processing the PDF from. Defaults
            to 0.

    Returns:
        str: The extracted text from the PDF, concatenated with line breaks.
    """
    pdf_processor = PDFProcessor(file_stream)
    pdf_processor.process_pdf(start_page=start_page, end_page=pdf_processor.pages)
    return '\n'.join(pdf_processor.extract())


def handle_embeddings_and_texts(chunks: list, collection_name: str, prompt_type: str):
    """
    Handles the embedding creation from chunks, searches for matching vectors in
    Milvus storage, and processes text data from the input chunks if no sufficient
    match is found.

    Combines the functionality of generating embeddings with the external API,
    querying the vector database for relevant matches, validating match thresholds,
    and generating fallback or additional results for unmatched embeddings and texts.

    Parameters:
        chunks (list): A list of input text chunks to process for embedding and text
        handling.

        collection_name (str): The name of the embedding collection in the Milvus
        database to perform the vector search.

        prompt_type (str): The type of the prompt to be used when generating embeddings.

    Returns:
        Tuple: A tuple containing the generated embedding, search results from the
        Milvus database, and optionally, a tuple of new embeddings and concatenated
        processed text if no sufficient match is found.
    """
    if prompt_type is not None:
        chatgpt_client.system_prompt = prompt_type
    embedding = chatgpt_client.create_embeddings(chunks)
    results = milvus_client.search_vectors(collection_name, query_vector=embedding, limit=1)
    if results and results[0]['distance'] >= 0.9:
        return embedding, results, None
    new_embeddings = [embedding]
    texts = ''.join(chatgpt_client.send_message(chunk) for chunk in chunks)
    return embedding, results, (new_embeddings, texts)


@celery.task(base=MyTaskWithSuccess, name='process_document')
def process_document(filename: str, bucket: str, user_id: str, prompt_type: str):
    """
    Asynchronous task for processing a document file stored in a MinIO bucket. The task includes
    retrieval of the file, processing it to extract text, preparing embeddings for the text chunks,
    and storing the final results in a Milvus database. Additionally, it generates a new PDF file
    from the processed text and uploads it back to a specified MinIO bucket.

    Args:
        filename (str): Name of the file to be processed from the MinIO bucket.
        bucket (str): Name of the MinIO bucket where the file is stored.
        user_id (str): ID of the user processing the document.
        prompt_type (str): Type of the prompt for the user to prompt.

    Returns:
        dict: A dictionary representing the result created in the Milvus database.

    Raises:
        KeyError: Raised in case of unexpected missing buckets during operations.
        StorageException: Raised on failure to interact with MinIO client.
        ProcessingException: Raised for any issues in text processing or PDF creation.
        DatabaseException: Raised for errors occurring during interactions with Milvus.
    """
    file, _ = minio_client.get_file_from_bucket(bucket_name=bucket, object_name=filename)
    file_stream = BytesIO(file)

    # Обработка PDF
    long_text = process_pdf_and_extract(file_stream)

    # Разбивка текста на чанки
    chunks = chatgpt_client.split_text_into_chunks(long_text, chunk_size=chatgpt_client.max_tokens)

    # Работа с эмбеддингами и текстами
    embedding, results, embeddings_and_texts = handle_embeddings_and_texts(
        chunks,
        settings.COLLECTION_NAME,
        prompt_type)

    if embeddings_and_texts is None:
        for milvus_object in results:
            result = asyncio.run(__get_docs_milvus(milvus_object['id']))
            if result is None:
                continue
            return result, user_id, result['docs']['s3_briefly']

    new_embeddings, texts = embeddings_and_texts
    ids = milvus_client.insert_vectors(settings.COLLECTION_NAME, new_embeddings)

    # Генерация PDF и загрузка в MinIO
    pdf = MarkdownPdf(toc_level=3)
    pdf.add_section(Section(texts, toc=False))
    pdf.writer.close()
    pdf.out_file.seek(0)
    object_name = f"{uuid.uuid4()}.pdf"
    new_bucket = buckets.get('pdf')
    minio_client.upload_file_to_bucket(file_io=pdf.out_file, bucket_name=new_bucket, object_name=object_name)
    result = asyncio.run(__create_docs_milvus(ids, object_name, new_bucket))
    return result, user_id, result['s3_briefly']


async def __create_docs_milvus(
        milvus_ids: list[int],
        doc_name: str,
        bucket: str,
):
    async with get_service(DocsService) as docs_service:
        s3_briefly = f"{bucket}/{doc_name}"
        dto_doc = DocsCreate(
            name=doc_name,
            s3_briefly=s3_briefly,
        )
        result = await docs_service.create_docs_and_milvus(dto_doc, milvus_ids)
        return result


async def __get_docs_milvus(milvus_id: int):
    async with get_service(MilvusDocsService) as milvus_docs_service:
        result = await milvus_docs_service.get_one_or_none(milvus_id)
        return MilvusDocsRead.model_validate(result).model_dump()
