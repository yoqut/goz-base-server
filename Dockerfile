# 1. Base image
FROM python:3.12-slim

# 2. Ishchi katalog
WORKDIR /app

# 3. System dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 4. Pipni yangilash
RUN pip install --upgrade pip

# 5. Requirements o'rnatish
COPY requirements.txt .
RUN pip install -r requirements.txt

# 6. Loyihani copy qilish
COPY . .

EXPOSE 8000

# 7. Django migrations va Gunicorn birlashtirilgan CMD
CMD sh -c "python manage.py makemigrations --noinput && \
    python manage.py migrate --noinput && \
    python manage.py createsuper && \
    python manage.py collectstatic --noinput && \
    gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 4 & \
    celery -A config worker --loglevel=info"
