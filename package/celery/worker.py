from celery import Celery

from internal.config.settings import settings

uri = settings.CELERY_BROKER_URL
backend = settings.CELERY_RESULT_BACKEND
print("valuesssss", uri, backend)

print('\n' * 30)
celery = Celery('worker', broker=str(uri), backend=str(backend))
