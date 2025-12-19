#!/bin/bash
# scripts/celery.sh

set -e

echo "Database is ready!"

echo "Starting Celery worker..."
celery -A config worker --loglevel=info --pool=prefork --concurrency=4