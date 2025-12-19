#!/bin/bash
set -e

# Migratsiyalarni bajarish
echo "Running migrations..."
python manage.py makemigrations --noinput
python manage.py migrate --noinput

# Superuser yaratish (agar mavjud bo'lmasa)
echo "Creating superuser if not exists..."
python manage.py createsuper

# Static fayllarni yig'ish
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Nginx uchun fayl huquqlarini o'rnatish
chmod -R 755 /app/static

# Gunicorn ni ishga tushirish
echo "Starting Gunicorn..."
exec gunicorn config.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 4 \
    --timeout 120 \
    --log-level=info \
    --access-logfile - \
    --error-logfile -