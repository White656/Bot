import uuid

from fastapi import APIRouter, UploadFile, File, Depends

from internal.config.modules.minio import get_minio_client
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
        user_id: int,
        file: UploadFile = File(...),
        service: DocsService = Depends(DocsService),
        minio_client: MinioClient = Depends(get_minio_client),
):
    """
    Handles the upload of a PDF file, validates its MIME type and size, and stores
    the file in a specified bucket. The function initiates a background task for
    processing the uploaded document and returns a response with task details or
    an appropriate error message if validation or file upload fails.

    Args:
        user_id (int): The ID of the user uploading the file.
        file (UploadFile): An uploaded file object to be validated and processed.
        service (DocsService): A dependency injection providing access to the
            document service.
        minio_client (MinioClient): A dependency injection providing access to
            the MinIO client.

    Returns:
        DynamicResponse: A dynamic response indicating the result of the request.
        On success (200): Includes task information, target file name, and
            file size in task details.
        On failure (400): Includes details of the failure and corresponding
            messages such as MIME type verification or file size violations.
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

    print(user_id)
    bucket = buckets.get('tmp')
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
        task = process_document.delay(object_name, bucket, user_id)
        task_info = TaskRunInfo(id=task.id, filename=object_name, filesize=file.size)
        return DynamicResponse.create(
            status_code=200,
            detail='Success',
            description='File successfully uploaded.',
            example=task_info.model_dump())
    except Exception as e:
        return DynamicResponse.create(status_code=400, detail="Bad Request", description=str(e))
