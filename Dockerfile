# Dockerfile
FROM python:3.11-slim-bullseye

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy project
COPY . .

# Create scripts directory
RUN mkdir -p /scripts
COPY scripts/ /scripts/
RUN chmod +x /scripts/*.sh

# Create static directory
RUN mkdir -p /app/staticfiles
RUN mkdir -p /app/media

# Collect static files (will be run during build for production)
ARG DEBUG
RUN if [ "$DEBUG" = "False" ]; then python manage.py collectstatic --noinput; fi

# Run entrypoint
ENTRYPOINT ["/scripts/entrypoint.sh"]