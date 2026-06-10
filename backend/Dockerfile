FROM python:3.10-slim

WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Копирование requirements.txt из корня контекста
COPY requirements.txt .

# Установка Python-зависимостей
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# Копирование Django проекта (вся папка reading_api)
COPY reading_api/ ./reading_api/

# Рабочая директория - где лежит manage.py
WORKDIR /app/reading_api

# Добавляем текущую директорию в PYTHONPATH чтобы gunicorn нашёл reading_api.wsgi
ENV PYTHONPATH=/app/reading_api

# Сборка статики
RUN python manage.py collectstatic --noinput 2>/dev/null || true

EXPOSE 8000

# Gunicorn запускается из директории где лежит manage.py
# reading_api.wsgi - это module path (reading_api/reading_api/wsgi.py)
CMD ["gunicorn", "reading_api.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "1"]
