from celery import Celery
from internal.config.settings import settings

celery = Celery(__name__, broker=str(settings.CELERY_BROKER_URL), backend=str(settings.CELERY_RESULT_BACKEND))


@celery.task(name='process_document')
def process_document(filename: str):
    print(filename)
    return True
