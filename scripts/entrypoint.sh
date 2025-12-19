#!/bin/bash
# scripts/entrypoint.sh

set -e

echo "Running database migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Creating superuser if not exists..."
python manage.py createsuper

echo "Starting server..."
exec "$@"