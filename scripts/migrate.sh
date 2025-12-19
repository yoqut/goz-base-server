#!/bin/bash
# scripts/migrate.sh

set -e

echo "Running migrations..."
python manage.py migrate --noinput

echo "Migration completed!"