from io import BytesIO
from celery import Celery
from internal.config.settings import settings
from package.pdf import PDFProcessor

celery = Celery('worker', broker=str(settings.CELERY_BROKER_URL), backend=str(settings.CELERY_RESULT_BACKEND))


@celery.task(name='process_document')
def process_document(contents: BytesIO):
    pdf_processor = PDFProcessor(contents)
    pdf_processor.process_pdf(start_page=0, end_page=pdf_processor.pages)
    return ''.join(f'{page}\n' for page in pdf_processor.extract())
