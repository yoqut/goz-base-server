#!/bin/bash
set -e

# Django migrations
python manage.py makemigrations --noinput
python manage.py migrate --noinput

# Create superuser if needed
python manage.py createsuper

# Collect static
python manage.py collectstatic --noinput

# Start Gunicorn & Celery
gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 4 &

