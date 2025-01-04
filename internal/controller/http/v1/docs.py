import uuid

from fastapi import APIRouter, UploadFile, File, Depends

from internal.config.minio import get_minio_client
from internal.config.settings import buckets, MAX_FILE_SIZE
from internal.dto.celery import TaskRunInfo
from internal.dto.docs import DocsCreate
from internal.service.docs import DocsService
from internal.usecase.utils.responses import HTTP_400_BAD_REQUEST, HTTP_200_OK_REQUEST, DynamicResponse
from package.minio.main import MinioClient
from package.celery.worker import process_document

# Создаем объект Router для маршрутов данного модуля
router = APIRouter()


@router.post(
    "/upload-pdf",
    summary="Загрузка и проверка PDF файла",
    responses={
        **HTTP_400_BAD_REQUEST.schema(
            status_code=400,
            description='Failed to upload file.',
            example={"detail": "Invalid MIME type. Expected application/pdf."}
        ),
        **HTTP_200_OK_REQUEST.schema(
            status_code=200,
            description='Success',
            example={"id": "1234567890", "filename": "example.pdf", "filesize": 1024}
        ),
    },
    tags=["PDF Upload"])
async def upload_pdf(
        file: UploadFile = File(...),
        service: DocsService = Depends(DocsService),
        minio_client: MinioClient = Depends(get_minio_client),
):
    """
    Uploads and validates a PDF file. This function checks whether a provided file is a PDF by
    validating its MIME type and file size before uploading it to a specific bucket in Minio storage.
    After successful upload, a success message is returned.

    Args:
        file (UploadFile): The PDF file to be uploaded. Must have the MIME type 'application/pdf' and
            should not exceed the defined maximum allowed file size.
        service (DocsService): Dependency-injected instance of DocsService for handling
            document-related operations.
        minio_client (MinioClient): Dependency-injected client for interacting with Minio
            object storage.

    Returns:
        HTTP_200_OK_REQUEST: Response indicating that the file was successfully uploaded.

    Raises:
        HTTP_400_BAD_REQUEST: Raised if the file MIME type is invalid (not a PDF) or if the file size
            exceeds the maximum allowed limit.
    """
    # Проверяем, что файл имеет расширение .pdf
    if file.content_type != "application/pdf":
        return DynamicResponse.create(status_code=400, description='Invalid MIME type. Expected application/pdf.')

    if file.size >= MAX_FILE_SIZE:
        return DynamicResponse.create(
            status_code=400,
            description='File size exceeds the limit.',
            detail=f'File size must be less than {MAX_FILE_SIZE / 1024} KB.',
        )

    bucket = buckets.get('pdf')
    object_name = f"{uuid.uuid4()}.pdf"
    s3_briefly = f"{bucket}/{object_name}"

    doc_data = DocsCreate(
        name=object_name,
        s3_briefly=s3_briefly,
    )
    try:
        await service.transaction_to_minio(
            minio_client=minio_client,
            dto=doc_data,
            bucket=bucket,
            file=file.file,
        )
        task = process_document.delay(object_name)
        task_info = TaskRunInfo(id=task.id, filename=object_name, filesize=file.size)
        return DynamicResponse.create(
            status_code=200,
            detail='Success',
            description='File successfully uploaded.',
            example=task_info.model_dump())
    except Exception as e:
        return DynamicResponse.create(status_code=400, detail="Bad Request", description=str(e))
