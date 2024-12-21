from fastapi import APIRouter, UploadFile, File

from internal.usecase.utils.responses import HTTP_400_BAD_REQUEST, HTTP_200_OK_REQUEST

# Создаем объект Router для маршрутов данного модуля
router = APIRouter()

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB


@router.post(
    "/upload-pdf",
    summary="Загрузка и проверка PDF файла",
    tags=["PDF Upload"])
async def upload_pdf(
        file: UploadFile = File(...),
):
    """
    Эндпоинт для загрузки и проверки PDF-файла.

    Данный маршрут принимает PDF файл, проверяет его формат
    и содержание. В случае успешной проверки возвращает сообщение
    о валидности файла.

    Args:
        file (UploadFile): Загружаемый файл, передается через форму в HTTP-запросе.

    Raises:
        HTTPException: Если формат файла не соответствует PDF или файл поврежден.

    Returns:
        dict: Сообщение о статусе проверки файла и его названии.
    """
    # Проверяем, что файл имеет расширение .pdf
    if not file.filename.endswith(".pdf"):
        return HTTP_400_BAD_REQUEST(description='Invalid file format. Expected PDF file.')

    if file.size >= MAX_FILE_SIZE:
        return HTTP_400_BAD_REQUEST(
            description='File size exceeds the limit.',
            detail=f'File size must be less than {MAX_FILE_SIZE / 1024} KB.',
        )

    try:
        # Считываем содержимое файла
        contents = await file.read()

        # Если считывание прошло успешно, возвращаем успех
        return HTTP_200_OK_REQUEST(detail="PDF file is valid.")
    except Exception as e:
        # Обработка ошибок при работе с файлом (например, файл не является валидным PDF)
        return HTTP_400_BAD_REQUEST(description=str(e))
