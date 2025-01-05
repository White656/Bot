import uuid
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


def handle_embeddings_and_texts(chunks: list, collection_name: str):
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

    Returns:
        Tuple: A tuple containing the generated embedding, search results from the
        Milvus database, and optionally, a tuple of new embeddings and concatenated
        processed text if no sufficient match is found.
    """
    embedding = chatgpt_client.create_embeddings(chunks)
    results = milvus_client.search_vectors(collection_name, query_vector=embedding, limit=1)
    if results and results[0]['distance'] >= 0.9:
        return embedding, results, None
    new_embeddings = [embedding]
    texts = ''.join(chatgpt_client.send_message(chunk) for chunk in chunks)
    return embedding, results, (new_embeddings, texts)


@celery.task(name='process_document')
def process_document(filename: str, bucket: str):
    """
    Processes a document, extracts text, generates embeddings, and stores the processed
    output in a storage bucket.

    This task performs the following steps:
    1. Retrieves the file from a specified storage bucket (MinIO).
    2. Processes the file (PDF) to extract textual data.
    3. Splits the extracted text into manageable chunks.
    4. Handles embeddings for the text chunks, saving new embeddings when applicable.
    5. Generates a PDF from the processed text and uploads it back into the storage bucket.
    6. Logs results of the processing step where applicable.

    Args:
        filename: str
            The name of the file to process, located in the specified bucket.
        bucket: str
            The name of the storage bucket containing the file.

    Returns:
        int
            Returns 1 if embeddings and text processing lead to a new PDF being created and
            uploaded. Returns 2 if no new embeddings and text were generated, and only
            logging was performed.
    """
    file, _ = minio_client.get_file_from_bucket(bucket_name=bucket, object_name=filename)
    file_stream = BytesIO(file)

    # Обработка PDF
    long_text = process_pdf_and_extract(file_stream)

    # Разбивка текста на чанки
    chunks = chatgpt_client.split_text_into_chunks(long_text, chunk_size=chatgpt_client.max_tokens)

    # Работа с эмбеддингами и текстами
    embedding, results, embeddings_and_texts = handle_embeddings_and_texts(chunks, settings.COLLECTION_NAME)

    if embeddings_and_texts is not None:
        new_embeddings, texts = embeddings_and_texts
        milvus_client.insert_vectors(settings.COLLECTION_NAME, new_embeddings)

        # Генерация PDF и загрузка в MinIO
        pdf = MarkdownPdf(toc_level=3)
        pdf.add_section(Section(texts, toc=False))
        pdf.writer.close()

        object_name = f"{uuid.uuid4()}.pdf"
        minio_client.upload_file_to_bucket(file_io=pdf.out_file, bucket_name=bucket, object_name=object_name)
        return 1

    # Логирование найденных результатов
    for item in results:
        print('id:', item['id'], 'distance:', item['distance'])
    return 2
