from celery import Task
import requests

from internal.config.settings import settings

webhook_url = settings.TELEGRAM_WEBHOOK


class MyTaskWithSuccess(Task):
    # Поведение при успешном завершении задачи
    def on_success(self, retval, task_id, args, kwargs):
        _, user_id, document = retval
        print(f"Document: {document}, User ID: {user_id}")
        result = requests.post(webhook_url, json={"file_url": f'https://cdn.student-space.ru/{document}',
                                                  "user_id": user_id})
        super().on_success(retval, task_id, args, kwargs)

    # Поведение при ошибке (добавлено для полноты примера)
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        print(f"Task {task_id} failed with exception: {exc}")
        super().on_failure(exc, task_id, args, kwargs, einfo)
