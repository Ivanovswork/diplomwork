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

# Копирование Django проекта
COPY reading_api/ ./reading_api/

WORKDIR /app/reading_api

# Сборка статики
RUN python manage.py collectstatic --noinput 2>/dev/null || true

EXPOSE 8000

CMD ["gunicorn", "reading_api.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "1"]
