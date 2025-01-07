# Базовый образ Python
FROM python:3.10

# Установить рабочую директорию в контейнере
WORKDIR /app

# Установить переменные окружения для Python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Скопировать файл с зависимостями в контейнер
COPY requirements.txt /app/

# Установить зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Скопировать код приложения в контейнер
COPY . /app/

# Указать команду для запуска приложения (замените на вашу команду)
CMD ["make", "run"]